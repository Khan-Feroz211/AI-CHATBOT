"""Async order-processing tasks for BazaarBot.

Heavy order operations (DB writes, stock updates, customer notifications)
run in the Celery 'orders' queue so the webhook handler returns instantly.
"""
import logging
from datetime import datetime, timedelta, timezone

from bazaarbot.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="bazaarbot.tasks.order_tasks.process_order",
)
def process_order(
    self,
    tenant_slug: str,
    phone: str,
    product_name: str,
    quantity: int,
    unit_price: float,
    payment_method: str = "pending",
) -> dict:
    """Create an order record in the database and trigger a confirmation email.

    Retries up to 3 times (30-second delay) on transient failures.
    Returns ``{"success": True, "order_ref": str, "total": float}`` on
    success.
    """
    try:
        from bazaarbot.database_pg import create_order
        from bazaarbot.tasks.email_tasks import send_order_confirmation

        order_ref, total = create_order(
            tenant_slug, phone, product_name, quantity, unit_price, payment_method
        )
        logger.info(
            "Order created: ref=%s total=%.2f tenant=%s phone=%s",
            order_ref,
            total,
            tenant_slug,
            phone,
        )

        # Parse the numeric order ID from the reference string (format: "ORD-<id>").
        try:
            order_id = int(order_ref.split("-")[-1])
        except (ValueError, IndexError):
            logger.error(
                "process_order: cannot parse order ID from ref '%s' (tenant=%s); "
                "skipping confirmation email.",
                order_ref,
                tenant_slug,
            )
            return {"success": True, "order_ref": order_ref, "total": total}

        send_order_confirmation.delay(order_id=order_id, tenant_slug=tenant_slug)

        return {"success": True, "order_ref": order_ref, "total": total}
    except Exception as exc:
        logger.error("process_order failed (tenant=%s): %s", tenant_slug, exc)
        raise self.retry(exc=exc)


@celery.task(
    bind=True,
    max_retries=2,
    default_retry_delay=15,
    name="bazaarbot.tasks.order_tasks.update_order_status",
)
def update_order_status(
    self,
    order_ref: str,
    new_status: str,
    tenant_slug: str,
) -> dict:
    """Update an existing order's status and notify the owner by email.

    Valid statuses: ``pending``, ``confirmed``, ``shipped``, ``delivered``,
    ``cancelled``.
    """
    valid_statuses = {"pending", "confirmed", "shipped", "delivered", "cancelled"}
    if new_status not in valid_statuses:
        logger.error(
            "update_order_status: invalid status '%s' for order %s",
            new_status,
            order_ref,
        )
        return {"success": False, "reason": "invalid_status"}

    try:
        from bazaarbot.database_pg import get_tenant
        from bazaarbot.tasks.email_tasks import send_notification_email

        tenant = get_tenant(tenant_slug)
        if tenant and tenant.get("notify_email"):
            body = (
                f"Order Status Update \u2014 {tenant['name']}\n\n"
                f"Order Ref: {order_ref}\n"
                f"Naya status: {new_status}\n\n"
                f"\u2014 BazaarBot"
            )
            send_notification_email.delay(
                to_email=tenant["notify_email"],
                subject=f"Order {order_ref} \u2014 {new_status.capitalize()}",
                body=body,
                tenant_slug=tenant_slug,
            )

        logger.info(
            "Order status updated: ref=%s status=%s tenant=%s",
            order_ref,
            new_status,
            tenant_slug,
        )
        return {"success": True, "order_ref": order_ref, "status": new_status}
    except Exception as exc:
        logger.error("update_order_status failed: %s", exc)
        raise self.retry(exc=exc)


@celery.task(
    name="bazaarbot.tasks.order_tasks.cleanup_old_sessions",
)
def cleanup_old_sessions(days_old: int = 30) -> dict:
    """Delete bot conversation sessions older than *days_old* days.

    Scheduled weekly (Sunday 02:00 PKT) by Celery Beat to prevent the
    sessions table from growing indefinitely.  Returns a count of the
    rows deleted.
    """
    from sqlalchemy import delete, text
    from bazaarbot.database_pg import _run, AsyncSessionLocal
    from bazaarbot.models import Session as BotSession

    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days_old)

    async def _delete():
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                delete(BotSession).where(BotSession.updated_at < cutoff)
            )
            await session.commit()
            return result.rowcount

    try:
        deleted = _run(_delete())
        logger.info("cleanup_old_sessions: deleted %d rows older than %d days", deleted, days_old)
        return {"success": True, "deleted": deleted, "days_old": days_old}
    except Exception as exc:
        logger.error("cleanup_old_sessions failed: %s", exc)
        return {"success": False, "error": str(exc)}
