"""SQLite persistence layer for BazaarBot."""
import sqlite3
import json
from datetime import datetime, timezone
from contextlib import contextmanager
from bazaarbot.config import config


@contextmanager
def get_db():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create all tables and seed demo data."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                city TEXT DEFAULT 'Karachi',
                business_type TEXT DEFAULT 'retail',
                owner_phone TEXT,
                owner_email TEXT,
                easypaisa_number TEXT,
                jazzcash_number TEXT,
                bank_title TEXT,
                bank_iban TEXT,
                notify_email TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            INSERT OR IGNORE INTO tenants (slug, name, city, business_type)
            VALUES ('default', 'BazaarBot Demo', 'Karachi', 'retail');

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_slug TEXT NOT NULL DEFAULT 'default',
                phone TEXT NOT NULL,
                name TEXT,
                city TEXT,
                role TEXT DEFAULT 'customer',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tenant_slug, phone)
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_slug TEXT NOT NULL DEFAULT 'default',
                phone TEXT NOT NULL,
                state TEXT DEFAULT 'idle',
                context TEXT DEFAULT '{}',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tenant_slug, phone)
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_slug TEXT NOT NULL DEFAULT 'default',
                phone TEXT NOT NULL,
                direction TEXT NOT NULL,
                content TEXT NOT NULL,
                intent TEXT,
                channel TEXT DEFAULT 'whatsapp',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_slug TEXT NOT NULL DEFAULT 'default',
                product_name TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                quantity INTEGER NOT NULL DEFAULT 0,
                unit TEXT DEFAULT 'pieces',
                buy_price REAL NOT NULL DEFAULT 0,
                sell_price REAL NOT NULL DEFAULT 0,
                reorder_level INTEGER DEFAULT 10,
                supplier TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tenant_slug, product_name)
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_slug TEXT NOT NULL DEFAULT 'default',
                phone TEXT NOT NULL,
                order_ref TEXT NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total REAL NOT NULL,
                payment_method TEXT DEFAULT 'pending',
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_slug TEXT NOT NULL DEFAULT 'default',
                phone TEXT NOT NULL,
                customer_name TEXT,
                appointment_date TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                purpose TEXT,
                status TEXT DEFAULT 'booked',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS knowledge_docs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_slug TEXT NOT NULL DEFAULT 'default',
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT DEFAULT '',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
    # Seed after tables are committed
    _seed_demo_inventory()


def _seed_demo_inventory():
    """Seed realistic Pakistani product inventory if table is empty."""
    demo_products = [
        ("Basmati Chawal",  "food",       500,  "kg",     150, 180, 50,  "Kohinoor Mills"),
        ("Atta (Flour)",    "food",       300,  "kg",     55,  70,  100, "National Foods"),
        ("Cooking Oil",     "food",       200,  "litre",  380, 420, 30,  "Dalda Foods"),
        ("Sugar (Cheeni)",  "food",       400,  "kg",     120, 140, 80,  "Al-Abbas Sugar"),
        ("Daal Mash",       "food",       150,  "kg",     220, 260, 20,  "Local Market"),
        ("Surf Excel 1kg",  "household",  250,  "box",    320, 380, 40,  "Unilever"),
        ("Mobile Recharge", "telecom",    1000, "pieces", 95,  100, 200, "Jazz/Zong"),
        ("LED Bulb 18W",    "electronics",80,   "pieces", 180, 250, 10,  "Local Wholesale"),
        ("Cotton Kameez",   "clothing",   60,   "pieces", 400, 600, 5,   "Faisalabad Market"),
        ("Panadol Strip",   "medicine",   500,  "strip",  25,  35,  100, "GSK Pakistan"),
    ]
    with get_db() as conn:
        for name, cat, qty, unit, buy, sell, reorder, supplier in demo_products:
            conn.execute("""
                INSERT OR IGNORE INTO inventory
                (tenant_slug, product_name, category, quantity, unit,
                 buy_price, sell_price, reorder_level, supplier)
                VALUES ('default', ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, cat, qty, unit, buy, sell, reorder, supplier))


# ── Session helpers ──────────────────────────────────────────────────────

def get_session(tenant_slug, phone):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE tenant_slug=? AND phone=?",
            (tenant_slug, phone)
        ).fetchone()
        if row:
            return {"state": row["state"], "context": json.loads(row["context"])}
    return {"state": "idle", "context": {}}


def set_session(tenant_slug, phone, state, context=None):
    ctx = json.dumps(context or {})
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO sessions (tenant_slug, phone, state, context, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(tenant_slug, phone)
            DO UPDATE SET state=excluded.state,
                          context=excluded.context,
                          updated_at=excluded.updated_at
        """, (tenant_slug, phone, state, ctx, now))


def clear_session(tenant_slug, phone):
    set_session(tenant_slug, phone, "idle", {})


# ── Message logging ──────────────────────────────────────────────────────

def log_message(tenant_slug, phone, direction, content, intent=None, channel="whatsapp"):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO messages "
            "(tenant_slug, phone, direction, content, intent, channel) "
            "VALUES (?,?,?,?,?,?)",
            (tenant_slug, phone, direction, content, intent, channel)
        )


def get_recent_messages(tenant_slug, limit=30):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT phone, direction, content, intent, channel, created_at "
            "FROM messages WHERE tenant_slug=? ORDER BY id DESC LIMIT ?",
            (tenant_slug, limit)
        ).fetchall()
        return [dict(r) for r in rows]


# ── Inventory helpers ────────────────────────────────────────────────────

def get_inventory(tenant_slug):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM inventory WHERE tenant_slug=? ORDER BY product_name",
            (tenant_slug,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_product(tenant_slug, name):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM inventory "
            "WHERE tenant_slug=? AND lower(product_name)=lower(?)",
            (tenant_slug, name)
        ).fetchone()
        return dict(row) if row else None


def upsert_product(tenant_slug, product_name, category="general", quantity=0,
                   unit="pieces", buy_price=0.0, sell_price=0.0,
                   reorder_level=10, supplier=""):
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO inventory
            (tenant_slug, product_name, category, quantity, unit,
             buy_price, sell_price, reorder_level, supplier, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(tenant_slug, product_name)
            DO UPDATE SET
                category=excluded.category,
                quantity=excluded.quantity,
                unit=excluded.unit,
                buy_price=excluded.buy_price,
                sell_price=excluded.sell_price,
                reorder_level=excluded.reorder_level,
                supplier=excluded.supplier,
                updated_at=excluded.updated_at
        """, (tenant_slug, product_name, category, quantity, unit,
              buy_price, sell_price, reorder_level, supplier, now))


def update_stock(tenant_slug, product_name, delta):
    """Adjust stock quantity (delta negative = sale)."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            "UPDATE inventory "
            "SET quantity = MAX(0, quantity + ?), updated_at=? "
            "WHERE tenant_slug=? AND lower(product_name)=lower(?)",
            (delta, now, tenant_slug, product_name)
        )


def get_low_stock(tenant_slug):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM inventory "
            "WHERE tenant_slug=? AND quantity <= reorder_level ORDER BY quantity",
            (tenant_slug,)
        ).fetchall()
        return [dict(r) for r in rows]


# ── Order helpers ────────────────────────────────────────────────────────

def create_order(tenant_slug, phone, product_name, quantity, unit_price,
                 payment_method="pending"):
    total = round(quantity * unit_price, 2)
    ref = ("ORD-" + str(abs(hash(phone + product_name + str(quantity))))[-6:]).upper()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO orders "
            "(tenant_slug, phone, order_ref, product_name, quantity, "
            " unit_price, total, payment_method) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (tenant_slug, phone, ref, product_name, quantity,
             unit_price, total, payment_method)
        )
    update_stock(tenant_slug, product_name, -quantity)
    return ref, total


def get_orders(tenant_slug, phone=None, limit=10):
    with get_db() as conn:
        if phone:
            rows = conn.execute(
                "SELECT * FROM orders WHERE tenant_slug=? AND phone=? "
                "ORDER BY id DESC LIMIT ?",
                (tenant_slug, phone, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM orders WHERE tenant_slug=? "
                "ORDER BY id DESC LIMIT ?",
                (tenant_slug, limit)
            ).fetchall()
        return [dict(r) for r in rows]


# ── Appointment helpers ──────────────────────────────────────────────────

def book_appointment(tenant_slug, phone, customer_name, apt_date,
                     apt_time, purpose="", notes=""):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO appointments "
            "(tenant_slug, phone, customer_name, appointment_date, "
            " appointment_time, purpose, notes) "
            "VALUES (?,?,?,?,?,?,?)",
            (tenant_slug, phone, customer_name, apt_date,
             apt_time, purpose, notes)
        )
        row = conn.execute("SELECT last_insert_rowid() as id").fetchone()
        return row["id"] if row else None


def get_appointments(tenant_slug, phone=None, upcoming_only=True, limit=10):
    with get_db() as conn:
        base = "SELECT * FROM appointments WHERE tenant_slug=?"
        params = [tenant_slug]
        if phone:
            base += " AND phone=?"
            params.append(phone)
        if upcoming_only:
            base += " AND appointment_date >= date('now')"
        base += " ORDER BY appointment_date, appointment_time LIMIT ?"
        params.append(limit)
        rows = conn.execute(base, params).fetchall()
        return [dict(r) for r in rows]


def cancel_appointment(apt_id, tenant_slug):
    with get_db() as conn:
        conn.execute(
            "UPDATE appointments SET status='cancelled' "
            "WHERE id=? AND tenant_slug=?",
            (apt_id, tenant_slug)
        )


# ── Analytics ────────────────────────────────────────────────────────────

def get_analytics(tenant_slug):
    with get_db() as conn:
        total_msgs = conn.execute(
            "SELECT COUNT(*) as c FROM messages WHERE tenant_slug=?",
            (tenant_slug,)
        ).fetchone()["c"]
        today_msgs = conn.execute(
            "SELECT COUNT(*) as c FROM messages "
            "WHERE tenant_slug=? AND date(created_at)=date('now')",
            (tenant_slug,)
        ).fetchone()["c"]
        order_row = conn.execute(
            "SELECT COUNT(*) as c, COALESCE(SUM(total),0) as rev "
            "FROM orders WHERE tenant_slug=?",
            (tenant_slug,)
        ).fetchone()
        upcoming_apts = conn.execute(
            "SELECT COUNT(*) as c FROM appointments "
            "WHERE tenant_slug=? AND appointment_date>=date('now') "
            "AND status='booked'",
            (tenant_slug,)
        ).fetchone()["c"]
        low_stock_count = conn.execute(
            "SELECT COUNT(*) as c FROM inventory "
            "WHERE tenant_slug=? AND quantity<=reorder_level",
            (tenant_slug,)
        ).fetchone()["c"]
        top_intents = conn.execute(
            "SELECT intent, COUNT(*) as c FROM messages "
            "WHERE tenant_slug=? AND intent IS NOT NULL "
            "GROUP BY intent ORDER BY c DESC LIMIT 6",
            (tenant_slug,)
        ).fetchall()
        return {
            "total_messages": total_msgs,
            "today_messages": today_msgs,
            "total_orders": order_row["c"],
            "total_revenue": float(order_row["rev"]),
            "upcoming_appointments": upcoming_apts,
            "low_stock_items": low_stock_count,
            "top_intents": {r["intent"]: r["c"] for r in top_intents},
        }


# ── Knowledge docs ───────────────────────────────────────────────────────

def get_knowledge_docs(tenant_slug):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM knowledge_docs WHERE tenant_slug=?",
            (tenant_slug,)
        ).fetchall()
        return [dict(r) for r in rows]


def upsert_knowledge_doc(tenant_slug, title, content, tags=""):
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM knowledge_docs WHERE tenant_slug=? AND title=?",
            (tenant_slug, title)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE knowledge_docs "
                "SET content=?, tags=?, updated_at=? WHERE id=?",
                (content, tags, now, existing["id"])
            )
        else:
            conn.execute(
                "INSERT INTO knowledge_docs "
                "(tenant_slug, title, content, tags, updated_at) "
                "VALUES (?,?,?,?,?)",
                (tenant_slug, title, content, tags, now)
            )


def delete_knowledge_doc(doc_id, tenant_slug):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM knowledge_docs WHERE id=? AND tenant_slug=?",
            (doc_id, tenant_slug)
        )


# ── Tenant helpers ───────────────────────────────────────────────────────

def get_tenant(slug):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM tenants WHERE slug=?", (slug,)
        ).fetchone()
        return dict(row) if row else None


def create_tenant(slug, name, city="Karachi", business_type="retail",
                  owner_phone="", owner_email=""):
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO tenants "
            "(slug, name, city, business_type, owner_phone, owner_email) "
            "VALUES (?,?,?,?,?,?)",
            (slug, name, city, business_type, owner_phone, owner_email)
        )


def list_tenants():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM tenants ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]
