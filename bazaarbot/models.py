"""SQLAlchemy ORM models for BazaarBot (PostgreSQL / Day 2+).

All 8 tables mirror the existing SQLite schema with additional columns
introduced in Day 2: plan, api_key, admin_password_hash, is_active on
Tenant; password_hash, jwt_token on User.
"""
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Tenant ────────────────────────────────────────────────────────────────

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    city = Column(String(100), default="Karachi", nullable=False)
    business_type = Column(String(50), default="retail", nullable=False)
    owner_phone = Column(String(30), nullable=True)
    owner_email = Column(String(255), nullable=True)
    easypaisa_number = Column(String(30), nullable=True)
    jazzcash_number = Column(String(30), nullable=True)
    bank_title = Column(String(100), nullable=True)
    bank_iban = Column(String(50), nullable=True)
    notify_email = Column(String(255), nullable=True)
    # Day 2 additions
    plan = Column(String(20), default="starter", nullable=False)
    api_key = Column(String(64), unique=True, nullable=True, index=True)
    admin_password_hash = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="tenant", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="tenant", cascade="all, delete-orphan")
    inventory = relationship("Inventory", back_populates="tenant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="tenant", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="tenant", cascade="all, delete-orphan")
    knowledge_docs = relationship("KnowledgeDoc", back_populates="tenant", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "slug": self.slug,
            "name": self.name,
            "city": self.city,
            "business_type": self.business_type,
            "owner_phone": self.owner_phone,
            "owner_email": self.owner_email,
            "easypaisa_number": self.easypaisa_number,
            "jazzcash_number": self.jazzcash_number,
            "bank_title": self.bank_title,
            "bank_iban": self.bank_iban,
            "notify_email": self.notify_email,
            "plan": self.plan,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── User ──────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_slug", "phone", name="uq_users_tenant_phone"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_slug = Column(
        String(100),
        ForeignKey("tenants.slug", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phone = Column(String(30), nullable=False)
    name = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    role = Column(String(20), default="customer", nullable=False)
    # Day 2 additions
    password_hash = Column(String(255), nullable=True)
    jwt_token = Column(String(255), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        nullable=False,
    )

    tenant = relationship("Tenant", back_populates="users")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_slug": self.tenant_slug,
            "phone": self.phone,
            "name": self.name,
            "city": self.city,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── Session ───────────────────────────────────────────────────────────────

class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        UniqueConstraint("tenant_slug", "phone", name="uq_sessions_tenant_phone"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_slug = Column(
        String(100),
        ForeignKey("tenants.slug", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phone = Column(String(30), nullable=False)
    state = Column(String(50), default="idle", nullable=False)
    context = Column(JSONB, default=dict, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        server_default=func.now(),
        nullable=False,
    )

    tenant = relationship("Tenant", back_populates="sessions")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_slug": self.tenant_slug,
            "phone": self.phone,
            "state": self.state,
            "context": self.context or {},
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ── Message ───────────────────────────────────────────────────────────────

class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_tenant_created", "tenant_slug", "created_at"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_slug = Column(
        String(100),
        ForeignKey("tenants.slug", ondelete="CASCADE"),
        nullable=False,
    )
    phone = Column(String(30), nullable=False)
    direction = Column(String(10), nullable=False)  # "in" | "out"
    content = Column(Text, nullable=False)
    intent = Column(String(50), nullable=True)
    channel = Column(String(20), default="whatsapp", nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        nullable=False,
    )

    tenant = relationship("Tenant", back_populates="messages")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_slug": self.tenant_slug,
            "phone": self.phone,
            "direction": self.direction,
            "content": self.content,
            "intent": self.intent,
            "channel": self.channel,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── Inventory ─────────────────────────────────────────────────────────────

class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint("tenant_slug", "product_name", name="uq_inventory_tenant_product"),
        Index("ix_inventory_tenant_category", "tenant_slug", "category"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_slug = Column(
        String(100),
        ForeignKey("tenants.slug", ondelete="CASCADE"),
        nullable=False,
    )
    product_name = Column(String(255), nullable=False)
    category = Column(String(50), default="general", nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    unit = Column(String(30), default="pieces", nullable=False)
    buy_price = Column(Float, default=0.0, nullable=False)
    sell_price = Column(Float, default=0.0, nullable=False)
    reorder_level = Column(Integer, default=10, nullable=False)
    supplier = Column(String(255), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        server_default=func.now(),
        nullable=False,
    )

    tenant = relationship("Tenant", back_populates="inventory")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_slug": self.tenant_slug,
            "product_name": self.product_name,
            "category": self.category,
            "quantity": self.quantity,
            "unit": self.unit,
            "buy_price": self.buy_price,
            "sell_price": self.sell_price,
            "reorder_level": self.reorder_level,
            "supplier": self.supplier,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ── Order ─────────────────────────────────────────────────────────────────

class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_tenant_status", "tenant_slug", "status"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_slug = Column(
        String(100),
        ForeignKey("tenants.slug", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phone = Column(String(30), nullable=False)
    order_ref = Column(String(20), nullable=False)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    payment_method = Column(String(30), default="pending", nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        nullable=False,
    )

    tenant = relationship("Tenant", back_populates="orders")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_slug": self.tenant_slug,
            "phone": self.phone,
            "order_ref": self.order_ref,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total": self.total,
            "payment_method": self.payment_method,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── Appointment ───────────────────────────────────────────────────────────

class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        Index("ix_appointments_tenant_status", "tenant_slug", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_slug = Column(
        String(100),
        ForeignKey("tenants.slug", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phone = Column(String(30), nullable=False)
    customer_name = Column(String(255), nullable=True)
    appointment_date = Column(String(10), nullable=False)  # "YYYY-MM-DD"
    appointment_time = Column(String(5), nullable=False)   # "HH:MM"
    purpose = Column(Text, nullable=True)
    status = Column(String(20), default="booked", nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        nullable=False,
    )

    tenant = relationship("Tenant", back_populates="appointments")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_slug": self.tenant_slug,
            "phone": self.phone,
            "customer_name": self.customer_name,
            "appointment_date": self.appointment_date,
            "appointment_time": self.appointment_time,
            "purpose": self.purpose,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── KnowledgeDoc ──────────────────────────────────────────────────────────

class KnowledgeDoc(Base):
    __tablename__ = "knowledge_docs"
    __table_args__ = (
        Index("ix_knowledge_docs_tenant", "tenant_slug"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_slug = Column(
        String(100),
        ForeignKey("tenants.slug", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(String(500), default="", nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        server_default=func.now(),
        nullable=False,
    )

    tenant = relationship("Tenant", back_populates="knowledge_docs")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_slug": self.tenant_slug,
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
