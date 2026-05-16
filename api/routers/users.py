from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime, timezone

from firebase_admin import auth as firebase_auth
from middleware.auth import require_auth, require_admin
from services.firebase import get_db
from services import brevo

router = APIRouter()

PROFESSION_LABELS = {
    "gcm":         "Geriatric Care Manager",
    "elder_law":   "Elder Law Attorney",
    "social_work": "Social Worker",
    "financial":   "Financial Planner",
}

PROFESSION_PLANS = {
    "gcm":         "standard",
    "elder_law":   "premium",
    "social_work": "standard",
    "financial":   "standard",
}

PROFESSION_MONTHLY_RATE = {
    "gcm":         149,
    "elder_law":   199,
    "social_work": 149,
    "financial":   149,
}


class RegisterRequest(BaseModel):
    full_name: str
    profession: str       # gcm | elder_law | social_work | financial
    license_states: list[str]
    beta: bool = True


@router.post("/register")
async def register_practitioner(body: RegisterRequest, user: dict = Depends(require_auth)):
    """
    Called immediately after Firebase Auth account creation on the client.
    Sets practitioner custom claim, stores Firestore profile, sends welcome email.
    """
    uid = user["uid"]

    if body.profession not in PROFESSION_LABELS:
        raise HTTPException(status_code=400, detail=f"Unknown profession: {body.profession}")

    if not body.license_states:
        raise HTTPException(status_code=400, detail="At least one license state is required.")

    # 1. Set custom claims on Firebase Auth token
    try:
        firebase_auth.set_custom_user_claims(uid, {
            "practitioner": True,
            "profession":   body.profession,
            "beta":         body.beta,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set user claims: {str(e)}")

    # 2. Write user profile to Firestore
    try:
        db  = get_db()
        doc = db.collection("users").document(uid)
        doc.set({
            "uid":            uid,
            "email":          user.get("email", ""),
            "full_name":      body.full_name,
            "role":           "practitioner",
            "profession":     body.profession,
            "profession_label": PROFESSION_LABELS[body.profession],
            "license_states": body.license_states,
            "plan":           PROFESSION_PLANS[body.profession],
            "monthly_rate":   PROFESSION_MONTHLY_RATE[body.profession],
            "beta":           body.beta,
            "status":         "pending_activation",
            "baa_accepted":   True,
            "baa_accepted_at": datetime.now(timezone.utc).isoformat(),
            "created_at":     datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save user profile: {str(e)}")

    # 3. Send welcome email (non-blocking — don't fail registration if email fails)
    email = user.get("email", "")
    if email:
        try:
            profession_label = PROFESSION_LABELS[body.profession]
            states_str = ", ".join(body.license_states)
            html = f"""
<div style="font-family:'Georgia',serif;max-width:560px;margin:0 auto;">
  <p style="font-size:20px;color:#1e1230;margin-bottom:8px;">
    We received your application, {body.full_name}.
  </p>
  <p style="font-family:sans-serif;font-size:15px;color:#4a2d65;margin-bottom:16px;font-weight:300;">
    Thank you for signing up as a practitioner on Parental Care Guide. Your application is now pending review — we'll be in touch soon.
  </p>
  <hr style="border:none;border-top:1px solid #e8d5f0;margin:20px 0;" />
  <p style="font-family:sans-serif;font-size:13px;color:#6b4d85;margin-bottom:4px;">
    <strong>Role:</strong> {profession_label}
  </p>
  <p style="font-family:sans-serif;font-size:13px;color:#6b4d85;margin-bottom:20px;">
    <strong>License states:</strong> {states_str}
  </p>
  <div style="background:#f8f4fb;border-left:3px solid #501464;padding:14px 18px;border-radius:0 8px 8px 0;margin-bottom:20px;">
    <p style="font-family:sans-serif;font-size:13px;color:#1e1230;margin:0 0 6px;font-weight:600;">What happens next</p>
    <p style="font-family:sans-serif;font-size:13px;color:#4a2d65;margin:0;line-height:1.6;font-weight:300;">
      1. Verify your email address (link in a separate email)<br>
      2. Our team reviews your application<br>
      3. You'll receive an approval email when you're cleared to sign in
    </p>
  </div>
  <p style="font-family:sans-serif;font-size:13px;color:#6b4d85;font-weight:300;">
    You're on <strong>Beta Access</strong> — free while we build. We'll notify you well before billing begins, and you'll lock in a founding member rate.
  </p>
  <p style="font-family:sans-serif;font-size:13px;color:#6b4d85;margin-top:20px;font-weight:300;">
    — The Parental Care Guide team
  </p>
</div>
"""
            brevo.send_email(
                to_email=email,
                to_name=body.full_name,
                subject="We received your application — Parental Care Guide",
                html_content=html,
                text_content=(
                    f"We received your application, {body.full_name}.\n\n"
                    f"Role: {profession_label}\n"
                    f"License states: {states_str}\n\n"
                    "What happens next:\n"
                    "1. Verify your email address\n"
                    "2. Our team reviews your application\n"
                    "3. You'll receive an approval email when you're cleared to sign in\n\n"
                    "You're on Beta Access — free while we build.\n"
                    "— The Parental Care Guide team"
                ),
            )
        except Exception:
            pass  # Never block registration on email failure

    return {
        "success":    True,
        "uid":        uid,
        "role":       "practitioner",
        "profession": body.profession,
        "beta":       body.beta,
    }


# ── Approval email templates ──────────────────────────────────────────────────

def _approval_email_html(full_name: str) -> str:
    return f"""
<div style="font-family:'Georgia',serif;max-width:560px;margin:0 auto;">
  <p style="font-size:20px;color:#1e1230;margin-bottom:8px;">
    You've been approved, {full_name}.
  </p>
  <p style="font-family:sans-serif;font-size:15px;color:#4a2d65;margin-bottom:20px;font-weight:300;">
    Your Parental Care Guide practitioner account is now active. You can sign in and access your dashboard right away.
  </p>
  <p style="margin-bottom:24px;">
    <a href="https://parentalcareguide.com/dashboard.html"
       style="display:inline-block;padding:12px 28px;background:#501464;color:#fff;border-radius:100px;text-decoration:none;font-family:sans-serif;font-size:15px;font-weight:600;">
      Go to Dashboard
    </a>
  </p>
  <hr style="border:none;border-top:1px solid #e8d5f0;margin:24px 0;" />
  <p style="font-family:sans-serif;font-size:13px;color:#6b4d85;font-weight:300;">
    You're on <strong>Beta Access</strong> — no billing during the beta. We'll notify you well before any charges begin, and you'll lock in a founding-member rate.
  </p>
  <p style="font-family:sans-serif;font-size:13px;color:#6b4d85;margin-top:16px;font-weight:300;">
    — The Parental Care Guide team
  </p>
</div>
"""


def _approval_email_text(full_name: str) -> str:
    return (
        f"You've been approved, {full_name}.\n\n"
        "Your Parental Care Guide practitioner account is now active.\n"
        "Sign in at: https://parentalcareguide.com/dashboard.html\n\n"
        "You're on Beta Access — no billing during the beta.\n"
        "— The Parental Care Guide team"
    )


def _rejection_email_html(full_name: str) -> str:
    return f"""
<div style="font-family:'Georgia',serif;max-width:560px;margin:0 auto;">
  <p style="font-size:20px;color:#1e1230;margin-bottom:8px;">
    An update on your application, {full_name}.
  </p>
  <p style="font-family:sans-serif;font-size:15px;color:#4a2d65;margin-bottom:16px;font-weight:300;">
    After reviewing your practitioner application, we're not able to approve access at this time.
  </p>
  <p style="font-family:sans-serif;font-size:14px;color:#6b4d85;margin-bottom:20px;font-weight:300;">
    If you believe this was an error or have questions, please reply to this email or reach us at
    <a href="mailto:support@parentalcareguide.com" style="color:#501464;">support@parentalcareguide.com</a>.
  </p>
  <hr style="border:none;border-top:1px solid #e8d5f0;margin:24px 0;" />
  <p style="font-family:sans-serif;font-size:13px;color:#6b4d85;font-weight:300;">
    — The Parental Care Guide team
  </p>
</div>
"""


def _rejection_email_text(full_name: str) -> str:
    return (
        f"An update on your application, {full_name}.\n\n"
        "After reviewing your practitioner application, we're not able to approve access at this time.\n\n"
        "If you believe this was an error, reply to this email or contact support@parentalcareguide.com.\n\n"
        "— The Parental Care Guide team"
    )


# ── Status endpoint ───────────────────────────────────────────────────────────

class StatusRequest(BaseModel):
    status: Literal["active", "rejected"]


@router.post("/{uid}/status")
async def set_user_status(
    uid: str,
    body: StatusRequest,
    admin: dict = Depends(require_admin),
):
    """
    Admin-only: approve or reject a practitioner.
    Sets/clears Firebase Auth custom claims and sends an email notification.
    """
    db = get_db()
    user_ref = db.collection("users").document(uid)
    snap = user_ref.get()

    if not snap.exists:
        raise HTTPException(status_code=404, detail=f"User {uid} not found in Firestore")

    user_data = snap.to_dict()
    full_name  = user_data.get("full_name", "")
    email      = user_data.get("email", "")
    profession = user_data.get("profession", "")

    # 1. Update custom claims
    try:
        if body.status == "active":
            firebase_auth.set_custom_user_claims(uid, {
                "practitioner": True,
                "profession":   profession,
                "beta":         user_data.get("beta", True),
            })
        else:
            firebase_auth.set_custom_user_claims(uid, {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update Firebase claims: {str(e)}")

    # 2. Update Firestore status
    try:
        update_payload: dict = {"status": body.status}
        if body.status == "active":
            update_payload["active_at"] = datetime.now(timezone.utc).isoformat()
        else:
            update_payload["rejected_at"] = datetime.now(timezone.utc).isoformat()
        user_ref.update(update_payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update Firestore: {str(e)}")

    # 3. Send notification email (non-blocking)
    if email:
        try:
            if body.status == "active":
                brevo.send_email(
                    to_email=email,
                    to_name=full_name,
                    subject="You've been approved — Parental Care Guide",
                    html_content=_approval_email_html(full_name),
                    text_content=_approval_email_text(full_name),
                )
            else:
                brevo.send_email(
                    to_email=email,
                    to_name=full_name,
                    subject="An update on your Parental Care Guide application",
                    html_content=_rejection_email_html(full_name),
                    text_content=_rejection_email_text(full_name),
                )
        except Exception:
            pass  # Never fail the status update over an email error

    return {"success": True, "uid": uid, "status": body.status}
