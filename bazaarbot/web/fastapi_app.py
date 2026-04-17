"""BazaarBot web dashboard — FastAPI routes.

Mirrors every route in bazaarbot/web/app.py (Flask).
Run via APP_BACKEND=fastapi in .env / environment.
"""
import logging
import os
import re
import traceback
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from twilio.twiml.messaging_response import MessagingResponse

from bazaarbot.config import config, Config
from bazaarbot import database as db
from bazaarbot.bot.intent_router import process_message, process_message_async

logger = logging.getLogger(__name__)

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
    """Run DB initialisation and optional NLP warm-up at startup."""
    db.init_db()

    # LangChain RAG warm-up (optional, controlled by env flag)
    from bazaarbot.nlp.langchain_rag import load_knowledge_base
    if Config.USE_LANGCHAIN_RAG:
        load_knowledge_base()
        print("LangChain RAG: loaded")
    else:
        print("LangChain RAG: disabled (TF-IDF mode)")

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
    from bazaarbot.cache import get_cached_inventory, set_cached_inventory
    cached = get_cached_inventory(tenant_slug)
    if cached is not None:
        items = cached
    else:
        items = db.get_inventory(tenant_slug)
        set_cached_inventory(tenant_slug, items)
    return _tmpl(
        "inventory.html", request,
        items=items,
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
        # upsert_product already busts the cache via database_pg shim,
        # but we also bust here for the case where the FastAPI route
        # bypasses the shim in a future refactor.
        from bazaarbot.cache import invalidate_inventory_cache
        invalidate_inventory_cache(tenant_slug)
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
        if Config.USE_LLM_FALLBACK:
            reply = await process_message_async(message, phone, tenant_slug,
                                                channel="web")
        else:
            reply = process_message(phone, message, tenant_slug)
        return JSONResponse({"response": reply})
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
        if Config.USE_LLM_FALLBACK:
            response = await process_message_async(message, phone, tenant_slug,
                                                   channel="api")
        else:
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

        tenant_slug = config.DEFAULT_TENANT
        lower = incoming.lower().strip()

        # ── Fast-path: direct order command → offload to Celery worker ──────
        # Matches "order <product name> <qty>" sent directly (not via multi-turn
        # session).  Celery task handles product lookup, stock validation, DB
        # write, and confirmation email, so the webhook returns immediately.
        if lower.startswith("order "):
            parts = lower.split()
            if len(parts) >= 3:
                try:
                    quantity = int(parts[-1])
                    product_name = " ".join(parts[1:-1]).title()
                except ValueError:
                    # Last token is not a number — fall through to normal handler
                    product_name = ""
                    quantity = 0
                if product_name and quantity > 0:
                    from bazaarbot.tasks.order_tasks import process_order
                    process_order.delay(
                        tenant_slug,
                        from_number,
                        product_name,
                        quantity,
                        "pending",
                    )
                    logger.info(
                        "Order task queued for tenant=%s product='%s' qty=%d",
                        tenant_slug, product_name, quantity,
                    )
                    resp = MessagingResponse()
                    resp.message(
                        "✅ Aapka order process ho raha hai!\n"
                        "Thodi der mein confirm message milega.\n"
                        "*menu* likhein waapis jaane ke liye."
                    )
                    return Response(content=str(resp), media_type="text/xml")
                else:
                    # Parsing failed — return a helpful format hint
                    resp = MessagingResponse()
                    resp.message(
                        "⚠️ Order format galat hai.\n"
                        "Sahi format: *order [product] [quantity]*\n"
                        "Misaal: order Atta 5"
                    )
                    return Response(content=str(resp), media_type="text/xml")

        # ── Default path: synchronous intent router ───────────────────────
        if Config.USE_LLM_FALLBACK:
            response_text = await process_message_async(
                incoming, from_number, tenant_slug, channel="whatsapp"
            )
        else:
            response_text = process_message(from_number, incoming, tenant_slug)
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


# ── NLP diagnostic endpoints ───────────────────────────────────────────────

# Bearer-token extractor (optional — 401 if missing/invalid)
_bearer_scheme = HTTPBearer()


def _require_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict:
    """FastAPI dependency that validates a Bearer JWT and returns its payload."""
    from bazaarbot.auth.auth_service import decode_access_token
    return decode_access_token(credentials.credentials)


@app.get("/api/nlp/status")
async def nlp_status(request: Request):
    """Return current NLP pipeline configuration.  No auth required."""
    from bazaarbot.nlp.rag_engine import get_engine, INTENT_PATTERNS
    from bazaarbot.nlp.langchain_rag import retrieve_langchain as _lc
    from bazaarbot.nlp import langchain_rag as _lc_mod
    from bazaarbot.nlp.llm_service import is_llm_enabled

    engine = get_engine()

    # Count knowledge docs available in TF-IDF engine
    knowledge_doc_count = len(engine._docs) if engine._docs else 0

    # Determine LangChain status by checking module-level vectorstore
    lc_active = _lc_mod._vectorstore is not None

    return JSONResponse({
        "tfidf_rag": "active",
        "langchain_rag": "active" if lc_active else "disabled",
        "llm_fallback": "active" if is_llm_enabled() else "disabled",
        "llm_provider": Config.LLM_PROVIDER,
        "intent_count": len(INTENT_PATTERNS),
        "knowledge_docs": knowledge_doc_count,
    })


@app.post("/api/nlp/test")
async def nlp_test(
    request: Request,
    _payload: dict = Depends(_require_jwt),
):
    """Run the full NLP pipeline on a test query and return diagnostics.

    Body: {"query": str, "tenant_slug": str}
    Requires a valid Bearer JWT token.
    """
    data = await _parse_json(request)
    query = str(data.get("query", "")).strip()[:500]
    tenant_slug = str(data.get("tenant_slug", config.DEFAULT_TENANT)).strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'query' field is required.",
        )

    from bazaarbot.nlp.rag_engine import get_engine
    from bazaarbot.nlp.langchain_rag import retrieve_langchain
    from bazaarbot.nlp.llm_service import is_llm_enabled, call_llm

    engine = get_engine()
    try:
        engine.load_tenant_docs(tenant_slug)
    except Exception:
        pass

    # TF-IDF scoring
    intent, confidence = engine._classify_intent_scored(query.lower())

    # Sync TF-IDF response (the existing answer() path)
    _, tfidf_response = engine.answer(query.lower())

    # LangChain context retrieval
    langchain_context = retrieve_langchain(query)

    # LLM response (only if enabled and confidence is below threshold)
    llm_response: Optional[str] = None
    path_taken = "tfidf"

    if is_llm_enabled() and (
        confidence < Config.LLM_CONFIDENCE_THRESHOLD or intent == "unknown"
    ):
        try:
            tenant_data = db.get_tenant(tenant_slug) or {}
            llm_response = await call_llm(
                query=query,
                context=langchain_context or engine.retrieve(query),
                tenant_data=tenant_data,
            )
            if llm_response:
                path_taken = "llm"
        except Exception as exc:
            traceback.print_exc()

    if path_taken == "tfidf" and langchain_context:
        path_taken = "rag"

    # Determine the final response that would be sent to the user
    if llm_response:
        final_response = llm_response
    elif tfidf_response:
        final_response = tfidf_response
    elif langchain_context:
        final_response = (
            "🤖 *BazaarBot Assistant*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"{langchain_context[:400]}\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Aur madad ke liye *menu* likhein."
        )
    else:
        final_response = (
            "Maafi chahta hoon, samajh nahi aaya. Please dobara likhein."
        )

    return JSONResponse({
        "intent": intent,
        "confidence": round(confidence, 4),
        "tfidf_response": tfidf_response,
        "langchain_context": langchain_context,
        "llm_response": llm_response,
        "final_response": final_response,
        "path_taken": path_taken,
    })


# ── Health ─────────────────────────────────────────────────────────────────

def _check_celery_workers() -> dict:
    """Inspect connected Celery workers with a short timeout.

    Returns ``{"status": "ok", "workers": N}`` when at least one worker
    is online, ``{"status": "no_workers", "workers": 0}`` when the broker
    is reachable but idle, or ``{"status": "unavailable"}`` on any error.
    """
    try:
        from bazaarbot.celery_app import celery as _celery
        active = _celery.control.inspect(timeout=2.0).active()
        if active:
            return {"status": "ok", "workers": len(active)}
        return {"status": "no_workers", "workers": 0}
    except Exception:
        return {"status": "unavailable"}


@app.get("/health")
async def health(request: Request):
    from bazaarbot.cache import health_check as redis_health
    return JSONResponse({
        "status":   "ok",
        "service":  "BazaarBot",
        "version":  "1.0.0",
        "redis":    redis_health(),
        "celery":   _check_celery_workers(),
    })


# ── Task status ────────────────────────────────────────────────────────────

@app.get("/api/tasks/status/{task_id}")
async def task_status(request: Request, task_id: str):
    """Return the current status of a Celery task.

    No authentication required — callers receive the task's status string
    and, once complete, its serialised result.

    ``status`` values mirror Celery's AsyncResult: ``PENDING``,
    ``STARTED``, ``SUCCESS``, ``FAILURE``, ``RETRY``, ``REVOKED``.
    """
    try:
        from celery.result import AsyncResult
        result = AsyncResult(task_id)
        return JSONResponse({
            "task_id": task_id,
            "status":  result.status,
            "result":  result.result if result.ready() else None,
        })
    except Exception as exc:
        logger.warning("task_status(%s) error: %s", task_id, exc)
        return JSONResponse(
            {"task_id": task_id, "status": "UNKNOWN", "result": None},
            status_code=500,
        )
