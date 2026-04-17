"""Async appointment reminder tasks for BazaarBot.

Appointment reminders are dispatched from the Celery 'appointments' queue
so that Twilio API latency never blocks the webhook handler.
"""
import logging
from datetime import date, datetime, timedelta, timezone

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
    appointment_id: int,
    tenant_slug: str,
) -> dict:
    """Send a WhatsApp reminder for a specific upcoming appointment.

    Looks up the appointment in the database.  If the appointment is not
    found or has already been cancelled, the task returns early without
    sending a message.

    Message template (Roman Urdu + English):

        "Assalam o Alaikum <name>!
         Reminder: Aapki appointment kal <time> baje hai <business> mein.
         Kaam: <purpose>
         Confirm karne ke liye 'CONFIRM' likhein ya cancel ke liye 'CANCEL'."

    Retries up to 3 times (60-second delay) on Twilio failures.
    Returns ``{"success": bool, "appointment_id": int, "sent_to": phone}``.
    """
    try:
        from bazaarbot.database_pg import get_appointments, get_tenant
        from bazaarbot.tasks.alert_tasks import send_whatsapp_alert

        appointments = get_appointments(tenant_slug, upcoming_only=False, limit=200)
        appt = next(
            (a for a in appointments if a["id"] == appointment_id),
            None,
        )
        if not appt:
            logger.warning(
                "send_appointment_reminder: appointment not found for tenant=%s",
                tenant_slug,
            )
            return {"success": False, "reason": "not_found"}

        if appt["status"] != "booked":
            logger.info(
                "send_appointment_reminder: skipping non-booked appointment "
                "(status=%s tenant=%s)",
                appt["status"], tenant_slug,
            )
            return {"success": False, "reason": "status_not_booked"}

        tenant = get_tenant(tenant_slug)
        business_name = tenant["name"] if tenant else tenant_slug
        customer = appt.get("customer_name") or appt.get("phone", "")

        message = (
            f"Assalam o Alaikum {customer}!\n\n"
            f"Reminder: Aapki appointment kal "
            f"{appt['appointment_time']} baje hai "
            f"{business_name} mein.\n"
            f"Kaam: {appt.get('purpose') or 'Business visit'}\n\n"
            f"Confirm karne ke liye 'CONFIRM' likhein "
            f"ya cancel ke liye 'CANCEL'."
        )

        send_whatsapp_alert.delay(
            to_number=appt["phone"],
            message=message,
            tenant_slug=tenant_slug,
        )

        logger.info(
            "send_appointment_reminder: queued for tenant=%s date=%s",
            tenant_slug, appt.get("appointment_date"),
        )
        return {
            "success": True,
            "appointment_id": appointment_id,
            "sent_to": appt["phone"],
        }
    except Exception as exc:
        logger.error(
            "send_appointment_reminder failed (tenant=%s): %s", tenant_slug, exc,
        )
        raise self.retry(exc=exc)


@celery.task(
    name="bazaarbot.tasks.appointment_tasks.send_daily_reminders",
)
def send_daily_reminders() -> dict:
    """Dispatch WhatsApp reminders for all appointments scheduled for tomorrow.

    Scheduled daily at 08:00 PKT by Celery Beat.  Queries the
    ``appointments`` table directly (via the async session) for all
    ``booked`` appointments whose date equals tomorrow, then fires an
    individual :func:`send_appointment_reminder` sub-task for each one.

    Returns the number of reminders queued and the target date.
    """
    from bazaarbot.database_pg import _run, AsyncSessionLocal
    from bazaarbot.models import Appointment
    from sqlalchemy import select

    tomorrow_str = (datetime.now(tz=timezone.utc).date() + timedelta(days=1)).isoformat()

    async def _get_appointments():
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Appointment).where(
                    Appointment.appointment_date == tomorrow_str,
                    Appointment.status == "booked",
                )
            )
            return result.scalars().all()

    appointments = _run(_get_appointments())
    sent = 0
    for appt in appointments:
        send_appointment_reminder.delay(appt.id, appt.tenant_slug)
        sent += 1

    logger.info(
        "send_daily_reminders: queued %d reminders for %s",
        sent, tomorrow_str,
    )
    return {"reminders_queued": sent, "date": tomorrow_str}

