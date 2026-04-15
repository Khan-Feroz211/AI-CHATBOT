"""Twilio WhatsApp outbound helper."""
from bazaarbot.config import config


def send_whatsapp(to: str, body: str) -> bool:
    """Send a WhatsApp message via Twilio. Returns True on success."""
    sid = config.TWILIO_ACCOUNT_SID
    token = config.TWILIO_AUTH_TOKEN
    if not sid or not token:
        print(f"[WhatsApp] Not configured — would send to {to}: {body[:60]}")
        return False
    try:
        from twilio.rest import Client
        client = Client(sid, token)
        to_num = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
        msg = client.messages.create(
            body=body,
            from_=config.TWILIO_WHATSAPP_FROM,
            to=to_num,
        )
        print(f"[WhatsApp] Sent SID={msg.sid}")
        return True
    except Exception as exc:
        print(f"[WhatsApp] Error: {exc}")
        return False
