"""Intent router — multi-turn session-aware message dispatcher."""
from bazaarbot import database as db
from bazaarbot.bot.menu import get_main_menu
from bazaarbot.bot.handlers import (
    handle_stock,
    handle_add_stock_prompt,
    handle_add_stock,
    handle_update_stock,
    handle_sell,
    handle_order_start,
    handle_order_create,
    handle_market_finder,
    handle_payment,
    handle_appointment_start,
    handle_appointment_create,
    handle_view_appointments,
    handle_cancel_appointment,
    handle_transactions,
    handle_help,
    handle_unknown,
)
from bazaarbot.nlp.rag_engine import get_engine
from bazaarbot.config import config

_MENU_TRIGGERS = {
    "hi", "hello", "hey", "start", "menu", "salam", "aoa",
    "assalam", "salaam", "shuru", "",
}


def process_message(phone: str, message: str,
                    tenant_slug: str = "") -> str:
    """Route an incoming message and return a response string."""
    tenant_slug = tenant_slug or config.DEFAULT_TENANT
    message = (message or "").strip()
    lower = message.lower()

    db.log_message(tenant_slug, phone, "in", message)

    session = db.get_session(tenant_slug, phone)
    state = session.get("state", "idle")

    response = _route(tenant_slug, phone, lower, message, state)

    db.log_message(tenant_slug, phone, "out", response)
    return response


def _menu(tenant_slug: str) -> str:
    tenant = db.get_tenant(tenant_slug)
    return get_main_menu((tenant or {}).get("name", "BazaarBot"))


def _route(tenant_slug: str, phone: str,
           lower: str, original: str, state: str) -> str:

    # ── Multi-turn: adding stock ─────────────────────────────────────────
    if state == "adding_stock":
        if lower in ("menu", "cancel", "exit"):
            db.clear_session(tenant_slug, phone)
            return _menu(tenant_slug)
        prefix = lower if lower.startswith("add ") else "add product " + original
        return handle_add_stock(tenant_slug, phone, prefix)

    # ── Multi-turn: placing order ────────────────────────────────────────
    if state == "placing_order":
        if lower in ("menu", "cancel", "exit"):
            db.clear_session(tenant_slug, phone)
            return _menu(tenant_slug)
        prefix = lower if lower.startswith("order ") else "order " + original
        return handle_order_create(tenant_slug, phone, prefix)

    # ── Multi-turn: booking appointment ─────────────────────────────────
    if state == "booking_appointment":
        if lower in ("menu", "cancel", "exit"):
            db.clear_session(tenant_slug, phone)
            return _menu(tenant_slug)
        prefix = (
            lower if lower.startswith("appoint ")
            else "appoint " + original
        )
        return handle_appointment_create(tenant_slug, phone, prefix)

    # ── NLP intent classification ────────────────────────────────────────
    engine = get_engine()
    try:
        engine.load_tenant_docs(tenant_slug)
    except Exception:
        pass
    intent, rag_response = engine.answer(lower)

    # Direct RAG responses (escalate, unknown-with-snippet)
    handled_by_router = {
        "greet", "stock_check", "add_stock", "sell", "order", "payment",
        "market_finder", "appointment", "transactions", "price", "help",
    }
    if rag_response and intent not in handled_by_router:
        return rag_response

    # ── Greet / menu ─────────────────────────────────────────────────────
    if lower in _MENU_TRIGGERS or intent == "greet":
        return _menu(tenant_slug)

    # ── Stock ─────────────────────────────────────────────────────────────
    if lower in ("1", "stock", "maal", "inventory", "check stock") \
            or intent == "stock_check":
        return handle_stock(tenant_slug, phone)

    # ── Add stock ─────────────────────────────────────────────────────────
    if lower.startswith("add "):
        return handle_add_stock(tenant_slug, phone, lower)
    if intent == "add_stock":
        return handle_add_stock_prompt(tenant_slug, phone)

    # ── Sell ──────────────────────────────────────────────────────────────
    if lower.startswith("sell "):
        return handle_sell(tenant_slug, phone, lower)
    if intent == "sell":
        return "Format: *sell [product] [qty]*\nMisaal: sell Atta 5"

    # ── Update stock ──────────────────────────────────────────────────────
    if lower.startswith("update "):
        return handle_update_stock(tenant_slug, phone, lower)

    # ── Order ─────────────────────────────────────────────────────────────
    if lower in ("2", "order", "naya order") or (
        intent == "order" and not lower.startswith("order ")
    ):
        return handle_order_start(tenant_slug, phone)
    if lower.startswith("order "):
        return handle_order_create(tenant_slug, phone, lower)

    # ── Market finder ─────────────────────────────────────────────────────
    if lower in ("3", "market", "bazaar", "supplier", "mandi") \
            or intent == "market_finder":
        return handle_market_finder(tenant_slug, phone, lower)
    if lower.startswith("market "):
        return handle_market_finder(tenant_slug, phone, lower)

    # ── Payment ───────────────────────────────────────────────────────────
    if lower in ("4", "payment", "pay", "easypaisa", "jazzcash") \
            or intent == "payment":
        return handle_payment(tenant_slug, phone)

    # ── Appointment ───────────────────────────────────────────────────────
    if lower in ("5", "appointment", "appoint", "booking") \
            or intent == "appointment":
        return handle_appointment_start(tenant_slug, phone)
    if lower.startswith("appoint "):
        return handle_appointment_create(tenant_slug, phone, lower)
    if lower in ("appointments", "my appointments", "meri appointments"):
        return handle_view_appointments(tenant_slug, phone)
    if lower.startswith("cancel appoint"):
        return handle_cancel_appointment(tenant_slug, phone, lower)

    # ── Transactions ──────────────────────────────────────────────────────
    if lower in ("6", "history", "transactions", "orders") \
            or intent == "transactions":
        return handle_transactions(tenant_slug, phone)

    # ── Help ──────────────────────────────────────────────────────────────
    if lower in ("7", "help", "madad", "?") or intent == "help":
        return handle_help()

    # ── Fallback ──────────────────────────────────────────────────────────
    return handle_unknown(tenant_slug, phone, rag_response or "")
