"""Email notifications via stdlib smtplib — no extra dependencies."""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bazaarbot.config import config


def send_email(to: str, subject: str, body: str, html: str = "") -> bool:
    """Send an email. Returns True on success."""
    if not config.SMTP_USER or not config.SMTP_PASS:
        print(f"[Email] SMTP not configured — would send '{subject}' to {to}")
        return False
    if not to:
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = config.SMTP_USER
        msg["To"] = to
        msg.attach(MIMEText(body, "plain", "utf-8"))
        if html:
            msg.attach(MIMEText(html, "html", "utf-8"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=ctx)
            server.login(config.SMTP_USER, config.SMTP_PASS)
            server.sendmail(config.SMTP_USER, to, msg.as_string())
        print(f"[Email] Sent '{subject}' to {to}")
        return True
    except Exception as exc:
        print(f"[Email] Error: {exc}")
        return False


def send_order_confirmation(to: str, order_ref: str,
                            product: str, qty: int, total: float) -> bool:
    subject = f"BazaarBot — Order Confirm: {order_ref}"
    body = (
        f"Shukriya aapke order ke liye!\n\n"
        f"Order Ref: {order_ref}\n"
        f"Product: {product}\n"
        f"Qty: {qty}\n"
        f"Total: Rs.{total:,.0f}\n\n"
        f"Hum aapko update denge jab order ship ho.\n"
        f"— BazaarBot Team"
    )
    return send_email(to, subject, body)


def send_low_stock_alert(to: str, items: list) -> bool:
    subject = "BazaarBot — Low Stock Alert!"
    lines = ["Niche diye gaye items ka stock kam ho gaya hai:\n"]
    for item in items:
        lines.append(
            f"• {item['product_name']} — {item['quantity']} {item['unit']} "
            f"bache hain (reorder level: {item['reorder_level']})"
        )
    body = "\n".join(lines) + "\n\n— BazaarBot"
    return send_email(to, subject, body)


def send_appointment_confirmation(to: str, apt_id,
                                  date: str, time_str: str,
                                  purpose: str) -> bool:
    subject = f"BazaarBot — Appointment #{apt_id} Confirm"
    body = (
        f"Aapki appointment confirm ho gayi!\n\n"
        f"Date: {date}\n"
        f"Time: {time_str}\n"
        f"Purpose: {purpose or 'Business visit'}\n\n"
        f"— BazaarBot Team"
    )
    return send_email(to, subject, body)
