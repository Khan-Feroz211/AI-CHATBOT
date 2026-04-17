"""Async order-processing tasks for BazaarBot.

Heavy order operations (product validation, DB writes, stock updates,
and customer notifications) run in the Celery 'orders' queue so the
webhook handler returns instantly without blocking on any I/O.
"""
import logging
from datetime import datetime, timedelta, timezone

from bazaarbot.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    name="bazaarbot.tasks.order_tasks.process_order",
)
def process_order(
    self,
    tenant_slug: str,
    phone: str,
    product_name: str,
    quantity: int,
    payment_method: str = "pending",
) -> dict:
    """Process a new order asynchronously.

    Steps:
    1. Fetch the product from inventory and validate it exists.
    2. Validate that enough stock is available.
    3. Create the order record in the database (which also deducts stock).
    4. If the post-sale quantity drops at or below the reorder level,
       enqueue a :func:`~bazaarbot.tasks.alert_tasks.check_low_stock` task.
    5. Enqueue a confirmation email via
       :func:`~bazaarbot.tasks.email_tasks.send_order_confirmation`.
    6. Return the order reference, numeric order ID, and total.

    On failure the task retries up to 2 times with a 30-second delay.
    """
    try:
        from bazaarbot.database_pg import create_order, get_product
        from bazaarbot.tasks.email_tasks import send_order_confirmation

        # Step 1 & 2 — validate product and stock
        product = get_product(tenant_slug, product_name)
        if not product:
            logger.warning(
                "process_order: product '%s' not found (tenant=%s)",
                product_name, tenant_slug,
            )
            return {"success": False, "error": "product_not_found"}

        if product["quantity"] < quantity:
            logger.warning(
                "process_order: insufficient stock for '%s' "
                "(available=%d, requested=%d, tenant=%s)",
                product_name, product["quantity"], quantity, tenant_slug,
            )
            return {
                "success": False,
                "error": "insufficient_stock",
                "available": product["quantity"],
            }

        unit_price = float(product["sell_price"])

        # Step 3 — create order record + deduct stock (handled inside create_order)
        order_ref, total = create_order(
            tenant_slug, phone, product_name, quantity, unit_price, payment_method
        )
        logger.info(
            "Order created: ref=%s total=%.2f tenant=%s",
            order_ref, total, tenant_slug,
        )

        # Step 4 — check if post-sale quantity triggers a low-stock alert
        new_qty = product["quantity"] - quantity
        reorder_level = int(product.get("reorder_level") or 0)
        if reorder_level > 0 and new_qty <= reorder_level:
            from bazaarbot.tasks.alert_tasks import check_low_stock
            check_low_stock.delay(tenant_slug)
            logger.info(
                "process_order: low-stock check enqueued for tenant=%s "
                "(product='%s' new_qty=%d reorder_level=%d)",
                tenant_slug, product_name, new_qty, reorder_level,
            )

        # Step 5 — parse numeric order ID for the confirmation email
        # order_ref format: "ORD-<6-char-hex>" — parse last segment as base-16 int
        try:
            order_id = int(order_ref.split("-")[-1], 16)
        except (ValueError, IndexError):
            logger.error(
                "process_order: cannot parse order ID from ref '%s' (tenant=%s); "
                "skipping confirmation email.",
                order_ref, tenant_slug,
            )
            return {"success": True, "order_ref": order_ref, "total": total}

        send_order_confirmation.delay(order_id=order_id, tenant_slug=tenant_slug)

        return {
            "success": True,
            "order_ref": order_ref,
            "order_id": order_id,
            "total": total,
        }

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
            new_status, order_ref,
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
            order_ref, new_status, tenant_slug,
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
    from sqlalchemy import delete
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
        logger.info(
            "cleanup_old_sessions: deleted %d rows older than %d days",
            deleted, days_old,
        )
        return {"success": True, "deleted": deleted, "days_old": days_old}
    except Exception as exc:
        logger.error("cleanup_old_sessions failed: %s", exc)
        return {"success": False, "error": str(exc)}

