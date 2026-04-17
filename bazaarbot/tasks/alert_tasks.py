"""Async low-stock and WhatsApp alert tasks for BazaarBot.

Low-stock checks scan the full inventory table and can be slow on large
catalogs, so they run in the Celery 'alerts' queue instead of blocking
the webhook.  WhatsApp outbound messages are also handled here so that
Twilio API latency never affects webhook response time.
"""
import logging

from bazaarbot.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(
    name="bazaarbot.tasks.alert_tasks.check_low_stock",
)
def check_low_stock(tenant_slug: str | None = None) -> dict:
    """Check inventory for low-stock items and send alert emails.

    If *tenant_slug* is provided, only that tenant is checked.
    If ``None``, **all active tenants** are checked (used by the Beat
    schedule as a daily sweep).

    A product is considered low-stock when::

        quantity <= reorder_level  (and reorder_level > 0)

    An alert email is dispatched for each tenant that has at least one
    low-stock item.  Returns the number of tenants checked and alerts sent.
    """
    from bazaarbot.database_pg import get_inventory

    if tenant_slug is not None:
        slugs = [tenant_slug]
    else:
        # Fetch all active tenant slugs directly via async layer
        from bazaarbot.database_pg import _run, AsyncSessionLocal
        from bazaarbot.models import Tenant
        from sqlalchemy import select

        async def _get_active_slugs() -> list[str]:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Tenant.slug).where(Tenant.is_active.is_(True))
                )
                return [row[0] for row in result.fetchall()]

        slugs = _run(_get_active_slugs())

    alerts_sent = 0
    for slug in slugs:
        inventory = get_inventory(slug)
        low_items = [
            item for item in inventory
            if int(item.get("reorder_level") or 0) > 0
            and item["quantity"] <= int(item.get("reorder_level") or 0)
        ]

        if low_items:
            from bazaarbot.tasks.email_tasks import send_low_stock_alert_email
            send_low_stock_alert_email.delay(
                tenant_slug=slug,
                low_stock_items=low_items,
            )
            alerts_sent += 1
            logger.info(
                "check_low_stock: alert queued for tenant=%s (%d items)",
                slug, len(low_items),
            )
        else:
            logger.debug("check_low_stock: tenant=%s — no low-stock items", slug)

    return {"slugs_checked": len(slugs), "alerts_sent": alerts_sent}


@celery.task(
    name="bazaarbot.tasks.alert_tasks.check_all_low_stock",
)
def check_all_low_stock() -> dict:
    """Beat task alias: run a low-stock check across all active tenants.

    Delegates to :func:`check_low_stock` with ``tenant_slug=None``.
    Scheduled daily at 09:00 PKT by Celery Beat.
    """
    return check_low_stock(tenant_slug=None)


@celery.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="bazaarbot.tasks.alert_tasks.send_whatsapp_alert",
)
def send_whatsapp_alert(
    self,
    to_number: str,
    message: str,
    tenant_slug: str,
) -> dict:
    """Send a WhatsApp message asynchronously via Twilio.

    Used for order confirmations, appointment reminders, and other
    customer-facing alerts.  Wraps the existing
    :func:`~bazaarbot.channels.whatsapp.send_whatsapp` helper.

    Retries up to 3 times (30-second delay) on transient Twilio errors.
    Returns ``{"success": bool, "to": to_number}``.
    """
    try:
        from bazaarbot.channels.whatsapp import send_whatsapp
        send_whatsapp(to_number, message)
        logger.info(
            "send_whatsapp_alert: message sent to %s (tenant=%s)",
            to_number, tenant_slug,
        )
        return {"success": True, "to": to_number}
    except Exception as exc:
        logger.error(
            "send_whatsapp_alert: failed for %s (tenant=%s): %s",
            to_number, tenant_slug, exc,
        )
        raise self.retry(exc=exc)

