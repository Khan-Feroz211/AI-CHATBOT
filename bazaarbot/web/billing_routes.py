"""Billing API endpoints for BazaarBot SaaS subscription management.

Endpoints:
    GET  /api/billing/plans               — All plans (public, optional JWT)
    GET  /api/billing/usage               — Current tenant usage (JWT required)
    POST /api/billing/checkout            — Initiate payment checkout (JWT required)
    POST /api/billing/jazzcash/callback   — JazzCash payment callback (no auth)
    POST /api/billing/easypaisa/callback  — Easypaisa payment callback (no auth)
    POST /api/billing/cancel              — Cancel subscription (JWT required)
    GET  /api/billing/history             — Last 50 billing events (JWT required)
"""
import hashlib
import hmac as _hmac
import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bazaarbot.billing.middleware import get_db, get_tenant_subscription
from bazaarbot.billing.payment_service import (
    activate_subscription,
    create_easypaisa_checkout,
    create_jazzcash_checkout,
    verify_jazzcash_callback,
)
from bazaarbot.billing.plan_config import FREE_TRIAL_MESSAGES, PLANS, get_plan
from bazaarbot.config import Config
from bazaarbot.db.billing_models import BillingEvent, Subscription

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])

# ── Phone number validation ────────────────────────────────────────────────
# Pakistani mobile: +92 followed by a network prefix starting with 3 and
# 9 more digits.  Examples: +923001234567, +923451234567
_PHONE_RE = re.compile(r"^\+923[0-9]{9}$")


# ── JWT auth helpers ───────────────────────────────────────────────────────

_bearer_required = HTTPBearer()
_bearer_optional = HTTPBearer(auto_error=False)


def _require_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_required),
) -> dict:
    """Require a valid Bearer JWT. Raises HTTP 401 if missing or invalid."""
    from bazaarbot.auth.auth_service import decode_access_token

    return decode_access_token(credentials.credentials)


def _optional_jwt(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_optional),
) -> Optional[dict]:
    """Optionally parse a Bearer JWT. Returns ``None`` when absent or invalid."""
    if not credentials:
        return None
    try:
        from bazaarbot.auth.auth_service import decode_access_token

        return decode_access_token(credentials.credentials)
    except HTTPException:
        return None


# ── Easypaisa callback signature verification ─────────────────────────────


def _verify_easypaisa_callback(params: dict) -> bool:
    """Verify the Easypaisa callback signature using ``EASYPAISA_HASH_KEY``.

    Easypaisa computes HMAC-SHA256 over ``key=value`` pairs (sorted
    alphabetically, non-empty only) joined with ``&``, keyed on the
    merchant hash key.

    If ``EASYPAISA_HASH_KEY`` is not configured the verification is skipped
    (sandbox / dev mode) and ``True`` is returned so test flows still work.
    """
    hash_key = Config.EASYPAISA_HASH_KEY
    if not hash_key:
        logger.debug(
            "Easypaisa callback: EASYPAISA_HASH_KEY not configured — "
            "skipping signature verification (sandbox mode)"
        )
        return True

    params_copy = dict(params)
    # Easypaisa sends the hash under one of several field names depending on
    # the API version / integration type.
    received = (
        params_copy.pop("hashValue", "")
        or params_copy.pop("hash", "")
        or params_copy.pop("encryptedHashRequest", "")
    )

    sorted_keys = sorted(params_copy.keys())
    hash_string = "&".join(
        f"{k}={params_copy[k]}"
        for k in sorted_keys
        if str(params_copy.get(k, "")) != ""
    )
    # HMAC-SHA256 is the signing primitive required by the Easypaisa API spec.
    # It is NOT used for password storage.  # noqa: S324
    calculated = _hmac.new(  # lgtm[py/weak-sensitive-data-hashing]
        hash_key.encode("utf-8"),
        hash_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return _hmac.compare_digest(received.lower(), calculated.lower())


# ── GET /api/billing/plans ────────────────────────────────────────────────


@router.get("/plans")
async def list_plans(
    jwt: Optional[dict] = Depends(_optional_jwt),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Return all subscription plans with features and pricing.

    When a valid JWT is provided the plan the tenant is currently on will
    have ``is_current: true``.  Authentication is optional — the pricing
    page must always be publicly accessible.
    """
    current_plan_id: Optional[str] = None
    if jwt:
        tenant_slug: str = jwt.get("sub", "")
        if tenant_slug:
            sub = await get_tenant_subscription(tenant_slug, db)
            current_plan_id = sub.plan if sub else None

    result = []
    for plan in PLANS.values():
        result.append(
            {
                "plan_id": plan.plan_id,
                "name": plan.name,
                "price_pkr": plan.price_pkr,
                "price_display": f"PKR {plan.price_pkr:,}/month",
                "message_limit": plan.message_limit,
                "channels": plan.channels_allowed,
                "llm_enabled": plan.llm_enabled,
                "features": plan.features,
                "is_current": plan.plan_id == current_plan_id,
                "is_popular": plan.plan_id == "business",
            }
        )
    return JSONResponse(result)


# ── GET /api/billing/usage ────────────────────────────────────────────────


@router.get("/usage")
async def get_usage(
    jwt: dict = Depends(_require_jwt),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Return current message usage and subscription details for the tenant.

    Free-trial tenants get a live count of inbound messages for the current
    calendar month.  Paid tenants read the denormalised ``message_count``
    field that is incremented after each processed message.
    """
    from bazaarbot.models import Message

    tenant_slug: str = jwt.get("sub", "")
    sub = await get_tenant_subscription(tenant_slug, db)
    now = datetime.now(timezone.utc)

    if sub is None:
        # Free trial — count inbound messages in the current UTC calendar month.
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        used: int = (
            await db.scalar(
                select(func.count())
                .select_from(Message)
                .where(
                    Message.tenant_slug == tenant_slug,
                    Message.direction == "in",
                    Message.created_at >= month_start,
                )
            )
            or 0
        )
        limit = FREE_TRIAL_MESSAGES
        return JSONResponse(
            {
                "plan": "free_trial",
                "plan_name": "Free Trial",
                "messages_used": used,
                "message_limit": limit,
                "percent_used": round(used / limit * 100, 1) if limit else 0.0,
                "channels_allowed": ["whatsapp"],
                "llm_enabled": False,
                "period_end": None,
                "days_remaining": None,
                "price_pkr": 0,
            }
        )

    plan = get_plan(sub.plan)

    # channels_allowed is stored as JSON string in the DB column.
    try:
        channels: list = json.loads(sub.channels_allowed)
    except (TypeError, json.JSONDecodeError):
        channels = plan.channels_allowed

    days_remaining: Optional[int] = None
    if sub.period_end:
        days_remaining = max(0, (sub.period_end - now).days)

    pct = (
        round(sub.message_count / sub.message_limit * 100, 1)
        if sub.message_limit > 0
        else 0.0
    )

    return JSONResponse(
        {
            "plan": sub.plan,
            "plan_name": plan.name,
            "messages_used": sub.message_count,
            "message_limit": sub.message_limit,
            "percent_used": pct,
            "channels_allowed": channels,
            "llm_enabled": bool(sub.llm_enabled),
            "period_end": sub.period_end.isoformat() if sub.period_end else None,
            "days_remaining": days_remaining,
            "price_pkr": sub.price_pkr,
        }
    )


# ── POST /api/billing/checkout ────────────────────────────────────────────


@router.post("/checkout")
async def create_checkout(
    request: Request,
    jwt: dict = Depends(_require_jwt),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Initiate a JazzCash or Easypaisa payment checkout for a subscription.

    Body (JSON):
        plan         — ``"starter"`` | ``"business"`` | ``"pro"``
        gateway      — ``"jazzcash"`` | ``"easypaisa"``
        phone_number — Pakistani mobile in ``+923XXXXXXXXX`` format
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body.",
        )

    plan_id = str(data.get("plan", "")).strip().lower()
    gateway = str(data.get("gateway", "")).strip().lower()
    phone_number = str(data.get("phone_number", "")).strip()

    # Validate plan
    if plan_id not in PLANS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid plan '{plan_id}'. "
                f"Valid options: {', '.join(PLANS)}."
            ),
        )

    # Validate gateway
    if gateway not in ("jazzcash", "easypaisa"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid gateway. Choose 'jazzcash' or 'easypaisa'.",
        )

    # Validate Pakistani mobile number (+92XXXXXXXXXX)
    if not _PHONE_RE.match(phone_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid phone number format. "
                "Use: +923XXXXXXXXX (e.g. +923001234567)"
            ),
        )

    tenant_slug: str = jwt.get("sub", "")

    # Prevent re-purchasing the same plan
    sub = await get_tenant_subscription(tenant_slug, db)
    if sub and sub.plan == plan_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Aap already '{plan_id}' plan par hain.",
        )

    plan = get_plan(plan_id)

    if gateway == "jazzcash":
        result = await create_jazzcash_checkout(
            tenant_slug=tenant_slug,
            plan_id=plan_id,
            amount_pkr=plan.price_pkr,
            phone_number=phone_number,
        )
    else:  # easypaisa
        result = await create_easypaisa_checkout(
            tenant_slug=tenant_slug,
            plan_id=plan_id,
            amount_pkr=plan.price_pkr,
            phone_number=phone_number,
        )

    return JSONResponse(result)


# ── POST /api/billing/jazzcash/callback ───────────────────────────────────


@router.post("/jazzcash/callback")
async def jazzcash_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Handle the JazzCash MWALLET payment callback.

    JazzCash POSTs form-encoded data here after the user completes (or
    fails / cancels) a payment.  This endpoint is the ``pp_ReturnURL``
    that the user's browser is redirected to after payment.

    Important: always returns HTTP 200 to JazzCash — a non-2xx response
    causes JazzCash to retry the callback indefinitely.
    """
    try:
        form_data = await request.form()
        params = dict(form_data)

        response_code = params.get("pp_ResponseCode", "")
        txn_ref = params.get("pp_TxnRefNo", "")
        # Tenant slug was encoded in pp_BillReference as "billRef-{slug}"
        bill_ref = params.get("pp_BillReference", "")
        tenant_slug = bill_ref.replace("billRef-", "").strip() or "unknown"
        description = params.get("pp_Description", "")

        logger.info(
            "JazzCash callback: code=%s ref=%s tenant=%s",
            response_code,
            txn_ref,
            tenant_slug,
        )

        # ── Signature verification ────────────────────────────────────────
        if not verify_jazzcash_callback(dict(params)):
            logger.warning(
                "JazzCash callback: invalid signature for ref=%s tenant=%s",
                txn_ref,
                tenant_slug,
            )
            return JSONResponse(
                {"status": "invalid_signature"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Extract plan from description string "BazaarBot {plan_id} Plan"
        plan_id = "starter"
        desc_lower = description.lower()
        for pid in ("pro", "business", "starter"):
            if pid in desc_lower:
                plan_id = pid
                break

        if response_code == "000":
            # ── Payment successful ────────────────────────────────────────
            await activate_subscription(
                db=db,
                tenant_slug=tenant_slug,
                plan_id=plan_id,
                gateway="jazzcash",
                gateway_ref=txn_ref,
            )

            # Record the payment transaction separately from the subscription
            # lifecycle event that activate_subscription already appends.
            try:
                amount_paisas = int(params.get("pp_Amount", "0"))
            except (ValueError, TypeError):
                amount_paisas = 0

            payment_event = BillingEvent(
                tenant_slug=tenant_slug,
                event_type="payment_succeeded",
                plan=plan_id,
                amount_pkr=amount_paisas // 100,
                gateway="jazzcash",
                # Omit sensitive fields from the stored payload.
                gateway_data=json.dumps(
                    {
                        k: v
                        for k, v in params.items()
                        if k not in ("pp_Password", "pp_SecuredHash")
                    }
                ),
            )
            db.add(payment_event)

            logger.info(
                "JazzCash payment succeeded: tenant=%s plan=%s ref=%s",
                tenant_slug,
                plan_id,
                txn_ref,
            )
            return RedirectResponse(
                url=f"{Config.FRONTEND_URL}/billing/success",
                status_code=status.HTTP_302_FOUND,
            )

        else:
            # ── Payment failed or cancelled ───────────────────────────────
            logger.warning(
                "JazzCash payment failed: code=%s tenant=%s ref=%s",
                response_code,
                tenant_slug,
                txn_ref,
            )
            failure_event = BillingEvent(
                tenant_slug=tenant_slug,
                event_type="payment_failed",
                plan=plan_id,
                amount_pkr=0,
                gateway="jazzcash",
                gateway_data=json.dumps(
                    {
                        "response_code": response_code,
                        "txn_ref": txn_ref,
                        **{
                            k: v
                            for k, v in params.items()
                            if k not in ("pp_Password", "pp_SecuredHash")
                        },
                    }
                ),
            )
            db.add(failure_event)
            return RedirectResponse(
                url=f"{Config.FRONTEND_URL}/billing/failed",
                status_code=status.HTTP_302_FOUND,
            )

    except Exception as exc:
        # Log but return 200 to prevent JazzCash from retrying the callback.
        logger.error("JazzCash callback internal error: %s", exc, exc_info=True)
        return JSONResponse(
            {"status": "error", "message": "Internal error logged."},
            status_code=status.HTTP_200_OK,
        )


# ── POST /api/billing/easypaisa/callback ──────────────────────────────────


@router.post("/easypaisa/callback")
async def easypaisa_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Handle the Easypaisa Mobile Account payment callback.

    Easypaisa POSTs form-encoded data here after payment completion.
    Always returns HTTP 200 to prevent Easypaisa from retrying.
    """
    try:
        form_data = await request.form()
        params = dict(form_data)

        response_code = params.get("responseCode", "")
        order_id = params.get("orderId", "")
        # Extract tenant slug from customerReferenceNumber or fall back to
        # mobileAccountNo (not ideal but keeps flows working in sandbox).
        tenant_slug = (
            params.get("customerReferenceNumber", "").strip()
            or params.get("mobileAccountNo", "").strip()
            or "unknown"
        )
        description = params.get("description", "")

        logger.info(
            "Easypaisa callback: code=%s order=%s tenant=%s",
            response_code,
            order_id,
            tenant_slug,
        )

        # ── Signature verification ────────────────────────────────────────
        if not _verify_easypaisa_callback(dict(params)):
            logger.warning(
                "Easypaisa callback: invalid signature for order=%s tenant=%s",
                order_id,
                tenant_slug,
            )
            return JSONResponse(
                {"status": "invalid_signature"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Extract plan from description string "BazaarBot {plan_id} Plan"
        plan_id = "starter"
        desc_lower = description.lower()
        for pid in ("pro", "business", "starter"):
            if pid in desc_lower:
                plan_id = pid
                break

        if response_code == "0000":
            # ── Payment successful ────────────────────────────────────────
            await activate_subscription(
                db=db,
                tenant_slug=tenant_slug,
                plan_id=plan_id,
                gateway="easypaisa",
                gateway_ref=order_id,
            )

            try:
                amount_pkr = int(float(params.get("transactionAmount", "0")))
            except (ValueError, TypeError):
                amount_pkr = 0

            payment_event = BillingEvent(
                tenant_slug=tenant_slug,
                event_type="payment_succeeded",
                plan=plan_id,
                amount_pkr=amount_pkr,
                gateway="easypaisa",
                gateway_data=json.dumps(params),
            )
            db.add(payment_event)

            logger.info(
                "Easypaisa payment succeeded: tenant=%s plan=%s order=%s",
                tenant_slug,
                plan_id,
                order_id,
            )
            return RedirectResponse(
                url=f"{Config.FRONTEND_URL}/billing/success",
                status_code=status.HTTP_302_FOUND,
            )

        else:
            # ── Payment failed or cancelled ───────────────────────────────
            logger.warning(
                "Easypaisa payment failed: code=%s tenant=%s order=%s",
                response_code,
                tenant_slug,
                order_id,
            )
            failure_event = BillingEvent(
                tenant_slug=tenant_slug,
                event_type="payment_failed",
                plan=plan_id,
                amount_pkr=0,
                gateway="easypaisa",
                gateway_data=json.dumps(
                    {
                        "response_code": response_code,
                        "order_id": order_id,
                    }
                ),
            )
            db.add(failure_event)
            return RedirectResponse(
                url=f"{Config.FRONTEND_URL}/billing/failed",
                status_code=status.HTTP_302_FOUND,
            )

    except Exception as exc:
        # Return 200 to prevent Easypaisa from retrying the callback.
        logger.error("Easypaisa callback internal error: %s", exc, exc_info=True)
        return JSONResponse(
            {"status": "error", "message": "Internal error logged."},
            status_code=status.HTTP_200_OK,
        )


# ── POST /api/billing/cancel ──────────────────────────────────────────────


@router.post("/cancel")
async def cancel_subscription(
    jwt: dict = Depends(_require_jwt),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Cancel the tenant's active subscription.

    Sets ``status = "cancelled"`` and ``cancelled_at = now()``.  The tenant
    retains full access until ``period_end`` (end of the current billing
    cycle).  The response includes ``access_until`` so the frontend can
    display a clear message.
    """
    tenant_slug: str = jwt.get("sub", "")
    sub = await get_tenant_subscription(tenant_slug, db)

    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Koi active subscription nahi mili.",
        )

    now = datetime.now(timezone.utc)
    sub.status = "cancelled"
    sub.cancelled_at = now

    cancel_event = BillingEvent(
        tenant_slug=tenant_slug,
        event_type="subscription_cancelled",
        plan=sub.plan,
        amount_pkr=0,
        gateway=sub.gateway,
        gateway_data=json.dumps({"cancelled_at": now.isoformat()}),
    )
    db.add(cancel_event)

    access_until_str: Optional[str] = None
    if sub.period_end:
        access_until_str = sub.period_end.strftime("%d %b %Y")

    logger.info(
        "Subscription cancelled: tenant=%s plan=%s access_until=%s",
        tenant_slug,
        sub.plan,
        access_until_str,
    )

    return JSONResponse(
        {
            "status": "cancelled",
            "message": (
                f"Aapka {sub.plan} plan cancel ho gaya. "
                f"Access {access_until_str or 'billing period'} tak rehega."
            ),
            "plan": sub.plan,
            "access_until": sub.period_end.isoformat() if sub.period_end else None,
        }
    )


# ── GET /api/billing/history ──────────────────────────────────────────────


@router.get("/history")
async def billing_history(
    jwt: dict = Depends(_require_jwt),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Return the last 50 billing events for the authenticated tenant.

    Results are ordered newest-first so clients can display a reverse-
    chronological feed without sorting client-side.
    """
    tenant_slug: str = jwt.get("sub", "")

    result = await db.execute(
        select(BillingEvent)
        .where(BillingEvent.tenant_slug == tenant_slug)
        .order_by(BillingEvent.created_at.desc())
        .limit(50)
    )
    events = result.scalars().all()

    return JSONResponse([e.to_dict() for e in events])
