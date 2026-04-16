"""BazaarBot web dashboard — FastAPI routes.

Mirrors every route in bazaarbot/web/app.py (Flask).
Run via APP_BACKEND=fastapi in .env / environment.
"""
import os
import re
import traceback
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from twilio.twiml.messaging_response import MessagingResponse

from bazaarbot.config import config
from bazaarbot import database as db
from bazaarbot.bot.intent_router import process_message

_templates_dir = os.path.join(os.path.dirname(__file__), "templates")
_static_dir = os.path.join(os.path.dirname(__file__), "static")

# ── Rate limiter ──────────────────────────────────────────────────────────
# Convert "30 per minute" → "30/minute" for slowapi.
# Fall back to "30/minute" if the env value doesn't match the expected format.
_raw_rate = config.RATE_LIMIT
_rate_str = _raw_rate.replace(" per ", "/") if " per " in _raw_rate else _raw_rate
limiter = Limiter(key_func=get_remote_address, default_limits=[_rate_str])


@asynccontextmanager
async def _lifespan(application: FastAPI):
    """Run DB initialisation once at startup (FastAPI best practice)."""
    db.init_db()
    yield


app = FastAPI(title="BazaarBot", lifespan=_lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY)
app.mount("/static", StaticFiles(directory=_static_dir), name="static")

templates = Jinja2Templates(directory=_templates_dir)

# ── Jinja2 url_for — maps Flask route names to paths ─────────────────────
_ROUTE_MAP = {
    "index": "/",
    "login": "/login",
    "logout": "/logout",
    "dashboard": "/dashboard",
    "switch_tenant": "/dashboard/switch/{slug}",
    "inventory": "/inventory",
    "inventory_save": "/inventory/save",
    "appointments": "/appointments",
    "cancel_apt": "/appointments/cancel/{apt_id}",
    "knowledge": "/knowledge",
    "knowledge_save": "/knowledge/save",
    "knowledge_delete": "/knowledge/delete/{doc_id}",
    "settings": "/settings",
    "static": "/static/{filename}",
}


def _template_url_for(endpoint: str, **kwargs) -> str:
    path = _ROUTE_MAP.get(endpoint, "/")
    for k, v in kwargs.items():
        path = path.replace(f"{{{k}}}", str(v))
    return path


# Override the Starlette built-in so Flask-style url_for() calls in templates work.
templates.env.globals["url_for"] = _template_url_for

# ── DB lazy init ──────────────────────────────────────────────────────────
# (handled in _lifespan above; middleware removed)

# ── Helpers ──────────────────────────────────────────────────────────────

def _flash(request: Request, message: str, category: str = "info") -> None:
    """Store a flash message in the session for the next template render."""
    flashes = list(request.session.get("_flashes", []))
    flashes.append({"category": category, "message": message})
    request.session["_flashes"] = flashes


def _tmpl(template_name: str, request: Request, **ctx) -> HTMLResponse:
    """Render a Jinja2 template with session, flash, and request context.

    Provides get_flashed_messages() compatible with Flask's implementation
    so existing templates work without modification.
    """
    session = request.session

    def get_flashed_messages(with_categories=False):
        flashes = list(session.get("_flashes", []))
        session["_flashes"] = []
        if with_categories:
            return [(f["category"], f["message"]) for f in flashes]
        return [f["message"] for f in flashes]

    return templates.TemplateResponse(template_name, {
        "request": request,
        "session": session,
        "get_flashed_messages": get_flashed_messages,
        **ctx,
    })


def _require_admin(request: Request) -> Optional[RedirectResponse]:
    if not request.session.get("admin"):
        return RedirectResponse(url="/login", status_code=302)
    return None


def _extract_text(payload: dict) -> str:
    for key in ("Body", "ButtonText", "ButtonPayload", "ListTitle"):
        v = payload.get(key, "")
        if v and str(v).strip():
            return str(v).strip()
    return ""


async def _parse_json(request: Request) -> dict:
    """Parse JSON body; return empty dict on any error."""
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


# ── Auth ─────────────────────────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return _tmpl("login.html", request)


@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request):
    form = await request.form()
    if str(form.get("password", "")) == config.ADMIN_PASSWORD:
        request.session["admin"] = True
        request.session["tenant"] = config.DEFAULT_TENANT
        return RedirectResponse(url="/dashboard", status_code=302)
    _flash(request, "Galat password. Dobara koshish karein.", "error")
    return _tmpl("login.html", request)


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)


# ── Public ────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return _tmpl("index.html", request)


# ── Dashboard ─────────────────────────────────────────────────────────────

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    redir = _require_admin(request)
    if redir:
        return redir
    tenant_slug = request.session.get("tenant", config.DEFAULT_TENANT)
    return _tmpl(
        "dashboard.html", request,
        analytics=db.get_analytics(tenant_slug),
        messages=db.get_recent_messages(tenant_slug, limit=30),
        low_stock=db.get_low_stock(tenant_slug),
        upcoming=db.get_appointments(tenant_slug, upcoming_only=True, limit=5),
        tenant_slug=tenant_slug,
        tenants=db.list_tenants(),
    )


@app.get("/dashboard/switch/{slug}")
async def switch_tenant(request: Request, slug: str):
    redir = _require_admin(request)
    if redir:
        return redir
    if re.fullmatch(r"[a-zA-Z0-9_-]{1,50}", slug):
        if any(t["slug"] == slug for t in db.list_tenants()):
            request.session["tenant"] = slug
    return RedirectResponse(url="/dashboard", status_code=302)


# ── Inventory ─────────────────────────────────────────────────────────────

@app.get("/inventory", response_class=HTMLResponse)
async def inventory(request: Request):
    redir = _require_admin(request)
    if redir:
        return redir
    tenant_slug = request.session.get("tenant", config.DEFAULT_TENANT)
    return _tmpl(
        "inventory.html", request,
        items=db.get_inventory(tenant_slug),
        low_stock=db.get_low_stock(tenant_slug),
        tenant_slug=tenant_slug,
    )


@app.post("/inventory/save")
async def inventory_save(request: Request):
    redir = _require_admin(request)
    if redir:
        return redir
    tenant_slug = request.session.get("tenant", config.DEFAULT_TENANT)
    form = await request.form()
    try:
        db.upsert_product(
            tenant_slug,
            product_name=str(form.get("product_name", "")).strip(),
            category=str(form.get("category", "general")),
            quantity=int(form.get("quantity", 0)),
            unit=str(form.get("unit", "pieces")),
            buy_price=float(form.get("buy_price", 0)),
            sell_price=float(form.get("sell_price", 0)),
            reorder_level=int(form.get("reorder_level", 10)),
            supplier=str(form.get("supplier", "")),
        )
        _flash(request, "Product save ho gaya.", "success")
    except Exception as exc:
        _flash(request, f"Error: {exc}", "error")
    return RedirectResponse(url="/inventory", status_code=302)


# ── Appointments ───────────────────────────────────────────────────────────

@app.get("/appointments", response_class=HTMLResponse)
async def appointments(request: Request):
    redir = _require_admin(request)
    if redir:
        return redir
    tenant_slug = request.session.get("tenant", config.DEFAULT_TENANT)
    all_apts = db.get_appointments(tenant_slug, upcoming_only=False, limit=50)
    return _tmpl(
        "appointments.html", request,
        appointments=[a for a in all_apts if a["status"] == "booked"],
        tenant_slug=tenant_slug,
    )


@app.post("/appointments/cancel/{apt_id}")
async def cancel_apt(request: Request, apt_id: int):
    redir = _require_admin(request)
    if redir:
        return redir
    tenant_slug = request.session.get("tenant", config.DEFAULT_TENANT)
    db.cancel_appointment(apt_id, tenant_slug)
    _flash(request, "Appointment cancel ho gayi.", "success")
    return RedirectResponse(url="/appointments", status_code=302)


# ── Knowledge base ─────────────────────────────────────────────────────────

@app.get("/knowledge", response_class=HTMLResponse)
async def knowledge(request: Request):
    redir = _require_admin(request)
    if redir:
        return redir
    tenant_slug = request.session.get("tenant", config.DEFAULT_TENANT)
    return _tmpl(
        "knowledge.html", request,
        docs=db.get_knowledge_docs(tenant_slug),
        tenant_slug=tenant_slug,
    )


@app.post("/knowledge/save")
async def knowledge_save(request: Request):
    redir = _require_admin(request)
    if redir:
        return redir
    tenant_slug = request.session.get("tenant", config.DEFAULT_TENANT)
    form = await request.form()
    title = str(form.get("title", "")).strip()
    content = str(form.get("content", "")).strip()
    tags = str(form.get("tags", "")).strip()
    if title and content:
        db.upsert_knowledge_doc(tenant_slug, title, content, tags)
        _flash(request, "Document save ho gaya.", "success")
    else:
        _flash(request, "Title aur content zaroor bhariein.", "error")
    return RedirectResponse(url="/knowledge", status_code=302)


@app.post("/knowledge/delete/{doc_id}")
async def knowledge_delete(request: Request, doc_id: int):
    redir = _require_admin(request)
    if redir:
        return redir
    tenant_slug = request.session.get("tenant", config.DEFAULT_TENANT)
    db.delete_knowledge_doc(doc_id, tenant_slug)
    _flash(request, "Document delete ho gaya.", "success")
    return RedirectResponse(url="/knowledge", status_code=302)


# ── Settings ───────────────────────────────────────────────────────────────

@app.get("/settings", response_class=HTMLResponse)
async def settings_get(request: Request):
    redir = _require_admin(request)
    if redir:
        return redir
    tenant_slug = request.session.get("tenant", config.DEFAULT_TENANT)
    tenant = db.get_tenant(tenant_slug) or {}
    return _tmpl("settings.html", request, tenant=tenant, tenant_slug=tenant_slug)


@app.post("/settings")
async def settings_post(request: Request):
    redir = _require_admin(request)
    if redir:
        return redir
    tenant_slug = request.session.get("tenant", config.DEFAULT_TENANT)
    f = await request.form()
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
    _flash(request, "Settings save ho gayi.", "success")
    return RedirectResponse(url="/settings", status_code=302)


# ── Chat widget API ────────────────────────────────────────────────────────

@app.post("/chat")
@limiter.limit("60/minute")
async def chat(request: Request):
    data = await _parse_json(request)
    message = str(data.get("message", "")).strip()[:1000]
    phone = str(data.get("phone", "web-user"))
    tenant_slug = str(data.get("tenant", config.DEFAULT_TENANT))
    if not message:
        return JSONResponse({"response": "Kuch likhein please."})
    try:
        return JSONResponse({"response": process_message(phone, message, tenant_slug)})
    except Exception:
        traceback.print_exc()
        return JSONResponse({"response": "Kuch ghalat hua. *menu* likhein."})


# ── REST API ───────────────────────────────────────────────────────────────

@app.post("/api/message")
@limiter.limit("120/minute")
async def api_message(request: Request):
    """JSON API for external CRM / app integration.

    Body: {"phone": "...", "message": "...", "tenant": "..."}
    Response: {"response": "...", "intent": "..."}
    """
    data = await _parse_json(request)
    phone = str(data.get("phone", "api-user")).strip()
    message = str(data.get("message", "")).strip()[:1000]
    tenant_slug = str(data.get("tenant", config.DEFAULT_TENANT)).strip()
    if not message:
        return JSONResponse({"error": "message field required"}, status_code=400)
    try:
        from bazaarbot.nlp.rag_engine import get_engine
        engine = get_engine()
        engine.load_tenant_docs(tenant_slug)
        intent, _ = engine.answer(message.lower())
        response = process_message(phone, message, tenant_slug)
        return JSONResponse({"response": response, "intent": intent})
    except Exception:
        traceback.print_exc()
        return JSONResponse({"error": "internal error"}, status_code=500)


# ── WhatsApp webhook ───────────────────────────────────────────────────────

async def _webhook_handler(request: Request) -> Response:
    """Shared handler for GET /webhook and POST /webhook (with trailing slash)."""
    try:
        if request.method == "POST":
            form_data = await request.form()
            payload = dict(form_data)
        else:
            payload = dict(request.query_params)

        # Meta-style hub challenge (cross-provider compatibility)
        if request.method == "GET" and payload.get("hub.mode") == "subscribe":
            token = config.WEBHOOK_VERIFY_TOKEN
            if token and payload.get("hub.verify_token") == token:
                try:
                    challenge_int = int(payload.get("hub.challenge", 0))
                except (ValueError, TypeError):
                    challenge_int = 0
                return Response(
                    content=str(challenge_int),
                    media_type="text/plain; charset=utf-8",
                )
            return Response(content="forbidden", status_code=403)

        if request.method == "GET" and not payload.get("Body"):
            return Response(content="OK")

        incoming = _extract_text(payload)[:1000]
        from_number = payload.get("From", "").replace("whatsapp:", "")
        print(f"📨 {from_number}: {incoming}")

        response_text = process_message(from_number, incoming, config.DEFAULT_TENANT)
        resp = MessagingResponse()
        resp.message(response_text)
        return Response(content=str(resp), media_type="text/xml")

    except Exception as exc:
        print(f"❌ Webhook error: {exc}")
        traceback.print_exc()
        resp = MessagingResponse()
        resp.message("Maafi — kuch masla hua. *menu* likhein.")
        return Response(content=str(resp), media_type="text/xml")


@app.api_route("/webhook", methods=["GET", "POST"])
@limiter.limit("120/minute")
async def webhook(request: Request):
    return await _webhook_handler(request)


@app.api_route("/webhook/", methods=["GET", "POST"], include_in_schema=False)
@limiter.limit("120/minute")
async def webhook_slash(request: Request):
    return await _webhook_handler(request)


# ── Health ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health(request: Request):
    return JSONResponse({"status": "ok", "service": "BazaarBot", "version": "1.0.0"})
