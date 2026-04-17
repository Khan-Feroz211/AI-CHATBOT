"""Async appointment reminder tasks for BazaarBot.

Appointment reminders are dispatched from the Celery 'appointments' queue
so that SMTP I/O never blocks the webhook handler.
"""
import logging
from datetime import date, timedelta

from bazaarbot.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="bazaarbot.tasks.appointment_tasks.send_appointment_reminder",
)
def send_appointment_reminder(
    self,
    tenant_slug: str,
    appointment_id: int,
    customer_phone: str,
    customer_name: str,
    apt_date: str,
    apt_time: str,
    purpose: str,
) -> dict:
    """Send a 24-hour reminder email for a single appointment.

    The reminder is addressed to the tenant's notification email because
    BazaarBot stores the customer's *phone* number, not their email.
    Retries up to 3 times (60-second delay) on failure.

    Returns ``{"success": bool, "appointment_id": int}``.
    """
    try:
        from bazaarbot.database_pg import get_tenant
        from bazaarbot.tasks.email_tasks import send_notification_email

        tenant = get_tenant(tenant_slug)
        if not tenant or not tenant.get("notify_email"):
            logger.warning(
                "send_appointment_reminder: no notify_email for tenant %s", tenant_slug
            )
            return {"success": False, "reason": "no_notify_email"}

        body = (
            f"Appointment Reminder \u2014 {tenant['name']}\n\n"
            f"Kal ka appointment yaad dilana tha:\n\n"
            f"Customer: {customer_name or customer_phone}\n"
            f"Phone: {customer_phone}\n"
            f"Date: {apt_date}\n"
            f"Time: {apt_time}\n"
            f"Purpose: {purpose or 'Business visit'}\n\n"
            f"\u2014 BazaarBot"
        )

        send_notification_email.delay(
            to_email=tenant["notify_email"],
            subject=f"Appointment Reminder \u2014 {apt_date} {apt_time}",
            body=body,
            tenant_slug=tenant_slug,
        )

        logger.info(
            "Appointment reminder queued: id=%d tenant=%s date=%s",
            appointment_id,
            tenant_slug,
            apt_date,
        )
        return {"success": True, "appointment_id": appointment_id}
    except Exception as exc:
        logger.error("send_appointment_reminder failed (id=%d): %s", appointment_id, exc)
        raise self.retry(exc=exc)


@celery.task(
    name="bazaarbot.tasks.appointment_tasks.send_daily_reminders",
)
def send_daily_reminders() -> dict:
    """Dispatch reminder emails for all appointments scheduled for tomorrow.

    Scheduled daily at 08:00 PKT by Celery Beat.  Iterates all active
    tenants and fetches their upcoming appointments for the next calendar
    day, then fires individual :func:`send_appointment_reminder` sub-tasks.

    Returns a summary of how many reminders were dispatched.
    """
    from bazaarbot.database_pg import get_appointments, list_tenants

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    tenants = list_tenants()
    active = [t for t in tenants if t.get("is_active", True)]

    total_sent = 0
    for tenant in active:
        tenant_slug = tenant["slug"]
        # Fetch all upcoming appointments and filter for tomorrow
        appointments = get_appointments(tenant_slug, upcoming_only=True, limit=100)
        tomorrow_apts = [a for a in appointments if a.get("appointment_date") == tomorrow]

        for apt in tomorrow_apts:
            send_appointment_reminder.delay(
                tenant_slug=tenant_slug,
                appointment_id=apt["id"],
                customer_phone=apt.get("phone", ""),
                customer_name=apt.get("customer_name", ""),
                apt_date=apt.get("appointment_date", ""),
                apt_time=apt.get("appointment_time", ""),
                purpose=apt.get("purpose", ""),
            )
            total_sent += 1

    logger.info(
        "send_daily_reminders: dispatched %d reminders for %s",
        total_sent,
        tomorrow,
    )
    return {"success": True, "reminders_sent": total_sent, "date": tomorrow}
