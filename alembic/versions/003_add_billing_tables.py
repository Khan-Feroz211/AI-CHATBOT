"""Add billing tables: subscriptions + billing_events.

Revision ID: 003
Revises:     001
Create Date: 2025-01-01 00:00:00.000000

What this migration does
------------------------
1. Creates the ``subscriptions`` table — one row per tenant, tracking the
   active SaaS plan, billing period, message counter, and gateway reference.
2. Creates the ``billing_events`` table — an append-only audit log for every
   significant billing action (payment, upgrade, cancellation, reset).
3. Adds composite indexes to support the most common query patterns:
   - ``(tenant_slug, status)`` on subscriptions for active-subscription lookups.
   - ``(period_end)``          on subscriptions for expiry sweeps.
   - ``(tenant_slug, created_at)`` on billing_events for per-tenant history.
4. Installs a PostgreSQL trigger function ``check_tenant_message_limit()``
   that enforces the per-tenant message quota at the DB level as a last line
   of defence (the application layer checks first via middleware.py).

Note: down_revision is "001" because the second migration (002, JWT/auth
additions) was applied via ``autogenerate`` and has no corresponding file in
this repository.  Adjust to "002" if that migration file is added later.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# ── Revision identifiers ───────────────────────────────────────────────────

revision: str = "003"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── upgrade ────────────────────────────────────────────────────────────────

def upgrade() -> None:
    # ── 1. subscriptions ─────────────────────────────────────────────────
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "sub_id",
            sa.String(36),
            nullable=False,
            comment="UUID for external references",
        ),
        sa.Column("tenant_slug", sa.String(100), nullable=False),
        sa.Column(
            "plan",
            sa.String(20),
            nullable=False,
            comment="starter | business | pro",
        ),
        sa.Column(
            "status",
            sa.String(20),
            server_default="active",
            nullable=False,
            comment="active | cancelled | expired | past_due",
        ),
        sa.Column("message_limit", sa.Integer(), nullable=False),
        sa.Column(
            "channels_allowed",
            sa.String(100),
            nullable=False,
            comment='JSON list, e.g. ["whatsapp"]',
        ),
        sa.Column(
            "llm_enabled",
            sa.Boolean(),
            server_default=sa.text("FALSE"),
            nullable=False,
        ),
        sa.Column("price_pkr", sa.Integer(), nullable=False),
        sa.Column(
            "billing_cycle",
            sa.String(20),
            server_default="monthly",
            nullable=False,
        ),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "message_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "gateway",
            sa.String(20),
            nullable=True,
            comment="jazzcash | easypaisa | free",
        ),
        sa.Column(
            "gateway_ref",
            sa.String(255),
            nullable=True,
            comment="Transaction reference returned by the payment gateway",
        ),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_slug"],
            ["tenants.slug"],
            ondelete="CASCADE",
            name="fk_subscriptions_tenant_slug",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sub_id", name="uq_subscriptions_sub_id"),
    )

    # Primary lookup: active subscription for a tenant.
    op.create_index(
        "ix_subscriptions_tenant_slug",
        "subscriptions",
        ["tenant_slug"],
    )

    # Composite index for the most common query filter.
    op.create_index(
        "ix_subscriptions_tenant_status",
        "subscriptions",
        ["tenant_slug", "status"],
    )

    # Supports scheduled expiry sweeps (find all subs where period_end < now).
    op.create_index(
        "ix_subscriptions_period_end",
        "subscriptions",
        ["period_end"],
    )

    # ── 2. billing_events ────────────────────────────────────────────────
    op.create_table(
        "billing_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "event_id",
            sa.String(36),
            nullable=False,
            comment="UUID for idempotency checks",
        ),
        sa.Column("tenant_slug", sa.String(100), nullable=False),
        sa.Column(
            "event_type",
            sa.String(50),
            nullable=False,
            comment=(
                "subscription_created | payment_succeeded | payment_failed | "
                "subscription_cancelled | plan_upgraded | message_limit_reset"
            ),
        ),
        sa.Column("plan", sa.String(20), nullable=True),
        sa.Column(
            "amount_pkr",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("gateway", sa.String(20), nullable=True),
        sa.Column(
            "gateway_data",
            sa.Text(),
            nullable=True,
            comment="Raw JSON payload from the payment-gateway callback",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", name="uq_billing_events_event_id"),
    )

    # Supports per-tenant billing history queries.
    op.create_index(
        "ix_billing_events_tenant_slug",
        "billing_events",
        ["tenant_slug"],
    )

    # Composite index for paginated per-tenant history ordered by time.
    op.create_index(
        "ix_billing_events_tenant_created",
        "billing_events",
        ["tenant_slug", "created_at"],
    )

    # ── 3. PostgreSQL trigger: enforce message limit at DB level ──────────
    # This is a last-resort guard.  The application enforces limits via
    # middleware.py first; the trigger fires on every INSERT into messages
    # as a defence-in-depth measure.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION check_tenant_message_limit()
        RETURNS TRIGGER AS $$
        DECLARE
            current_limit INTEGER;
            current_count INTEGER;
        BEGIN
            SELECT message_limit, message_count
              INTO current_limit, current_count
              FROM subscriptions
             WHERE tenant_slug = NEW.tenant_slug
               AND status = 'active'
             LIMIT 1;

            -- Only raise when a subscription row exists AND its counter has
            -- reached (or exceeded) the plan's limit.  Tenants with no
            -- subscription row are on the free trial and are NOT blocked here
            -- (the application layer handles that check).
            IF FOUND AND current_count >= current_limit THEN
                RAISE EXCEPTION
                    'Message limit exceeded for tenant %', NEW.tenant_slug
                    USING ERRCODE = 'P0001';
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_check_message_limit
        BEFORE INSERT ON messages
        FOR EACH ROW
        EXECUTE FUNCTION check_tenant_message_limit();
        """
    )


# ── downgrade ──────────────────────────────────────────────────────────────

def downgrade() -> None:
    # Drop the trigger before the function to avoid dependency errors.
    op.execute(
        "DROP TRIGGER IF EXISTS trg_check_message_limit ON messages;"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS check_tenant_message_limit();"
    )

    # Drop indexes explicitly (Alembic may not infer them on all backends).
    op.drop_index("ix_billing_events_tenant_created", table_name="billing_events")
    op.drop_index("ix_billing_events_tenant_slug", table_name="billing_events")
    op.drop_table("billing_events")

    op.drop_index("ix_subscriptions_period_end", table_name="subscriptions")
    op.drop_index("ix_subscriptions_tenant_status", table_name="subscriptions")
    op.drop_index("ix_subscriptions_tenant_slug", table_name="subscriptions")
    op.drop_table("subscriptions")
