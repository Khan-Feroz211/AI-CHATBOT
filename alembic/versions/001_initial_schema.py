"""Initial schema — all 8 BazaarBot tables + indexes + RLS policies.

Revision ID: 001
Revises: None
Create Date: 2024-12-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── Tables where tenant isolation RLS applies ─────────────────────────────
_RLS_TABLES = (
    "users",
    "sessions",
    "messages",
    "inventory",
    "orders",
    "appointments",
    "knowledge_docs",
)


def upgrade() -> None:
    # ── 1. tenants ────────────────────────────────────────────────────────
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("city", sa.String(100), server_default="Karachi", nullable=False),
        sa.Column("business_type", sa.String(50), server_default="retail", nullable=False),
        sa.Column("owner_phone", sa.String(30), nullable=True),
        sa.Column("owner_email", sa.String(255), nullable=True),
        sa.Column("easypaisa_number", sa.String(30), nullable=True),
        sa.Column("jazzcash_number", sa.String(30), nullable=True),
        sa.Column("bank_title", sa.String(100), nullable=True),
        sa.Column("bank_iban", sa.String(50), nullable=True),
        sa.Column("notify_email", sa.String(255), nullable=True),
        sa.Column("plan", sa.String(20), server_default="starter", nullable=False),
        sa.Column("api_key", sa.String(64), nullable=True),
        sa.Column("admin_password_hash", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("TRUE"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
        sa.UniqueConstraint("api_key", name="uq_tenants_api_key"),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)
    op.create_index("ix_tenants_api_key", "tenants", ["api_key"], unique=True)

    # ── 2. users ──────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_slug", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(30), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("role", sa.String(20), server_default="customer", nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("jwt_token", sa.String(255), nullable=True),
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
            name="fk_users_tenant_slug",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_slug", "phone", name="uq_users_tenant_phone"),
    )
    op.create_index("ix_users_tenant_slug", "users", ["tenant_slug"])

    # ── 3. sessions ───────────────────────────────────────────────────────
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_slug", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(30), nullable=False),
        sa.Column("state", sa.String(50), server_default="idle", nullable=False),
        sa.Column(
            "context",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_slug"],
            ["tenants.slug"],
            ondelete="CASCADE",
            name="fk_sessions_tenant_slug",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_slug", "phone", name="uq_sessions_tenant_phone"),
    )
    op.create_index("ix_sessions_tenant_slug", "sessions", ["tenant_slug"])

    # ── 4. messages ───────────────────────────────────────────────────────
    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_slug", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(30), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(50), nullable=True),
        sa.Column("channel", sa.String(20), server_default="whatsapp", nullable=False),
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
            name="fk_messages_tenant_slug",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_messages_tenant_created", "messages", ["tenant_slug", "created_at"]
    )

    # ── 5. inventory ──────────────────────────────────────────────────────
    op.create_table(
        "inventory",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_slug", sa.String(100), nullable=False),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(50), server_default="general", nullable=False),
        sa.Column("quantity", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("unit", sa.String(30), server_default="pieces", nullable=False),
        sa.Column("buy_price", sa.Float(), server_default=sa.text("0"), nullable=False),
        sa.Column("sell_price", sa.Float(), server_default=sa.text("0"), nullable=False),
        sa.Column("reorder_level", sa.Integer(), server_default=sa.text("10"), nullable=False),
        sa.Column("supplier", sa.String(255), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_slug"],
            ["tenants.slug"],
            ondelete="CASCADE",
            name="fk_inventory_tenant_slug",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_slug", "product_name", name="uq_inventory_tenant_product"
        ),
    )
    op.create_index(
        "ix_inventory_tenant_category", "inventory", ["tenant_slug", "category"]
    )

    # ── 6. orders ─────────────────────────────────────────────────────────
    op.create_table(
        "orders",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_slug", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(30), nullable=False),
        sa.Column("order_ref", sa.String(20), nullable=False),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("total", sa.Float(), nullable=False),
        sa.Column(
            "payment_method", sa.String(30), server_default="pending", nullable=False
        ),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
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
            name="fk_orders_tenant_slug",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_orders_tenant_slug", "orders", ["tenant_slug"])
    op.create_index("ix_orders_tenant_status", "orders", ["tenant_slug", "status"])

    # ── 7. appointments ───────────────────────────────────────────────────
    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_slug", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(30), nullable=False),
        sa.Column("customer_name", sa.String(255), nullable=True),
        sa.Column("appointment_date", sa.String(10), nullable=False),
        sa.Column("appointment_time", sa.String(5), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), server_default="booked", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
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
            name="fk_appointments_tenant_slug",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_appointments_tenant_slug", "appointments", ["tenant_slug"])
    op.create_index(
        "ix_appointments_tenant_status", "appointments", ["tenant_slug", "status"]
    )

    # ── 8. knowledge_docs ─────────────────────────────────────────────────
    op.create_table(
        "knowledge_docs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_slug", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tags", sa.String(500), server_default="", nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_slug"],
            ["tenants.slug"],
            ondelete="CASCADE",
            name="fk_knowledge_docs_tenant_slug",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_docs_tenant", "knowledge_docs", ["tenant_slug"])

    # ── Row-Level Security: enable on all tables ──────────────────────────
    op.execute(
        """
        ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
        ALTER TABLE users ENABLE ROW LEVEL SECURITY;
        ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
        ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
        ALTER TABLE inventory ENABLE ROW LEVEL SECURITY;
        ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
        ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
        ALTER TABLE knowledge_docs ENABLE ROW LEVEL SECURITY;
        """
    )

    # ── RLS: tenant isolation policy (applies to non-superadmin sessions) ─
    for table in _RLS_TABLES:
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (
                tenant_slug = current_setting('app.current_tenant', TRUE)
            );
            """
        )

    # ── RLS: create app role and superadmin bypass policy ─────────────────
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT FROM pg_catalog.pg_roles WHERE rolname = 'bazaarbot_app'
            ) THEN
                CREATE ROLE bazaarbot_app;
            END IF;
        END
        $$;
        GRANT ALL ON ALL TABLES IN SCHEMA public TO bazaarbot_app;
        """
    )

    for table in _RLS_TABLES:
        op.execute(
            f"""
            CREATE POLICY superadmin_bypass ON {table}
            TO bazaarbot_app
            USING (TRUE);
            """
        )


def downgrade() -> None:
    # ── Drop superadmin bypass policies ───────────────────────────────────
    for table in reversed(_RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS superadmin_bypass ON {table};")

    # ── Drop tenant isolation policies ────────────────────────────────────
    for table in reversed(_RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")

    # ── Drop tables in reverse dependency order ───────────────────────────
    op.drop_table("knowledge_docs")
    op.drop_table("appointments")
    op.drop_table("orders")
    op.drop_table("inventory")
    op.drop_table("messages")
    op.drop_table("sessions")
    op.drop_table("users")
    op.drop_table("tenants")
