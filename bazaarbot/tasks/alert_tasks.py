"""Async low-stock alert tasks for BazaarBot.

Low-stock checks scan the full inventory table and can be slow on large
catalogs, so they run in the Celery 'alerts' queue instead of blocking
the webhook.
"""
import logging

from bazaarbot.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(
    name="bazaarbot.tasks.alert_tasks.check_low_stock",
)
def check_low_stock(tenant_slug: str) -> dict:
    """Scan inventory for a single tenant and send a low-stock alert email.

    Queries all products whose current quantity is at or below their
    reorder level, then delegates to
    :func:`~bazaarbot.tasks.email_tasks.send_low_stock_alert_email`.

    Returns the list of low-stock items found (may be empty).
    """
    from bazaarbot.database_pg import get_low_stock
    from bazaarbot.tasks.email_tasks import send_low_stock_alert_email

    low_items = get_low_stock(tenant_slug)
    logger.info(
        "check_low_stock: tenant=%s found %d low-stock items",
        tenant_slug,
        len(low_items),
    )

    if low_items:
        send_low_stock_alert_email.delay(
            tenant_slug=tenant_slug,
            low_stock_items=low_items,
        )

    return {"tenant_slug": tenant_slug, "low_stock_count": len(low_items), "items": low_items}


@celery.task(
    name="bazaarbot.tasks.alert_tasks.check_all_low_stock",
)
def check_all_low_stock() -> dict:
    """Run a low-stock check for every active tenant.

    Scheduled daily at 09:00 PKT by Celery Beat.  Iterates all tenants
    and dispatches a :func:`check_low_stock` sub-task for each one so
    that individual failures are isolated.

    Returns the number of tenants checked.
    """
    from bazaarbot.database_pg import list_tenants

    tenants = list_tenants()
    active = [t for t in tenants if t.get("is_active", True)]

    for tenant in active:
        check_low_stock.delay(tenant["slug"])

    logger.info("check_all_low_stock: dispatched checks for %d tenants", len(active))
    return {"success": True, "tenants_checked": len(active)}
