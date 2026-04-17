"""Async email tasks for BazaarBot.

All email sending is offloaded to the Celery 'email' queue so that
webhook handlers return immediately without blocking on SMTP.
"""
import logging

from bazaarbot.celery_app import celery
from bazaarbot.channels.email_channel import send_email

logger = logging.getLogger(__name__)


@celery.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="bazaarbot.tasks.email_tasks.send_notification_email",
)
def send_notification_email(
    self,
    to_email: str,
    subject: str,
    body: str,
    tenant_slug: str,
) -> dict:
    """Send a notification email asynchronously.

    Retries up to 3 times on failure with a 60-second delay between
    attempts.  Returns ``{"success": True, "to": to_email}`` on
    success.
    """
    try:
        send_email(to=to_email, subject=subject, body=body)
        logger.info("Email sent to %s for tenant %s", to_email, tenant_slug)
        return {"success": True, "to": to_email}
    except Exception as exc:
        logger.error("Email failed for %s (tenant=%s): %s", to_email, tenant_slug, exc)
        raise self.retry(exc=exc)


@celery.task(
    name="bazaarbot.tasks.email_tasks.send_order_confirmation",
)
def send_order_confirmation(
    order_id: int,
    tenant_slug: str,
) -> dict:
    """Send an order confirmation email to the business owner.

    Fetches tenant details from the database, composes a bilingual
    Urdu-English email body, then dispatches it via
    :func:`send_notification_email`.

    Returns ``{"success": False, "reason": "no_notify_email"}`` when the
    tenant has no notification email configured.
    """
    from bazaarbot.database_pg import get_tenant

    tenant = get_tenant(tenant_slug)
    if not tenant or not tenant.get("notify_email"):
        logger.warning(
            "send_order_confirmation: no notify_email for tenant %s", tenant_slug
        )
        return {"success": False, "reason": "no_notify_email"}

    email_body = (
        f"Order Confirmation \u2014 {tenant['name']}\n\n"
        f"Aapka order confirm ho gaya hai.\n"
        f"Order ID: {order_id}\n\n"
        f"Shukriya apna trust karne ke liye!\n"
        f"{tenant['name']} Team"
    )

    send_notification_email.delay(
        to_email=tenant["notify_email"],
        subject=f"New Order \u2014 {tenant['name']}",
        body=email_body,
        tenant_slug=tenant_slug,
    )
    logger.info("Order confirmation queued for order_id=%s tenant=%s", order_id, tenant_slug)
    return {"success": True, "order_id": order_id}


@celery.task(
    name="bazaarbot.tasks.email_tasks.send_low_stock_alert_email",
)
def send_low_stock_alert_email(
    tenant_slug: str,
    low_stock_items: list,
) -> dict:
    """Send a low-stock alert email to the business owner.

    No email is sent when *low_stock_items* is empty or the tenant has no
    notification email configured.  Returns a dict indicating success and
    how many items were reported.
    """
    if not low_stock_items:
        return {"success": False, "reason": "no_low_stock_items"}

    from bazaarbot.database_pg import get_tenant

    tenant = get_tenant(tenant_slug)
    if not tenant or not tenant.get("notify_email"):
        logger.warning(
            "send_low_stock_alert_email: no notify_email for tenant %s", tenant_slug
        )
        return {"success": False, "reason": "no_notify_email"}

    items_text = "\n".join(
        f"  - {item['product_name']}: {item['quantity']} {item['unit']} baki hai "
        f"(reorder level: {item['reorder_level']})"
        for item in low_stock_items
    )

    body = (
        f"Low Stock Alert \u2014 {tenant['name']}\n\n"
        f"Yeh products kam ho rahe hain:\n\n"
        f"{items_text}\n\n"
        f"Abhi order karein taake stock khatam na ho."
    )

    send_notification_email.delay(
        to_email=tenant["notify_email"],
        subject=f"Low Stock Alert \u2014 {tenant['name']}",
        body=body,
        tenant_slug=tenant_slug,
    )
    logger.info(
        "Low stock alert queued for tenant %s (%d items)",
        tenant_slug,
        len(low_stock_items),
    )
    return {"success": True, "items_count": len(low_stock_items)}
