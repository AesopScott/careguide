from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from middleware.auth import require_auth
from services import brevo
from services import twilio_sms

router = APIRouter()


class EmailRequest(BaseModel):
    to_email: str
    to_name: str
    subject: str
    html_content: str
    text_content: Optional[str] = None


class SmsRequest(BaseModel):
    to_phone: str   # E.164 format — e.g. +14155552671
    message: str


class ReminderRequest(BaseModel):
    """
    Generic reminder — plug any feature into this.
    Provide email, phone, or both. At least one is required.
    """
    title: str
    body: str
    email: Optional[str] = None
    phone: Optional[str] = None
    recipient_name: Optional[str] = ""


@router.post("/email")
def send_email(body: EmailRequest, user=Depends(require_auth)):
    try:
        result = brevo.send_email(
            to_email=body.to_email,
            to_name=body.to_name,
            subject=body.subject,
            html_content=body.html_content,
            text_content=body.text_content,
        )
        return {"success": True, "message_id": result.get("messageId")}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Brevo email error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Email delivery failed: {str(e)}")


@router.post("/sms")
def send_sms(body: SmsRequest, user=Depends(require_auth)):
    try:
        result = twilio_sms.send_sms(to_phone=body.to_phone, message=body.message)
        return {"success": True, "message_id": result.get("sid")}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Twilio SMS error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"SMS delivery failed: {str(e)}")


@router.post("/reminder")
def send_reminder(body: ReminderRequest, user=Depends(require_auth)):
    """
    Send a reminder via email and/or SMS.
    Features plug into this endpoint — medication reminders, appointment alerts, etc.
    """
    if not body.email and not body.phone:
        raise HTTPException(status_code=400, detail="At least one of email or phone is required.")

    results = {}

    if body.email:
        try:
            brevo.send_email(
                to_email=body.email,
                to_name=body.recipient_name or "",
                subject=body.title,
                html_content=f"<p>{body.body}</p>",
                text_content=body.body,
            )
            results["email"] = "sent"
        except Exception as e:
            results["email"] = f"failed: {str(e)}"

    if body.phone:
        try:
            twilio_sms.send_sms(
                to_phone=body.phone,
                message=f"{body.title}: {body.body}",
            )
            results["sms"] = "sent"
        except Exception as e:
            results["sms"] = f"failed: {str(e)}"

    any_sent = any(v == "sent" for v in results.values())
    return {"success": any_sent, "results": results}
