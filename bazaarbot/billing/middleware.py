"""Usage-enforcement middleware and FastAPI dependencies for BazaarBot billing.

This module provides:

  * ``get_tenant_subscription`` — look up the active Subscription row.
  * ``check_message_limit``     — (allowed, used, limit) for any tenant;
                                   free-trial tenants use a DB count.
  * ``increment_message_count`` — atomically bump message_count after success.
  * ``enforce_message_limit``   — raises HTTP 429 / 403 when limits are hit;
                                   call this at the top of every webhook handler.
  * ``check_llm_access``        — True for Business / Pro plans.
  * ``check_api_access``        — True for Pro plan only.
  * ``get_db``                  — FastAPI ``Depends``-compatible async DB session.
"""
import logging
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import Depends, HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bazaarbot.billing.plan_config import (
    check_api_allowed,
    check_channel_allowed,
    check_llm_allowed,
    FREE_TRIAL_MESSAGES,
)
from bazaarbot.config import Config
from bazaarbot.database_pg import AsyncSessionLocal
from bazaarbot.db.billing_models import Subscription

logger = logging.getLogger(__name__)


# ── FastAPI async-session dependency ──────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an ``AsyncSession`` for use with ``Depends(get_db)``.

    Commits on clean exit; rolls back on any exception.  This is the
    FastAPI-compatible counterpart to the ``asynccontextmanager`` version
    in ``database_pg``.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Subscription lookup ────────────────────────────────────────────────────

async def get_tenant_subscription(
    tenant_slug: str,
    db: AsyncSession,
) -> Subscription | None:
    """Return the *active* ``Subscription`` row for *tenant_slug*, or ``None``.

    A ``None`` result indicates the tenant is on the free trial (no paid plan).
    """
    result = await db.execute(
        select(Subscription).where(
            Subscription.tenant_slug == tenant_slug,
            Subscription.status == "active",
        )
    )
    return result.scalar_one_or_none()


# ── Message-limit checks ───────────────────────────────────────────────────

async def check_message_limit(
    tenant_slug: str,
    db: AsyncSession,
) -> tuple[bool, int, int]:
    """Check whether *tenant_slug* may send another message.

    Returns a ``(allowed, used, limit)`` triple:

    * **Free-trial** (no active subscription): counts all inbound messages for
      the current calendar month against the ``FREE_TRIAL_MESSAGES`` constant.
    * **Paid plan**: reads ``message_count`` and ``message_limit`` directly from
      the ``Subscription`` row.

    Args:
        tenant_slug: Slug of the tenant to check.
        db:          Open ``AsyncSession``.

    Returns:
        ``(True, used, limit)``  when the tenant is within quota.
        ``(False, used, limit)`` when the quota is exhausted.
    """
    from bazaarbot.models import Message  # avoid circular at module level

    sub = await get_tenant_subscription(tenant_slug, db)

    if sub is None:
        # Free-trial path: count inbound messages in the current UTC month.
        limit = FREE_TRIAL_MESSAGES
        now = datetime.now(timezone.utc)
        month_start = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        used: int = await db.scalar(
            select(func.count())
            .select_from(Message)
            .where(
                Message.tenant_slug == tenant_slug,
                Message.direction == "in",
                Message.created_at >= month_start,
            )
        ) or 0
        return used < limit, used, limit

    # Paid-plan path: trust the denormalised counter maintained by
    # increment_message_count() for speed; avoid a full table scan.
    allowed = sub.message_count < sub.message_limit
    return allowed, sub.message_count, sub.message_limit


# ── Message-count increment ────────────────────────────────────────────────

async def increment_message_count(
    tenant_slug: str,
    db: AsyncSession,
) -> None:
    """Atomically increment ``message_count`` on the tenant's active subscription.

    No-op when the tenant is on the free trial (no ``Subscription`` row).
    Call this *after* a message has been successfully processed and persisted.

    Args:
        tenant_slug: Slug of the tenant whose counter to bump.
        db:          Open ``AsyncSession`` (caller is responsible for commit).
    """
    await db.execute(
        update(Subscription)
        .where(
            Subscription.tenant_slug == tenant_slug,
            Subscription.status == "active",
        )
        .values(message_count=Subscription.message_count + 1)
    )


# ── Full pre-processing enforcement ───────────────────────────────────────

async def enforce_message_limit(
    tenant_slug: str,
    channel: str,
    db: AsyncSession,
) -> None:
    """Enforce message-count and channel-access limits before processing.

    Raises:
        ``HTTPException(429)`` — monthly message quota exhausted.
        ``HTTPException(403)`` — channel not included in the tenant's plan.

    Should be awaited at the start of every inbound-message webhook handler.

    Args:
        tenant_slug: Slug of the receiving tenant.
        channel:     Inbound channel identifier (e.g. ``"whatsapp"``).
        db:          Open ``AsyncSession``.
    """
    # ── 1. Message-count gate ─────────────────────────────────────────────
    allowed, used, limit = await check_message_limit(tenant_slug, db)
    if not allowed:
        logger.warning(
            "message_limit_exceeded tenant=%s used=%d limit=%d",
            tenant_slug,
            used,
            limit,
        )
        raise HTTPException(
            status_code=429,
            detail={
                "error": "message_limit_exceeded",
                "message": (
                    f"Aapka {limit} messages ka monthly quota khatam ho gaya. "
                    f"Plan upgrade ke liye: {Config.FRONTEND_URL}/billing"
                ),
                "used": used,
                "limit": limit,
                "upgrade_url": f"{Config.FRONTEND_URL}/billing",
            },
        )

    # ── 2. Channel-access gate ────────────────────────────────────────────
    sub = await get_tenant_subscription(tenant_slug, db)
    plan_id = sub.plan if sub else "starter"

    if not check_channel_allowed(plan_id, channel):
        logger.warning(
            "channel_not_allowed tenant=%s plan=%s channel=%s",
            tenant_slug,
            plan_id,
            channel,
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "channel_not_allowed",
                "message": (
                    f"Aapke {plan_id} plan mein {channel} channel shamil nahi. "
                    f"Business ya Pro plan lein."
                ),
                "current_plan": plan_id,
                "upgrade_url": f"{Config.FRONTEND_URL}/billing",
            },
        )


# ── Feature-flag helpers ───────────────────────────────────────────────────

async def check_llm_access(
    tenant_slug: str,
    db: AsyncSession,
) -> bool:
    """Return ``True`` when the tenant's plan permits LLM-powered replies.

    Free-trial and Starter tenants always return ``False``.  Business and Pro
    tenants return ``True``.

    Args:
        tenant_slug: Slug of the tenant to check.
        db:          Open ``AsyncSession``.
    """
    sub = await get_tenant_subscription(tenant_slug, db)
    if sub is None:
        return False
    return check_llm_allowed(sub.plan)


async def check_api_access(
    tenant_slug: str,
    db: AsyncSession,
) -> bool:
    """Return ``True`` when the tenant's plan permits REST API access.

    Only the Pro plan carries this flag.

    Args:
        tenant_slug: Slug of the tenant to check.
        db:          Open ``AsyncSession``.
    """
    sub = await get_tenant_subscription(tenant_slug, db)
    if sub is None:
        return False
    return check_api_allowed(sub.plan)
