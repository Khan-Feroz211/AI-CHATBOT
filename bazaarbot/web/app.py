"""BazaarBot web dashboard — Flask routes."""
import re
import traceback
from flask import (
    Flask, request, render_template, redirect, url_for,
    session, jsonify, flash,
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from twilio.twiml.messaging_response import MessagingResponse

from bazaarbot.config import config
from bazaarbot import database as db
from bazaarbot.bot.intent_router import process_message

import os as _os
_templates = _os.path.join(_os.path.dirname(__file__), "templates")
_static = _os.path.join(_os.path.dirname(__file__), "static")

app = Flask(__name__, template_folder=_templates, static_folder=_static)
app.secret_key = config.SECRET_KEY

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[config.RATE_LIMIT],
    storage_uri="memory://",
)

# Initialise DB lazily on first request so tests can override DATABASE_PATH
_db_initialised = False


@app.before_request
def _ensure_db():
    global _db_initialised
    if not _db_initialised:
        db.init_db()
        _db_initialised = True


# ── Helpers ──────────────────────────────────────────────────────────────

def _require_admin():
    if not session.get("admin"):
        return redirect(url_for("login"))
    return None


def _extract_text(payload) -> str:
    for key in ("Body", "ButtonText", "ButtonPayload", "ListTitle"):
        v = payload.get(key, "")
        if v and str(v).strip():
            return str(v).strip()
    return ""


# ── Auth ─────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password", "") == config.ADMIN_PASSWORD:
            session["admin"] = True
            session["tenant"] = config.DEFAULT_TENANT
            return redirect(url_for("dashboard"))
        flash("Galat password. Dobara koshish karein.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ── Public ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── Dashboard ─────────────────────────────────────────────────────────────

@app.route("/dashboard")
def dashboard():
    redir = _require_admin()
    if redir:
        return redir
    tenant_slug = session.get("tenant", config.DEFAULT_TENANT)
    return render_template(
        "dashboard.html",
        analytics=db.get_analytics(tenant_slug),
        messages=db.get_recent_messages(tenant_slug, limit=30),
        low_stock=db.get_low_stock(tenant_slug),
        upcoming=db.get_appointments(tenant_slug, upcoming_only=True, limit=5),
        tenant_slug=tenant_slug,
        tenants=db.list_tenants(),
    )


@app.route("/dashboard/switch/<slug>")
def switch_tenant(slug):
    redir = _require_admin()
    if redir:
        return redir
    # Allowlist: only alphanumeric + hyphen/underscore
    if re.fullmatch(r"[a-zA-Z0-9_-]{1,50}", slug):
        if any(t["slug"] == slug for t in db.list_tenants()):
            session["tenant"] = slug
    return redirect(url_for("dashboard"))


# ── Inventory ─────────────────────────────────────────────────────────────

@app.route("/inventory")
def inventory():
    redir = _require_admin()
    if redir:
        return redir
    tenant_slug = session.get("tenant", config.DEFAULT_TENANT)
    return render_template(
        "inventory.html",
        items=db.get_inventory(tenant_slug),
        low_stock=db.get_low_stock(tenant_slug),
        tenant_slug=tenant_slug,
    )


@app.route("/inventory/save", methods=["POST"])
def inventory_save():
    redir = _require_admin()
    if redir:
        return redir
    tenant_slug = session.get("tenant", config.DEFAULT_TENANT)
    try:
        db.upsert_product(
            tenant_slug,
            product_name=request.form["product_name"].strip(),
            category=request.form.get("category", "general"),
            quantity=int(request.form.get("quantity", 0)),
            unit=request.form.get("unit", "pieces"),
            buy_price=float(request.form.get("buy_price", 0)),
            sell_price=float(request.form.get("sell_price", 0)),
            reorder_level=int(request.form.get("reorder_level", 10)),
            supplier=request.form.get("supplier", ""),
        )
        flash("Product save ho gaya.", "success")
    except Exception as exc:
        flash(f"Error: {exc}", "error")
    return redirect(url_for("inventory"))


# ── Appointments ───────────────────────────────────────────────────────────

@app.route("/appointments")
def appointments():
    redir = _require_admin()
    if redir:
        return redir
    tenant_slug = session.get("tenant", config.DEFAULT_TENANT)
    all_apts = db.get_appointments(tenant_slug, upcoming_only=False, limit=50)
    return render_template(
        "appointments.html",
        appointments=[a for a in all_apts if a["status"] == "booked"],
        tenant_slug=tenant_slug,
    )


@app.route("/appointments/cancel/<int:apt_id>", methods=["POST"])
def cancel_apt(apt_id):
    redir = _require_admin()
    if redir:
        return redir
    tenant_slug = session.get("tenant", config.DEFAULT_TENANT)
    db.cancel_appointment(apt_id, tenant_slug)
    flash("Appointment cancel ho gayi.", "success")
    return redirect(url_for("appointments"))


# ── Knowledge base ─────────────────────────────────────────────────────────

@app.route("/knowledge")
def knowledge():
    redir = _require_admin()
    if redir:
        return redir
    tenant_slug = session.get("tenant", config.DEFAULT_TENANT)
    return render_template(
        "knowledge.html",
        docs=db.get_knowledge_docs(tenant_slug),
        tenant_slug=tenant_slug,
    )


@app.route("/knowledge/save", methods=["POST"])
def knowledge_save():
    redir = _require_admin()
    if redir:
        return redir
    tenant_slug = session.get("tenant", config.DEFAULT_TENANT)
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    tags = request.form.get("tags", "").strip()
    if title and content:
        db.upsert_knowledge_doc(tenant_slug, title, content, tags)
        flash("Document save ho gaya.", "success")
    else:
        flash("Title aur content zaroor bhariein.", "error")
    return redirect(url_for("knowledge"))


@app.route("/knowledge/delete/<int:doc_id>", methods=["POST"])
def knowledge_delete(doc_id):
    redir = _require_admin()
    if redir:
        return redir
    tenant_slug = session.get("tenant", config.DEFAULT_TENANT)
    db.delete_knowledge_doc(doc_id, tenant_slug)
    flash("Document delete ho gaya.", "success")
    return redirect(url_for("knowledge"))


# ── Settings ───────────────────────────────────────────────────────────────

@app.route("/settings", methods=["GET", "POST"])
def settings():
    redir = _require_admin()
    if redir:
        return redir
    tenant_slug = session.get("tenant", config.DEFAULT_TENANT)
    tenant = db.get_tenant(tenant_slug) or {}
    if request.method == "POST":
        f = request.form
        with db.get_db() as conn:
            conn.execute(
                "UPDATE tenants SET name=?, city=?, business_type=?, "
                "owner_phone=?, owner_email=?, easypaisa_number=?, "
                "jazzcash_number=?, bank_title=?, bank_iban=?, "
                "notify_email=? WHERE slug=?",
                (
                    f.get("name", ""), f.get("city", "Karachi"),
                    f.get("business_type", "retail"),
                    f.get("owner_phone", ""), f.get("owner_email", ""),
                    f.get("easypaisa_number", ""),
                    f.get("jazzcash_number", ""),
                    f.get("bank_title", ""), f.get("bank_iban", ""),
                    f.get("notify_email", ""), tenant_slug,
                )
            )
        flash("Settings save ho gayi.", "success")
        return redirect(url_for("settings"))
    return render_template(
        "settings.html", tenant=tenant, tenant_slug=tenant_slug
    )


# ── Chat widget API ────────────────────────────────────────────────────────

@app.route("/chat", methods=["POST"])
@limiter.limit("60 per minute")
def chat():
    data = request.get_json(force=True) or {}
    message = str(data.get("message", "")).strip()[:1000]
    phone = str(data.get("phone", "web-user"))
    tenant_slug = str(data.get("tenant", config.DEFAULT_TENANT))
    if not message:
        return jsonify({"response": "Kuch likhein please."})
    try:
        return jsonify({"response": process_message(phone, message, tenant_slug)})
    except Exception:
        traceback.print_exc()
        return jsonify({"response": "Kuch ghalat hua. *menu* likhein."})


# ── REST API ───────────────────────────────────────────────────────────────

@app.route("/api/message", methods=["POST"])
@limiter.limit("120 per minute")
def api_message():
    """JSON API for external CRM / app integration.

    Body: {"phone": "...", "message": "...", "tenant": "..."}
    Response: {"response": "...", "intent": "..."}
    """
    data = request.get_json(force=True) or {}
    phone = str(data.get("phone", "api-user")).strip()
    message = str(data.get("message", "")).strip()[:1000]
    tenant_slug = str(data.get("tenant", config.DEFAULT_TENANT)).strip()
    if not message:
        return jsonify({"error": "message field required"}), 400
    try:
        from bazaarbot.nlp.rag_engine import get_engine
        engine = get_engine()
        engine.load_tenant_docs(tenant_slug)
        intent, _ = engine.answer(message.lower())
        response = process_message(phone, message, tenant_slug)
        return jsonify({"response": response, "intent": intent})
    except Exception:
        traceback.print_exc()
        return jsonify({"error": "internal error"}), 500


# ── WhatsApp webhook ───────────────────────────────────────────────────────

@app.route("/webhook", methods=["GET", "POST"])
@app.route("/webhook/", methods=["GET", "POST"])
@limiter.limit("120 per minute")
def webhook():
    try:
        payload = request.form if request.method == "POST" else request.args

        # Meta-style hub challenge (cross-provider compatibility)
        if request.method == "GET" and payload.get("hub.mode") == "subscribe":
            token = config.WEBHOOK_VERIFY_TOKEN
            if token and payload.get("hub.verify_token") == token:
                # Sanitize challenge: only allow alphanumeric characters,
                # then return as plain-text (not HTML) to prevent XSS.
                raw = str(payload.get("hub.challenge", ""))
                safe = re.sub(r"[^a-zA-Z0-9]", "", raw)[:128]
                from flask import make_response
                resp_obj = make_response(safe)
                resp_obj.content_type = "text/plain; charset=utf-8"
                return resp_obj, 200
            return "forbidden", 403

        if request.method == "GET" and not payload.get("Body"):
            return "OK", 200

        incoming = _extract_text(payload)[:1000]
        from_number = payload.get("From", "").replace("whatsapp:", "")
        print(f"📨 {from_number}: {incoming}")

        response_text = process_message(
            from_number, incoming, config.DEFAULT_TENANT
        )
        resp = MessagingResponse()
        resp.message(response_text)
        return str(resp), 200, {"Content-Type": "text/xml"}

    except Exception as exc:
        print(f"❌ Webhook error: {exc}")
        traceback.print_exc()
        resp = MessagingResponse()
        resp.message("Maafi — kuch masla hua. *menu* likhein.")
        return str(resp), 200, {"Content-Type": "text/xml"}


# ── Health ─────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "BazaarBot", "version": "1.0.0"})
