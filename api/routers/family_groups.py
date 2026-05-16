from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from firebase_admin import auth as firebase_auth
from middleware.auth import require_practitioner
from services.firebase import get_db
from services import brevo

router = APIRouter()

INVITE_TTL_DAYS = 14
ACCEPT_INVITE_URL = "https://parentalcareguide.com/accept-invite.html"


class FamilyGroupCreate(BaseModel):
    name: str
    care_level: str = ""


class InviteRequest(BaseModel):
    email: EmailStr
    relationship: str = ""


class RevokeRequest(BaseModel):
    uid: str


def _verify_group_ownership(db, group_id: str, uid: str):
    snap = db.collection("family_groups").document(group_id).get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Family group not found")
    data = snap.to_dict()
    if data.get("practitioner_id") != uid:
        raise HTTPException(status_code=403, detail="Access denied")
    return data


@router.get("/")
def list_family_groups(user=Depends(require_practitioner)):
    """List family groups owned by the calling practitioner."""
    db = get_db()
    groups = db.collection("family_groups") \
               .where("practitioner_id", "==", user["uid"]) \
               .stream()
    return [{"id": g.id, **g.to_dict()} for g in groups]


@router.post("/")
def create_family_group(body: FamilyGroupCreate, user=Depends(require_practitioner)):
    """Create a new family group owned by the calling practitioner."""
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    data = {
        "name":            body.name,
        "practitioner_id": user["uid"],
        "care_level":      body.care_level,
        "status":          "active",
        "urgent_flags":    [],
        "created_at":      now,
        "updated_at":      now,
    }
    doc_ref = db.collection("family_groups").document()
    doc_ref.set(data)
    return {"id": doc_ref.id, **data}


@router.get("/{group_id}")
def get_family_group(group_id: str, user=Depends(require_practitioner)):
    """Get a single family group the caller owns."""
    db = get_db()
    snap = db.collection("family_groups").document(group_id).get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Family group not found")
    data = snap.to_dict()
    if data.get("practitioner_id") != user["uid"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return {"id": snap.id, **data}


def _invite_email_html(family_name: str, practitioner_name: str, invite_link: str) -> str:
    return f"""
<div style="font-family:'Georgia',serif;max-width:560px;margin:0 auto;">
  <p style="font-size:20px;color:#1e1230;margin-bottom:8px;">
    You've been invited to the Parental Care Guide portal.
  </p>
  <p style="font-family:sans-serif;font-size:15px;color:#4a2d65;margin-bottom:16px;font-weight:300;">
    <strong>{practitioner_name}</strong> has invited you to join the family portal for <strong>{family_name}</strong>. Through the portal you'll be able to see the care plan, medications, crisis information, and recent updates — and message the care coordinator directly.
  </p>
  <p style="margin-bottom:28px;">
    <a href="{invite_link}"
       style="display:inline-block;padding:13px 32px;background:#501464;color:#fff;border-radius:100px;text-decoration:none;font-family:sans-serif;font-size:15px;font-weight:600;">
      Accept invitation
    </a>
  </p>
  <p style="font-family:sans-serif;font-size:12px;color:#9b7db5;margin-bottom:6px;font-weight:300;">
    Or copy and paste this link into your browser:
  </p>
  <p style="font-family:monospace;font-size:11px;color:#6b4d85;word-break:break-all;margin-bottom:24px;">
    {invite_link}
  </p>
  <hr style="border:none;border-top:1px solid #e8d5f0;margin:20px 0;" />
  <p style="font-family:sans-serif;font-size:12px;color:#9b7db5;font-weight:300;line-height:1.5;">
    This link expires in {INVITE_TTL_DAYS} days. If you weren't expecting this invitation, you can safely ignore this email.
  </p>
  <p style="font-family:sans-serif;font-size:13px;color:#6b4d85;margin-top:20px;font-weight:300;">
    — The Parental Care Guide team
  </p>
</div>
"""


def _invite_email_text(family_name: str, practitioner_name: str, invite_link: str) -> str:
    return (
        f"You've been invited to the Parental Care Guide portal.\n\n"
        f"{practitioner_name} has invited you to join the family portal for {family_name}. "
        "Through the portal you'll be able to see the care plan, medications, crisis information, "
        "and recent updates — and message the care coordinator directly.\n\n"
        f"Accept the invitation here:\n{invite_link}\n\n"
        f"This link expires in {INVITE_TTL_DAYS} days. If you weren't expecting this invitation, ignore this email.\n\n"
        "— The Parental Care Guide team"
    )


@router.post("/{group_id}/invite")
def invite_family_member(group_id: str, body: InviteRequest, user=Depends(require_practitioner)):
    """
    Invite a family member to a group the caller owns.

    Creates (or refreshes) a `family_invitations` record, generates a Firebase
    email-link sign-in URL pointing at /accept-invite.html, and sends an email
    via Brevo. The actual claim-setting happens in POST /auth/accept-invite
    after the user signs in via the link.
    """
    db = get_db()
    group_data = _verify_group_ownership(db, group_id, user["uid"])

    email = body.email.strip().lower()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=INVITE_TTL_DAYS)

    # Check for an existing pending invitation for this (email, group_id)
    existing_q = db.collection("family_invitations") \
                   .where("invited_email", "==", email) \
                   .where("family_group_id", "==", group_id) \
                   .stream()
    existing = next(iter(existing_q), None)

    if existing:
        existing_data = existing.to_dict()
        if existing_data.get("status") == "accepted":
            raise HTTPException(
                status_code=409,
                detail="This person has already accepted an invitation to this family group.",
            )
        # Refresh: update expiry, restore status=pending, send a new link
        invitation_ref = existing.reference
        invitation_ref.update({
            "status":               "pending",
            "expires_at":           expires.isoformat(),
            "invited_at":           now.isoformat(),
            "invited_relationship": body.relationship or existing_data.get("invited_relationship", ""),
        })
        invitation_id = existing.id
    else:
        invitation_ref = db.collection("family_invitations").document()
        invitation_ref.set({
            "family_group_id":      group_id,
            "invited_email":        email,
            "invited_relationship": body.relationship,
            "invited_by_uid":       user["uid"],
            "invited_at":           now.isoformat(),
            "expires_at":           expires.isoformat(),
            "status":               "pending",
            "accepted_at":          None,
            "accepted_by_uid":      None,
        })
        invitation_id = invitation_ref.id

    # Generate Firebase email-link sign-in URL
    try:
        action_code_settings = firebase_auth.ActionCodeSettings(
            url=ACCEPT_INVITE_URL,
            handle_code_in_app=True,
        )
        invite_link = firebase_auth.generate_sign_in_with_email_link(email, action_code_settings)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate sign-in link: {str(e)}. "
                   "Confirm that Email/Password sign-in (with email link) is enabled in Firebase Console.",
        )

    # Send the email via Brevo (best-effort fall back, since invitation is already stored)
    family_name      = group_data.get("name", "the family")
    practitioner_doc = db.collection("users").document(user["uid"]).get()
    practitioner_name = (
        practitioner_doc.to_dict().get("full_name", "Your care coordinator")
        if practitioner_doc.exists else "Your care coordinator"
    )

    try:
        brevo.send_email(
            to_email=email,
            to_name="",
            subject=f"Invitation to {family_name}'s care portal — Parental Care Guide",
            html_content=_invite_email_html(family_name, practitioner_name, invite_link),
            text_content=_invite_email_text(family_name, practitioner_name, invite_link),
        )
    except Exception as e:
        # Don't fail the invitation — practitioner can resend
        return {
            "success":       True,
            "invitation_id": invitation_id,
            "email_sent":    False,
            "warning":       f"Invitation stored but email delivery failed: {str(e)}",
        }

    return {
        "success":       True,
        "invitation_id": invitation_id,
        "email_sent":    True,
    }


@router.post("/{group_id}/revoke")
def revoke_family_member(group_id: str, body: RevokeRequest, user=Depends(require_practitioner)):
    """
    Revoke a family member's access to a specific family group.

    Removes the group's id from the target user's family_group_ids claim,
    revokes refresh tokens so the change takes effect on the next request,
    and marks any associated invitation as revoked.
    """
    db = get_db()
    _verify_group_ownership(db, group_id, user["uid"])

    target_uid = body.uid.strip()
    if not target_uid:
        raise HTTPException(status_code=400, detail="uid is required")

    # Fetch existing claims
    try:
        target = firebase_auth.get_user(target_uid)
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")

    existing_claims = dict(target.custom_claims or {})
    group_ids = list(existing_claims.get("family_group_ids") or [])

    if group_id not in group_ids:
        # Nothing to revoke for this group — return idempotently
        return {"success": True, "uid": target_uid, "revoked": False, "remaining_groups": group_ids}

    group_ids = [g for g in group_ids if g != group_id]
    existing_claims["family_group_ids"] = group_ids
    # Keep the "family" label even if all groups are removed — user may be re-invited later

    try:
        firebase_auth.set_custom_user_claims(target_uid, existing_claims)
        firebase_auth.revoke_refresh_tokens(target_uid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update claims: {str(e)}")

    # Also update the user doc
    try:
        db.collection("users").document(target_uid).update({
            "family_group_ids": group_ids,
            "updated_at":       datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        pass  # Claim revocation already succeeded; profile update is non-critical

    # Mark any accepted invitation for this (email, group_id) pair as revoked
    try:
        target_email = (target.email or "").lower()
        if target_email:
            invs = db.collection("family_invitations") \
                     .where("invited_email", "==", target_email) \
                     .where("family_group_id", "==", group_id) \
                     .stream()
            for inv in invs:
                inv.reference.update({
                    "status":     "revoked",
                    "revoked_at": datetime.now(timezone.utc).isoformat(),
                })
    except Exception:
        pass

    return {
        "success":          True,
        "uid":              target_uid,
        "revoked":          True,
        "remaining_groups": group_ids,
    }
