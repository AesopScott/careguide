from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from services import brevo

router = APIRouter()

OWNER_EMAIL = "scott@parentalcareguide.com"
OWNER_NAME  = "Scott — PCG"

ROLE_LABELS = {
    "care_advocate": "Care Advocate (family caregiver)",
    "practitioner":  "Practitioner",
    "care_recipient": "Care Recipient",
    "other":         "Other",
}


class ContactRequest(BaseModel):
    first_name: str
    last_name:  str
    email:      str
    role:       Optional[str] = "other"
    subject:    str
    message:    str


@router.post("/contact")
def submit_contact(body: ContactRequest):
    """
    Public contact form. No auth required.
    Sends the message to the site owner and a confirmation to the sender.
    """
    full_name   = f"{body.first_name.strip()} {body.last_name.strip()}".strip()
    role_label  = ROLE_LABELS.get(body.role or "other", body.role or "—")

    # ── Email to owner ────────────────────────────────────────────────────────
    owner_html = f"""
<div style="font-family:sans-serif;max-width:560px;margin:0 auto;">
  <p style="font-size:18px;color:#1e1230;font-family:Georgia,serif;margin-bottom:16px;">
    New contact form submission
  </p>
  <table style="border-collapse:collapse;width:100%;margin-bottom:20px;">
    <tr>
      <td style="padding:8px 12px;background:#f8f4fb;font-weight:600;width:110px;color:#4a2d65;border-radius:4px 0 0 4px;">Name</td>
      <td style="padding:8px 12px;border-bottom:1px solid #e8d5f0;">{full_name}</td>
    </tr>
    <tr>
      <td style="padding:8px 12px;background:#f8f4fb;font-weight:600;color:#4a2d65;">Email</td>
      <td style="padding:8px 12px;border-bottom:1px solid #e8d5f0;">
        <a href="mailto:{body.email}" style="color:#501464;">{body.email}</a>
      </td>
    </tr>
    <tr>
      <td style="padding:8px 12px;background:#f8f4fb;font-weight:600;color:#4a2d65;">Role</td>
      <td style="padding:8px 12px;border-bottom:1px solid #e8d5f0;">{role_label}</td>
    </tr>
    <tr>
      <td style="padding:8px 12px;background:#f8f4fb;font-weight:600;color:#4a2d65;">Subject</td>
      <td style="padding:8px 12px;border-bottom:1px solid #e8d5f0;">{body.subject}</td>
    </tr>
  </table>
  <div style="background:#f8f4fb;border-left:3px solid #501464;padding:16px 20px;border-radius:0 8px 8px 0;">
    <p style="margin:0;color:#1e1230;line-height:1.6;white-space:pre-wrap;">{body.message}</p>
  </div>
</div>
"""

    owner_text = (
        f"New contact from {full_name} ({body.email})\n"
        f"Role: {role_label}\n"
        f"Subject: {body.subject}\n\n"
        f"{body.message}"
    )

    # ── Confirmation email to sender ──────────────────────────────────────────
    confirm_html = f"""
<div style="font-family:'Georgia',serif;max-width:560px;margin:0 auto;">
  <p style="font-size:20px;color:#1e1230;margin-bottom:8px;">
    We got your message, {body.first_name}.
  </p>
  <p style="font-family:sans-serif;font-size:15px;color:#4a2d65;margin-bottom:16px;font-weight:300;">
    Thanks for reaching out. We'll get back to you within one to two business days.
  </p>
  <div style="background:#f8f4fb;border-left:3px solid #501464;padding:14px 18px;border-radius:0 8px 8px 0;margin-bottom:20px;">
    <p style="font-family:sans-serif;font-size:13px;color:#6b4d85;margin:0 0 4px;font-weight:600;">{body.subject}</p>
    <p style="font-family:sans-serif;font-size:14px;color:#1e1230;margin:0;line-height:1.6;white-space:pre-wrap;">{body.message}</p>
  </div>
  <hr style="border:none;border-top:1px solid #e8d5f0;margin:20px 0;" />
  <p style="font-family:sans-serif;font-size:13px;color:#6b4d85;font-weight:300;">
    — The Parental Care Guide team<br>
    <a href="https://parentalcareguide.com" style="color:#501464;">parentalcareguide.com</a>
  </p>
</div>
"""

    confirm_text = (
        f"Hi {body.first_name},\n\n"
        "We got your message and will get back to you within 1–2 business days.\n\n"
        f"Subject: {body.subject}\n\n"
        f"{body.message}\n\n"
        "— The Parental Care Guide team\n"
        "parentalcareguide.com"
    )

    errors = []

    # Send to owner
    try:
        brevo.send_email(
            to_email=OWNER_EMAIL,
            to_name=OWNER_NAME,
            subject=f"[PCG Contact] {body.subject} — {full_name}",
            html_content=owner_html,
            text_content=owner_text,
        )
    except Exception as e:
        errors.append(f"owner delivery failed: {str(e)}")

    # Send confirmation to sender (best-effort — never fail the submission)
    try:
        brevo.send_email(
            to_email=body.email,
            to_name=full_name,
            subject="We received your message — Parental Care Guide",
            html_content=confirm_html,
            text_content=confirm_text,
        )
    except Exception:
        pass

    if errors:
        raise HTTPException(status_code=502, detail="; ".join(errors))

    return {"success": True, "email": body.email}
