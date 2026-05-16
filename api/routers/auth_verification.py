import secrets
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import auth as firebase_auth
from middleware.auth import require_auth
from services.firebase import get_db
from services import brevo

router = APIRouter()

TOKEN_TTL_HOURS = 24
VERIFY_URL_BASE = "https://parentalcareguide.com/verify-email.html"


def _verification_email_html(full_name: str, verify_url: str) -> str:
    first = full_name.split()[0] if full_name else "there"
    return f"""
<div style="font-family:'Georgia',serif;max-width:560px;margin:0 auto;">
  <p style="font-size:20px;color:#1e1230;margin-bottom:8px;">
    Verify your email, {first}.
  </p>
  <p style="font-family:sans-serif;font-size:15px;color:#4a2d65;margin-bottom:24px;font-weight:300;">
    One quick step before your application goes to review. Click the button below to confirm your email address.
  </p>
  <p style="margin-bottom:28px;">
    <a href="{verify_url}"
       style="display:inline-block;padding:13px 32px;background:#501464;color:#fff;border-radius:100px;text-decoration:none;font-family:sans-serif;font-size:15px;font-weight:600;">
      Verify my email
    </a>
  </p>
  <p style="font-family:sans-serif;font-size:12px;color:#9b7db5;margin-bottom:6px;font-weight:300;">
    Or copy and paste this link into your browser:
  </p>
  <p style="font-family:monospace;font-size:11px;color:#6b4d85;word-break:break-all;margin-bottom:24px;">
    {verify_url}
  </p>
  <hr style="border:none;border-top:1px solid #e8d5f0;margin:20px 0;" />
  <p style="font-family:sans-serif;font-size:12px;color:#9b7db5;font-weight:300;line-height:1.5;">
    This link expires in 24 hours. If you didn't create a Parental Care Guide account, you can safely ignore this email.
  </p>
  <p style="font-family:sans-serif;font-size:13px;color:#6b4d85;margin-top:20px;font-weight:300;">
    — The Parental Care Guide team
  </p>
</div>
"""


def _verification_email_text(full_name: str, verify_url: str) -> str:
    first = full_name.split()[0] if full_name else "there"
    return (
        f"Verify your email, {first}.\n\n"
        "Click the link below to confirm your email address:\n"
        f"{verify_url}\n\n"
        "This link expires in 24 hours.\n\n"
        "If you didn't create a Parental Care Guide account, ignore this email.\n\n"
        "— The Parental Care Guide team"
    )


@router.post("/auth/send-verification")
async def send_verification(user: dict = Depends(require_auth)):
    """
    Generate a secure email verification token, store it in Firestore,
    and send a branded verification email via Brevo.
    Called immediately after signup while the user is authenticated.
    """
    uid   = user["uid"]
    email = user.get("email", "")

    if not email:
        raise HTTPException(status_code=400, detail="No email address on this account.")

    # Re-check: if already verified, nothing to do
    try:
        fb_user = firebase_auth.get_user(uid)
        if fb_user.email_verified:
            return {"success": True, "already_verified": True}
    except Exception:
        pass

    db = get_db()

    # Look up the Firestore user profile for full_name
    full_name = email.split("@")[0]
    try:
        snap = db.collection("users").document(uid).get()
        if snap.exists:
            full_name = snap.to_dict().get("full_name", full_name)
    except Exception:
        pass

    # Generate a cryptographically secure token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS)

    # Store token in Firestore
    try:
        db.collection("email_verification_tokens").document(token).set({
            "uid":        uid,
            "email":      email,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at.isoformat(),
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store verification token: {str(e)}")

    # Send the email
    verify_url = f"{VERIFY_URL_BASE}?token={token}"
    try:
        brevo.send_email(
            to_email=email,
            to_name=full_name,
            subject="Verify your email — Parental Care Guide",
            html_content=_verification_email_html(full_name, verify_url),
            text_content=_verification_email_text(full_name, verify_url),
        )
    except Exception as e:
        # Clean up the token if email fails — user can retry
        try:
            db.collection("email_verification_tokens").document(token).delete()
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=f"Failed to send verification email: {str(e)}")

    return {"success": True, "email": email}


@router.post("/auth/accept-invite")
async def accept_invite(user: dict = Depends(require_auth)):
    """
    Called by /accept-invite.html after the user signs in via Firebase email
    link. Looks up any pending family_invitations matching the signed-in
    user's email, sets the "family" claim, appends each group's id to the
    family_group_ids array claim, writes/merges the users doc, and marks
    each invitation accepted.
    """
    uid   = user["uid"]
    email = (user.get("email") or "").strip().lower()

    if not email:
        raise HTTPException(status_code=400, detail="No email address on this account.")

    db = get_db()
    now = datetime.now(timezone.utc).isoformat()

    # Find pending invitations matching the signed-in email
    pending_q = db.collection("family_invitations") \
                  .where("invited_email", "==", email) \
                  .where("status", "==", "pending") \
                  .stream()
    pending = list(pending_q)

    if not pending:
        # Not an error — the user may have used the link just to sign in.
        # Return zero accepted so the client can show the right message.
        return {"success": True, "accepted": [], "family_group_ids": []}

    # Filter out expired
    accepted_invites = []
    accepted_group_ids: list[str] = []
    primary_relationship = ""

    for inv in pending:
        data = inv.to_dict()
        # Expiry check
        try:
            expires_at = datetime.fromisoformat(data["expires_at"])
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires_at:
                inv.reference.update({"status": "expired", "expired_at": now})
                continue
        except Exception:
            continue

        group_id = data.get("family_group_id")
        if not group_id:
            continue

        inv.reference.update({
            "status":          "accepted",
            "accepted_at":     now,
            "accepted_by_uid": uid,
        })
        accepted_invites.append(inv.id)
        accepted_group_ids.append(group_id)
        if not primary_relationship and data.get("invited_relationship"):
            primary_relationship = data["invited_relationship"]

    if not accepted_group_ids:
        return {"success": True, "accepted": [], "family_group_ids": [], "warning": "All matching invitations were expired."}

    # Merge accepted groups into the user's existing claims (deduped, preserving order)
    try:
        target = firebase_auth.get_user(uid)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to read user record.")

    existing_claims = dict(target.custom_claims or {})
    current_groups  = list(existing_claims.get("family_group_ids") or [])
    for gid in accepted_group_ids:
        if gid not in current_groups:
            current_groups.append(gid)

    existing_claims["family"] = True
    existing_claims["family_group_ids"] = current_groups

    try:
        firebase_auth.set_custom_user_claims(uid, existing_claims)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set claims: {str(e)}")

    # Write/merge the user document
    user_ref = db.collection("users").document(uid)
    snap = user_ref.get()
    existing_user = snap.to_dict() if snap.exists else {}
    user_payload: dict = {
        "uid":               uid,
        "email":             email,
        "role":              "family",
        "family_group_ids":  current_groups,
        "updated_at":        now,
    }
    if primary_relationship and not existing_user.get("relationship_to_parent"):
        user_payload["relationship_to_parent"] = primary_relationship
    if not existing_user:
        user_payload["full_name"]  = target.display_name or email.split("@")[0]
        user_payload["created_at"] = now
    user_ref.set(user_payload, merge=True)

    return {
        "success":          True,
        "accepted":         accepted_invites,
        "family_group_ids": current_groups,
    }


@router.post("/auth/verify-email")
async def verify_email(token: str):
    """
    Validate an email verification token and mark the Firebase Auth user as verified.
    No authentication required — the token IS the credential.
    """
    if not token or len(token) < 16:
        raise HTTPException(status_code=400, detail="Invalid token.")

    db = get_db()
    token_ref = db.collection("email_verification_tokens").document(token)

    try:
        snap = token_ref.get()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if not snap.exists:
        raise HTTPException(status_code=404, detail="Verification link not found or already used.")

    data = snap.to_dict()
    uid  = data.get("uid")

    # Check expiry
    try:
        expires_at = datetime.fromisoformat(data["expires_at"])
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires_at:
            token_ref.delete()
            raise HTTPException(status_code=410, detail="Verification link has expired. Please request a new one.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Could not validate token expiry.")

    # Mark the Firebase Auth user as email-verified
    try:
        firebase_auth.update_user(uid, email_verified=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify account: {str(e)}")

    # Delete the used token (one-time use)
    try:
        token_ref.delete()
    except Exception:
        pass  # Non-critical — token is already validated

    return {"success": True, "uid": uid}
