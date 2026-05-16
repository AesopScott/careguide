import httpx
import os
from typing import Optional

BREVO_API_URL = "https://api.brevo.com/v3"
SENDER_NAME  = "Parental Care Guide"
SENDER_EMAIL = "noreply@mail.parentalcareguide.com"
SMS_SENDER   = "PCG"  # max 11 chars, alphanumeric, shown as sender name on SMS


def _headers() -> dict:
    return {
        "api-key": os.getenv("BREVO_API_KEY"),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
) -> dict:
    """Send a transactional email via Brevo. Returns Brevo's response dict."""
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "htmlContent": html_content,
    }
    if text_content:
        payload["textContent"] = text_content

    with httpx.Client(timeout=10.0) as client:
        r = client.post(f"{BREVO_API_URL}/smtp/email", headers=_headers(), json=payload)
        r.raise_for_status()
        return r.json()


def send_sms(to_phone: str, message: str) -> dict:
    """
    Send a transactional SMS via Brevo.
    to_phone must be in E.164 format, e.g. +14155552671
    """
    payload = {
        "sender": SMS_SENDER,
        "recipient": to_phone,
        "content": message,
    }

    with httpx.Client(timeout=10.0) as client:
        r = client.post(f"{BREVO_API_URL}/transactionalSMS/sms", headers=_headers(), json=payload)
        r.raise_for_status()
        return r.json()
