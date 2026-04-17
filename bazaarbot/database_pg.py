"""Async PostgreSQL persistence layer for BazaarBot (Day 2+).

Uses SQLAlchemy 2.x async + asyncpg.  All public async functions have a
matching sync shim so existing bot/ handlers that import database.py can
be migrated incrementally without being touched.

Sync shims use asyncio.run() which is safe to call from any non-async
context (CLI, Celery workers, legacy Flask views).  They will raise
RuntimeError if called from inside a running event loop — use the
async_ prefixed functions directly in FastAPI route handlers instead.
"""
import asyncio
import secrets
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from typing import AsyncGenerator

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bazaarbot.config import config
from bazaarbot.models import (
    Appointment,
    Base,
    Inventory,
    KnowledgeDoc,
    Message,
    Order,
    Session as BotSession,
    Tenant,
    User,
)

# ── Engine & session factory ──────────────────────────────────────────────

engine = create_async_engine(
    config.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=config.DATABASE_POOL_SIZE,
    max_overflow=20,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Session context manager ───────────────────────────────────────────────

@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession with automatic commit / rollback."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Startup ───────────────────────────────────────────────────────────────

async def init_db() -> None:
    """Create all tables and seed the default tenant.  Called at startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _seed_default_tenant()
    await _seed_demo_inventory()


async def _seed_default_tenant() -> None:
    async with get_db() as session:
        existing = await session.scalar(
            select(Tenant).where(Tenant.slug == "default")
        )
        if not existing:
            session.add(
                Tenant(
                    slug="default",
                    name="BazaarBot Demo",
                    city="Karachi",
                    business_type="retail",
                )
            )


async def _seed_demo_inventory() -> None:
    demo_products = [
        ("Basmati Chawal",  "food",        500,  "kg",      150.0, 180.0, 50,  "Kohinoor Mills"),
        ("Atta (Flour)",    "food",        300,  "kg",      55.0,  70.0,  100, "National Foods"),
        ("Cooking Oil",     "food",        200,  "litre",   380.0, 420.0, 30,  "Dalda Foods"),
        ("Sugar (Cheeni)",  "food",        400,  "kg",      120.0, 140.0, 80,  "Al-Abbas Sugar"),
        ("Daal Mash",       "food",        150,  "kg",      220.0, 260.0, 20,  "Local Market"),
        ("Surf Excel 1kg",  "household",   250,  "box",     320.0, 380.0, 40,  "Unilever"),
        ("Mobile Recharge", "telecom",    1000,  "pieces",  95.0,  100.0, 200, "Jazz/Zong"),
        ("LED Bulb 18W",    "electronics",  80,  "pieces",  180.0, 250.0, 10,  "Local Wholesale"),
        ("Cotton Kameez",   "clothing",     60,  "pieces",  400.0, 600.0,  5,  "Faisalabad Market"),
        ("Panadol Strip",   "medicine",    500,  "strip",   25.0,  35.0,  100, "GSK Pakistan"),
    ]
    async with get_db() as session:
        count = await session.scalar(
            select(func.count()).select_from(Inventory).where(
                Inventory.tenant_slug == "default"
            )
        )
        if count and count > 0:
            return
        for name, cat, qty, unit, buy, sell, reorder, supplier in demo_products:
            session.add(
                Inventory(
                    tenant_slug="default",
                    product_name=name,
                    category=cat,
                    quantity=qty,
                    unit=unit,
                    buy_price=buy,
                    sell_price=sell,
                    reorder_level=reorder,
                    supplier=supplier,
                )
            )


# ── Tenant ────────────────────────────────────────────────────────────────

async def async_get_tenant(slug: str) -> dict | None:
    async with get_db() as session:
        row = await session.scalar(select(Tenant).where(Tenant.slug == slug))
        return row.to_dict() if row else None


async def async_list_tenants() -> list[dict]:
    async with get_db() as session:
        result = await session.scalars(select(Tenant).order_by(Tenant.id))
        return [t.to_dict() for t in result.all()]


async def async_create_tenant(
    slug: str,
    name: str,
    city: str = "Karachi",
    business_type: str = "retail",
    owner_phone: str = "",
    owner_email: str = "",
) -> None:
    async with get_db() as session:
        existing = await session.scalar(select(Tenant).where(Tenant.slug == slug))
        if not existing:
            session.add(
                Tenant(
                    slug=slug,
                    name=name,
                    city=city,
                    business_type=business_type,
                    owner_phone=owner_phone,
                    owner_email=owner_email,
                )
            )


async def async_update_tenant(slug: str, data: dict) -> None:
    allowed = {
        "name", "city", "business_type", "owner_phone", "owner_email",
        "easypaisa_number", "jazzcash_number", "bank_title", "bank_iban",
        "notify_email", "plan", "is_active",
    }
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return
    async with get_db() as session:
        await session.execute(
            update(Tenant).where(Tenant.slug == slug).values(**updates)
        )


# ── Session (bot conversation state) ─────────────────────────────────────

async def async_get_session(tenant_slug: str, phone: str) -> dict:
    async with get_db() as session:
        row = await session.scalar(
            select(BotSession).where(
                BotSession.tenant_slug == tenant_slug,
                BotSession.phone == phone,
            )
        )
        if row:
            return {"state": row.state, "context": row.context or {}}
    return {"state": "idle", "context": {}}


async def async_set_session(
    tenant_slug: str, phone: str, state: str, context: dict | None = None
) -> None:
    ctx = context or {}
    now = datetime.now(timezone.utc)
    async with get_db() as session:
        row = await session.scalar(
            select(BotSession).where(
                BotSession.tenant_slug == tenant_slug,
                BotSession.phone == phone,
            )
        )
        if row:
            row.state = state
            row.context = ctx
            row.updated_at = now
        else:
            session.add(
                BotSession(
                    tenant_slug=tenant_slug,
                    phone=phone,
                    state=state,
                    context=ctx,
                    updated_at=now,
                )
            )


async def async_clear_session(tenant_slug: str, phone: str) -> None:
    await async_set_session(tenant_slug, phone, "idle", {})


# ── Messages ──────────────────────────────────────────────────────────────

async def async_log_message(
    tenant_slug: str,
    phone: str,
    direction: str,
    content: str,
    intent: str | None = None,
    channel: str = "whatsapp",
) -> None:
    async with get_db() as session:
        session.add(
            Message(
                tenant_slug=tenant_slug,
                phone=phone,
                direction=direction,
                content=content,
                intent=intent,
                channel=channel,
            )
        )


async def async_get_recent_messages(tenant_slug: str, limit: int = 30) -> list[dict]:
    async with get_db() as session:
        result = await session.scalars(
            select(Message)
            .where(Message.tenant_slug == tenant_slug)
            .order_by(Message.id.desc())
            .limit(limit)
        )
        return [m.to_dict() for m in result.all()]


# ── Inventory ─────────────────────────────────────────────────────────────

async def async_get_inventory(tenant_slug: str) -> list[dict]:
    async with get_db() as session:
        result = await session.scalars(
            select(Inventory)
            .where(Inventory.tenant_slug == tenant_slug)
            .order_by(Inventory.product_name)
        )
        return [i.to_dict() for i in result.all()]


async def async_get_product(tenant_slug: str, name: str) -> dict | None:
    async with get_db() as session:
        row = await session.scalar(
            select(Inventory).where(
                Inventory.tenant_slug == tenant_slug,
                func.lower(Inventory.product_name) == name.lower(),
            )
        )
        return row.to_dict() if row else None


async def async_upsert_product(
    tenant_slug: str,
    product_name: str,
    category: str = "general",
    quantity: int = 0,
    unit: str = "pieces",
    buy_price: float = 0.0,
    sell_price: float = 0.0,
    reorder_level: int = 10,
    supplier: str = "",
) -> None:
    now = datetime.now(timezone.utc)
    async with get_db() as session:
        row = await session.scalar(
            select(Inventory).where(
                Inventory.tenant_slug == tenant_slug,
                func.lower(Inventory.product_name) == product_name.lower(),
            )
        )
        if row:
            row.category = category
            row.quantity = quantity
            row.unit = unit
            row.buy_price = buy_price
            row.sell_price = sell_price
            row.reorder_level = reorder_level
            row.supplier = supplier
            row.updated_at = now
        else:
            session.add(
                Inventory(
                    tenant_slug=tenant_slug,
                    product_name=product_name,
                    category=category,
                    quantity=quantity,
                    unit=unit,
                    buy_price=buy_price,
                    sell_price=sell_price,
                    reorder_level=reorder_level,
                    supplier=supplier,
                    updated_at=now,
                )
            )


async def async_update_stock(
    tenant_slug: str, product_name: str, delta: int
) -> None:
    now = datetime.now(timezone.utc)
    async with get_db() as session:
        row = await session.scalar(
            select(Inventory).where(
                Inventory.tenant_slug == tenant_slug,
                func.lower(Inventory.product_name) == product_name.lower(),
            )
        )
        if row:
            row.quantity = max(0, row.quantity + delta)
            row.updated_at = now


async def async_get_low_stock(tenant_slug: str) -> list[dict]:
    async with get_db() as session:
        result = await session.scalars(
            select(Inventory).where(
                Inventory.tenant_slug == tenant_slug,
                Inventory.quantity <= Inventory.reorder_level,
            ).order_by(Inventory.quantity)
        )
        return [i.to_dict() for i in result.all()]


# ── Orders ────────────────────────────────────────────────────────────────

async def async_create_order(
    tenant_slug: str,
    phone: str,
    product_name: str,
    quantity: int,
    unit_price: float,
    payment_method: str = "pending",
) -> tuple[str, float]:
    total = round(quantity * unit_price, 2)
    ref = "ORD-" + secrets.token_hex(3).upper()
    async with get_db() as session:
        session.add(
            Order(
                tenant_slug=tenant_slug,
                phone=phone,
                order_ref=ref,
                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price,
                total=total,
                payment_method=payment_method,
            )
        )
    await async_update_stock(tenant_slug, product_name, -quantity)
    return ref, total


async def async_get_orders(
    tenant_slug: str, phone: str | None = None, limit: int = 10
) -> list[dict]:
    async with get_db() as session:
        q = (
            select(Order)
            .where(Order.tenant_slug == tenant_slug)
            .order_by(Order.id.desc())
            .limit(limit)
        )
        if phone:
            q = q.where(Order.phone == phone)
        result = await session.scalars(q)
        return [o.to_dict() for o in result.all()]


# ── Appointments ──────────────────────────────────────────────────────────

async def async_book_appointment(
    tenant_slug: str,
    phone: str,
    customer_name: str,
    apt_date: str,
    apt_time: str,
    purpose: str = "",
    notes: str = "",
) -> int | None:
    async with get_db() as session:
        apt = Appointment(
            tenant_slug=tenant_slug,
            phone=phone,
            customer_name=customer_name,
            appointment_date=apt_date,
            appointment_time=apt_time,
            purpose=purpose,
            notes=notes,
        )
        session.add(apt)
        await session.flush()
        return apt.id


async def async_get_appointments(
    tenant_slug: str,
    phone: str | None = None,
    upcoming_only: bool = True,
    limit: int = 10,
) -> list[dict]:
    today = date.today().isoformat()
    async with get_db() as session:
        q = (
            select(Appointment)
            .where(Appointment.tenant_slug == tenant_slug)
            .order_by(Appointment.appointment_date, Appointment.appointment_time)
            .limit(limit)
        )
        if phone:
            q = q.where(Appointment.phone == phone)
        if upcoming_only:
            q = q.where(Appointment.appointment_date >= today)
        result = await session.scalars(q)
        return [a.to_dict() for a in result.all()]


async def async_cancel_appointment(apt_id: int, tenant_slug: str) -> None:
    async with get_db() as session:
        await session.execute(
            update(Appointment)
            .where(Appointment.id == apt_id, Appointment.tenant_slug == tenant_slug)
            .values(status="cancelled")
        )


# ── Knowledge docs ────────────────────────────────────────────────────────

async def async_get_knowledge_docs(tenant_slug: str) -> list[dict]:
    async with get_db() as session:
        result = await session.scalars(
            select(KnowledgeDoc).where(KnowledgeDoc.tenant_slug == tenant_slug)
        )
        return [d.to_dict() for d in result.all()]


async def async_upsert_knowledge_doc(
    tenant_slug: str, title: str, content: str, tags: str = ""
) -> None:
    now = datetime.now(timezone.utc)
    async with get_db() as session:
        row = await session.scalar(
            select(KnowledgeDoc).where(
                KnowledgeDoc.tenant_slug == tenant_slug,
                KnowledgeDoc.title == title,
            )
        )
        if row:
            row.content = content
            row.tags = tags
            row.updated_at = now
        else:
            session.add(
                KnowledgeDoc(
                    tenant_slug=tenant_slug,
                    title=title,
                    content=content,
                    tags=tags,
                    updated_at=now,
                )
            )


async def async_delete_knowledge_doc(doc_id: int, tenant_slug: str) -> None:
    async with get_db() as session:
        await session.execute(
            delete(KnowledgeDoc).where(
                KnowledgeDoc.id == doc_id,
                KnowledgeDoc.tenant_slug == tenant_slug,
            )
        )


# ── Analytics ─────────────────────────────────────────────────────────────

async def async_get_analytics(tenant_slug: str) -> dict:
    today = date.today().isoformat()
    async with get_db() as session:
        total_msgs = await session.scalar(
            select(func.count()).select_from(Message).where(
                Message.tenant_slug == tenant_slug
            )
        ) or 0

        today_msgs = await session.scalar(
            select(func.count()).select_from(Message).where(
                Message.tenant_slug == tenant_slug,
                func.date(Message.created_at) == today,
            )
        ) or 0

        order_stats = await session.execute(
            select(
                func.count().label("cnt"),
                func.coalesce(func.sum(Order.total), 0).label("rev"),
            ).where(Order.tenant_slug == tenant_slug)
        )
        orow = order_stats.first()
        total_orders = orow.cnt if orow else 0
        total_revenue = float(orow.rev) if orow else 0.0

        upcoming_apts = await session.scalar(
            select(func.count()).select_from(Appointment).where(
                Appointment.tenant_slug == tenant_slug,
                Appointment.appointment_date >= today,
                Appointment.status == "booked",
            )
        ) or 0

        low_stock_count = await session.scalar(
            select(func.count()).select_from(Inventory).where(
                Inventory.tenant_slug == tenant_slug,
                Inventory.quantity <= Inventory.reorder_level,
            )
        ) or 0

        intent_rows = await session.execute(
            select(Message.intent, func.count().label("c"))
            .where(
                Message.tenant_slug == tenant_slug,
                Message.intent.isnot(None),
            )
            .group_by(Message.intent)
            .order_by(func.count().desc())
            .limit(6)
        )
        top_intents = {row.intent: row.c for row in intent_rows}

    return {
        "total_messages": total_msgs,
        "today_messages": today_msgs,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "upcoming_appointments": upcoming_apts,
        "low_stock_items": low_stock_count,
        "top_intents": top_intents,
    }


# ── Users ─────────────────────────────────────────────────────────────────

async def async_get_user(tenant_slug: str, phone: str) -> dict | None:
    async with get_db() as session:
        row = await session.scalar(
            select(User).where(
                User.tenant_slug == tenant_slug,
                User.phone == phone,
            )
        )
        return row.to_dict() if row else None


async def async_upsert_user(
    tenant_slug: str,
    phone: str,
    name: str | None = None,
    city: str | None = None,
    role: str = "customer",
) -> None:
    async with get_db() as session:
        row = await session.scalar(
            select(User).where(
                User.tenant_slug == tenant_slug,
                User.phone == phone,
            )
        )
        if row:
            if name is not None:
                row.name = name
            if city is not None:
                row.city = city
            row.role = role
        else:
            session.add(
                User(
                    tenant_slug=tenant_slug,
                    phone=phone,
                    name=name,
                    city=city,
                    role=role,
                )
            )


# ═══════════════════════════════════════════════════════════════════════════
# Sync shim layer
#
# These functions mirror the public API of bazaarbot/database.py exactly so
# that existing callers (bot/, channels/) can be migrated one file at a
# time.  They must only be called from a non-async context.
# ═══════════════════════════════════════════════════════════════════════════

def _run(coro):
    """Run an async coroutine synchronously.

    Raises RuntimeError if called from inside a running event loop.
    In that case, use the async_ prefixed function directly.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None and loop.is_running():
        raise RuntimeError(
            "database_pg sync shims cannot be called from inside a running "
            "event loop. Use the async_ prefixed function directly in async "
            "contexts (e.g. FastAPI route handlers)."
        )
    return asyncio.run(coro)


def get_tenant(slug: str) -> dict | None:
    return _run(async_get_tenant(slug))


def list_tenants() -> list[dict]:
    return _run(async_list_tenants())


def create_tenant(
    slug: str,
    name: str,
    city: str = "Karachi",
    business_type: str = "retail",
    owner_phone: str = "",
    owner_email: str = "",
) -> None:
    _run(async_create_tenant(slug, name, city, business_type, owner_phone, owner_email))


def get_session(tenant_slug: str, phone: str) -> dict:
    return _run(async_get_session(tenant_slug, phone))


def set_session(
    tenant_slug: str, phone: str, state: str, context: dict | None = None
) -> None:
    _run(async_set_session(tenant_slug, phone, state, context))


def clear_session(tenant_slug: str, phone: str) -> None:
    _run(async_clear_session(tenant_slug, phone))


def log_message(
    tenant_slug: str,
    phone: str,
    direction: str,
    content: str,
    intent: str | None = None,
    channel: str = "whatsapp",
) -> None:
    _run(async_log_message(tenant_slug, phone, direction, content, intent, channel))


def get_recent_messages(tenant_slug: str, limit: int = 30) -> list[dict]:
    return _run(async_get_recent_messages(tenant_slug, limit))


def get_inventory(tenant_slug: str) -> list[dict]:
    from bazaarbot.cache import get_cached_inventory, set_cached_inventory
    cached = get_cached_inventory(tenant_slug)
    if cached is not None:
        return cached
    result = _run(async_get_inventory(tenant_slug))
    set_cached_inventory(tenant_slug, result)
    return result


def get_product(tenant_slug: str, name: str) -> dict | None:
    return _run(async_get_product(tenant_slug, name))


def upsert_product(
    tenant_slug: str,
    product_name: str,
    category: str = "general",
    quantity: int = 0,
    unit: str = "pieces",
    buy_price: float = 0.0,
    sell_price: float = 0.0,
    reorder_level: int = 10,
    supplier: str = "",
) -> None:
    _run(
        async_upsert_product(
            tenant_slug, product_name, category, quantity, unit,
            buy_price, sell_price, reorder_level, supplier,
        )
    )
    from bazaarbot.cache import invalidate_inventory_cache
    invalidate_inventory_cache(tenant_slug)


def update_stock(tenant_slug: str, product_name: str, delta: int) -> None:
    _run(async_update_stock(tenant_slug, product_name, delta))
    from bazaarbot.cache import invalidate_inventory_cache
    invalidate_inventory_cache(tenant_slug)


def get_low_stock(tenant_slug: str) -> list[dict]:
    return _run(async_get_low_stock(tenant_slug))


def create_order(
    tenant_slug: str,
    phone: str,
    product_name: str,
    quantity: int,
    unit_price: float,
    payment_method: str = "pending",
) -> tuple[str, float]:
    result = _run(
        async_create_order(
            tenant_slug, phone, product_name, quantity, unit_price, payment_method
        )
    )
    # async_create_order calls async_update_stock which modifies stock;
    # bust the inventory cache so the next read reflects the deduction.
    from bazaarbot.cache import invalidate_inventory_cache
    invalidate_inventory_cache(tenant_slug)
    return result


def get_orders(
    tenant_slug: str, phone: str | None = None, limit: int = 10
) -> list[dict]:
    return _run(async_get_orders(tenant_slug, phone, limit))


def book_appointment(
    tenant_slug: str,
    phone: str,
    customer_name: str,
    apt_date: str,
    apt_time: str,
    purpose: str = "",
    notes: str = "",
) -> int | None:
    return _run(
        async_book_appointment(
            tenant_slug, phone, customer_name, apt_date, apt_time, purpose, notes
        )
    )


def get_appointments(
    tenant_slug: str,
    phone: str | None = None,
    upcoming_only: bool = True,
    limit: int = 10,
) -> list[dict]:
    return _run(async_get_appointments(tenant_slug, phone, upcoming_only, limit))


def cancel_appointment(apt_id: int, tenant_slug: str) -> None:
    _run(async_cancel_appointment(apt_id, tenant_slug))


def get_knowledge_docs(tenant_slug: str) -> list[dict]:
    return _run(async_get_knowledge_docs(tenant_slug))


def upsert_knowledge_doc(
    tenant_slug: str, title: str, content: str, tags: str = ""
) -> None:
    _run(async_upsert_knowledge_doc(tenant_slug, title, content, tags))


def delete_knowledge_doc(doc_id: int, tenant_slug: str) -> None:
    _run(async_delete_knowledge_doc(doc_id, tenant_slug))


def get_analytics(tenant_slug: str) -> dict:
    return _run(async_get_analytics(tenant_slug))


def get_user(tenant_slug: str, phone: str) -> dict | None:
    return _run(async_get_user(tenant_slug, phone))
