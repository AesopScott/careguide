import httpx
import os

TWILIO_API_URL = "https://api.twilio.com/2010-04-01/Accounts"


def send_sms(to_phone: str, message: str) -> dict:
    """
    Send an SMS via Twilio.
    to_phone must be in E.164 format, e.g. +14155552671
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token  = os.getenv("TWILIO_AUTH_TOKEN")
    from_phone  = os.getenv("TWILIO_PHONE_NUMBER")

    with httpx.Client(timeout=10.0) as client:
        r = client.post(
            f"{TWILIO_API_URL}/{account_sid}/Messages.json",
            auth=(account_sid, auth_token),
            data={"From": from_phone, "To": to_phone, "Body": message},
        )
        r.raise_for_status()
        return r.json()
