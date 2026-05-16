from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from firebase_admin import auth as firebase_auth
from middleware.auth import require_auth
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
<p style="font-family:Georgia,serif;font-size:18px;color:#1e1230;margin-bottom:6px;">
  Welcome to Parental Care Guide, {body.full_name}.
</p>
<p style="font-family:sans-serif;font-size:15px;color:#4a2d65;margin-bottom:16px;">
  Your account is set up and ready. You're one of the first professionals on the platform — we built this for you.
</p>
<hr style="border:none;border-top:1px solid #e8d5f0;margin:20px 0;" />
<p style="font-family:sans-serif;font-size:13px;color:#6b4d85;margin-bottom:4px;">
  <strong>Role:</strong> {profession_label}
</p>
<p style="font-family:sans-serif;font-size:13px;color:#6b4d85;margin-bottom:20px;">
  <strong>License states:</strong> {states_str}
</p>
<p style="font-family:sans-serif;font-size:13px;color:#4a2d65;">
  You're on <strong>Beta Access</strong> — free while we build. We'll notify you well before billing begins, and you'll lock in a founding member rate.
</p>
<p style="font-family:sans-serif;font-size:13px;color:#6b4d85;margin-top:20px;">
  — The Parental Care Guide team
</p>
"""
            brevo.send_email(
                to_email=email,
                to_name=body.full_name,
                subject="Welcome to Parental Care Guide",
                html_content=html,
                text_content=(
                    f"Welcome to Parental Care Guide, {body.full_name}.\n\n"
                    f"Your account is ready. Role: {profession_label}. "
                    f"License states: {states_str}.\n\n"
                    "You're on Beta Access — free while we build. "
                    "We'll notify you before billing begins."
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
