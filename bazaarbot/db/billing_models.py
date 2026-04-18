"""SQLAlchemy ORM models for SaaS billing (Day 7).

Two tables:
  subscriptions   — active subscription per tenant
  billing_events  — immutable audit log of all billing events
"""
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import declarative_base

# Re-use the shared Base so Alembic sees all models together.
# Import from bazaarbot.models to share the same metadata registry.
try:
    from bazaarbot.models import Base
except ImportError:  # pragma: no cover – standalone usage
    Base = declarative_base()


class Subscription(Base):
    """One active subscription record per tenant."""

    __tablename__ = "subscriptions"
    __table_args__ = (
        Index("ix_subscriptions_tenant_slug", "tenant_slug"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    sub_id = Column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid4()),
    )
    tenant_slug = Column(
        String(100),
        ForeignKey("tenants.slug", ondelete="CASCADE"),
        nullable=False,
    )
    plan = Column(
        String(20),
        nullable=False,
        comment="starter | business | pro",
    )
    status = Column(
        String(20),
        nullable=False,
        default="active",
        comment="active | cancelled | expired | past_due",
    )
    message_limit = Column(Integer, nullable=False)
    channels_allowed = Column(
        String(100),
        nullable=False,
        comment='JSON list, e.g. ["whatsapp"]',
    )
    llm_enabled = Column(Boolean, nullable=False, default=False)
    price_pkr = Column(Integer, nullable=False)
    billing_cycle = Column(String(20), nullable=False, default="monthly")
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    message_count = Column(Integer, nullable=False, default=0)
    gateway = Column(
        String(20),
        nullable=True,
        comment="jazzcash | easypaisa | free",
    )
    gateway_ref = Column(
        String(255),
        nullable=True,
        comment="Payment reference returned by the gateway",
    )
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sub_id": self.sub_id,
            "tenant_slug": self.tenant_slug,
            "plan": self.plan,
            "status": self.status,
            "message_limit": self.message_limit,
            "channels_allowed": self.channels_allowed,
            "llm_enabled": self.llm_enabled,
            "price_pkr": self.price_pkr,
            "billing_cycle": self.billing_cycle,
            "period_start": (
                self.period_start.isoformat() if self.period_start else None
            ),
            "period_end": (
                self.period_end.isoformat() if self.period_end else None
            ),
            "message_count": self.message_count,
            "gateway": self.gateway,
            "gateway_ref": self.gateway_ref,
            "cancelled_at": (
                self.cancelled_at.isoformat() if self.cancelled_at else None
            ),
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }


class BillingEvent(Base):
    """Immutable audit log for every billing-related event."""

    __tablename__ = "billing_events"
    __table_args__ = (
        Index("ix_billing_events_tenant_slug", "tenant_slug"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid4()),
    )
    tenant_slug = Column(String(100), nullable=False)
    event_type = Column(
        String(50),
        nullable=False,
        comment=(
            "subscription_created | payment_succeeded | payment_failed | "
            "subscription_cancelled | plan_upgraded | message_limit_reset"
        ),
    )
    plan = Column(String(20), nullable=True)
    amount_pkr = Column(Integer, nullable=False, default=0)
    gateway = Column(String(20), nullable=True)
    gateway_data = Column(
        Text,
        nullable=True,
        comment="Raw JSON payload received from the payment gateway callback",
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_id": self.event_id,
            "tenant_slug": self.tenant_slug,
            "event_type": self.event_type,
            "plan": self.plan,
            "amount_pkr": self.amount_pkr,
            "gateway": self.gateway,
            "gateway_data": self.gateway_data,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }
