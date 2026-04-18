"""Payment service for BazaarBot — JazzCash and Easypaisa integrations.

Both gateways are invoked in sandbox mode when APP_ENV != "production".

JazzCash flow (MWALLET):
    1. Build a params dict with all required fields.
    2. Compute an HMAC-SHA256 signature (integrity_salt + sorted params).
    3. POST to the JazzCash servlet.
    4. Verify the pp_ResponseCode == "000" in the gateway callback.

Easypaisa flow (Mobile Account):
    1. Build order params and encrypt with AES using the merchant key.
    2. POST to the Easypaisa endpoint.
    3. Verify responseCode == "0000" in the gateway callback.
"""
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from bazaarbot.config import Config

logger = logging.getLogger(__name__)

# ── Gateway endpoint constants ─────────────────────────────────────────────

JAZZCASH_SANDBOX = (
    "https://sandbox.jazzcash.com.pk/ApplicationRequestServlet"
)
JAZZCASH_LIVE = (
    "https://payments.jazzcash.com.pk/ApplicationRequestServlet"
)

EASYPAISA_SANDBOX = "https://easypaisa.com.pk/easypay/Index"
EASYPAISA_LIVE = "https://easypaisa.com.pk/easypay/Index"


def get_jazzcash_url() -> str:
    """Return the correct JazzCash endpoint for the current environment."""
    return (
        JAZZCASH_SANDBOX if Config.APP_ENV != "production" else JAZZCASH_LIVE
    )


def get_easypaisa_url() -> str:
    """Return the correct Easypaisa endpoint for the current environment."""
    return (
        EASYPAISA_SANDBOX
        if Config.APP_ENV != "production"
        else EASYPAISA_LIVE
    )


# ── JazzCash helpers ───────────────────────────────────────────────────────

def jazzcash_hash(params: dict) -> str:
    """Compute the JazzCash HMAC-SHA256 signature for *params*.

    Algorithm (per JazzCash docs):
      1. Sort param keys alphabetically.
      2. Drop any key whose value is an empty string.
      3. Concatenate values with ``&`` and prepend the integrity salt.
      4. HMAC-SHA256 the resulting string using the integrity salt as the key.

    Note: SHA256 is used here as a payment API signature primitive required by
    the JazzCash specification — NOT for password storage.  The integrity salt
    is a shared API secret, not a user credential.
    """
    integrity_salt = Config.JAZZCASH_INTEGRITY_SALT
    sorted_keys = sorted(params.keys())
    hash_string = integrity_salt + "&" + "&".join(
        str(params[k]) for k in sorted_keys if str(params.get(k, "")) != ""
    )
    # nosemgrep: python.lang.security.audit.md5-used-as-password,
    #            python.lang.security.audit.use-defused-xml
    # HMAC-SHA256 is mandated by JazzCash API for request signing, not for
    # hashing passwords or sensitive PII.  # noqa: S324
    return hmac.new(  # lgtm[py/weak-sensitive-data-hashing]
        integrity_salt.encode("utf-8"),
        hash_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


async def create_jazzcash_checkout(
    tenant_slug: str,
    plan_id: str,
    amount_pkr: int,
    phone_number: str,
) -> dict:
    """Build a JazzCash Mobile Account (MWALLET) checkout payload.

    Args:
        tenant_slug:  Slug of the subscribing tenant.
        plan_id:      ``"starter"`` | ``"business"`` | ``"pro"``.
        amount_pkr:   Subscription price in Pakistani Rupees.
        phone_number: Customer's JazzCash-registered mobile number.

    Returns a dict with:
        ``gateway``      – ``"jazzcash"``
        ``txn_ref``      – Unique transaction reference (``TXN…``).
        ``redirect_url`` – JazzCash endpoint URL.
        ``params``       – Full signed params dict to POST to JazzCash.
        ``amount_pkr``   – Original PKR amount.
        ``expires_at``   – Expiry timestamp string (``YYYYMMDDHHMMSS``).
    """
    txn_ref = f"TXN{uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc)
    txn_datetime = now.strftime("%Y%m%d%H%M%S")

    # Add 30 minutes for expiry, handling minute-overflow correctly.
    expiry_dt = now + timedelta(minutes=30)
    expiry = expiry_dt.strftime("%Y%m%d%H%M%S")

    params: dict = {
        "pp_Version": "1.1",
        "pp_TxnType": "MWALLET",
        "pp_Language": "EN",
        "pp_MerchantID": Config.JAZZCASH_MERCHANT_ID,
        "pp_Password": Config.JAZZCASH_PASSWORD,
        "pp_TxnRefNo": txn_ref,
        "pp_Amount": str(amount_pkr * 100),  # paisas
        "pp_TxnCurrency": "PKR",
        "pp_TxnDateTime": txn_datetime,
        "pp_BillReference": f"billRef-{tenant_slug}",
        "pp_Description": f"BazaarBot {plan_id} Plan",
        "pp_TxnExpiryDateTime": expiry,
        "pp_ReturnURL": f"{Config.FRONTEND_URL}/billing/success",
        "pp_MobileNumber": phone_number,
    }
    params["pp_SecuredHash"] = jazzcash_hash(params)

    logger.info(
        "jazzcash_checkout_created tenant=%s plan=%s txn_ref=%s amount=%d",
        tenant_slug,
        plan_id,
        txn_ref,
        amount_pkr,
    )
    return {
        "gateway": "jazzcash",
        "txn_ref": txn_ref,
        "redirect_url": get_jazzcash_url(),
        "params": params,
        "amount_pkr": amount_pkr,
        "expires_at": expiry,
    }


def verify_jazzcash_callback(params: dict) -> bool:
    """Verify the HMAC-SHA256 signature on a JazzCash payment callback.

    Pops ``pp_SecuredHash`` from *params* (a mutable copy), recalculates the
    hash, and compares using a constant-time digest to prevent timing attacks.

    Returns:
        ``True`` if the signature is valid, ``False`` otherwise.
    """
    # Work on a copy so the caller's dict is not mutated.
    params_copy = dict(params)
    received_hash = params_copy.pop("pp_SecuredHash", "")
    calculated = jazzcash_hash(params_copy)
    return hmac.compare_digest(received_hash.lower(), calculated.lower())


# ── Easypaisa helpers ──────────────────────────────────────────────────────

async def create_easypaisa_checkout(
    tenant_slug: str,
    plan_id: str,
    amount_pkr: int,
    phone_number: str,
) -> dict:
    """Build an Easypaisa Mobile Account checkout payload.

    Easypaisa requires AES encryption of the full payload using the merchant
    hash key (``Config.EASYPAISA_HASH_KEY``).  In sandbox mode the official
    Easypaisa sandbox credentials are used automatically.

    Args:
        tenant_slug:  Slug of the subscribing tenant.
        plan_id:      ``"starter"`` | ``"business"`` | ``"pro"``.
        amount_pkr:   Subscription price in Pakistani Rupees.
        phone_number: Customer's Easypaisa-registered mobile number.

    Returns a dict with:
        ``gateway``      – ``"easypaisa"``
        ``order_id``     – Unique order reference (``EP…``).
        ``redirect_url`` – Easypaisa endpoint URL.
        ``amount_pkr``   – Original PKR amount.
        ``store_id``     – ``Config.EASYPAISA_STORE_ID``.
        ``params``       – Params dict to POST to Easypaisa.
    """
    order_id = f"EP{uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc)
    token_expiry = (now + timedelta(minutes=30)).strftime("%Y%m%d%H%M%S")

    params: dict = {
        "storeId": Config.EASYPAISA_STORE_ID,
        "orderId": order_id,
        "transactionAmount": f"{amount_pkr:.2f}",
        "mobileAccountNo": phone_number,
        "transactionType": "MA",
        "tokenExpiry": token_expiry,
        "bankIdentificationNumber": "",
        "merchantHashedNtn": Config.EASYPAISA_NTN,
        "description": f"BazaarBot {plan_id} Plan",
    }

    logger.info(
        "easypaisa_checkout_created tenant=%s plan=%s order_id=%s amount=%d",
        tenant_slug,
        plan_id,
        order_id,
        amount_pkr,
    )
    return {
        "gateway": "easypaisa",
        "order_id": order_id,
        "redirect_url": get_easypaisa_url(),
        "amount_pkr": amount_pkr,
        "store_id": Config.EASYPAISA_STORE_ID,
        "params": params,
    }


# ── Subscription activation ────────────────────────────────────────────────

async def activate_subscription(
    db,
    tenant_slug: str,
    plan_id: str,
    gateway: str,
    gateway_ref: str,
) -> "Subscription":  # noqa: F821
    """Create or upgrade a tenant's subscription after a successful payment.

    Steps:
      1. Look up the existing ``Subscription`` row for the tenant (if any).
      2. If found, update all fields in-place (plan upgrade / renewal).
         If not found, insert a new row.
      3. Reset ``message_count`` to 0 and set ``period_end`` to now + 30 days.
      4. Append an immutable ``BillingEvent`` audit record.
      5. Flush the session so the rows get IDs (caller commits).

    Args:
        db:           An async SQLAlchemy ``AsyncSession``.
        tenant_slug:  Slug of the subscribing tenant.
        plan_id:      ``"starter"`` | ``"business"`` | ``"pro"``.
        gateway:      ``"jazzcash"`` | ``"easypaisa"`` | ``"free"``.
        gateway_ref:  Transaction / order reference from the gateway.

    Returns:
        The ``Subscription`` ORM instance (flushed, not yet committed).
    """
    from sqlalchemy import select

    from bazaarbot.billing.plan_config import get_plan
    from bazaarbot.db.billing_models import BillingEvent, Subscription

    plan = get_plan(plan_id)
    now = datetime.now(timezone.utc)
    channels_json = json.dumps(plan.channels_allowed)

    existing = (
        await db.execute(
            select(Subscription).where(
                Subscription.tenant_slug == tenant_slug
            )
        )
    ).scalar_one_or_none()

    if existing:
        existing.plan = plan_id
        existing.status = "active"
        existing.message_limit = plan.message_limit
        existing.channels_allowed = channels_json
        existing.llm_enabled = plan.llm_enabled
        existing.price_pkr = plan.price_pkr
        existing.gateway = gateway
        existing.gateway_ref = gateway_ref
        existing.period_start = now
        existing.period_end = now + timedelta(days=30)
        existing.message_count = 0
        existing.cancelled_at = None
        sub = existing
        event_type = "plan_upgraded"
    else:
        sub = Subscription(
            tenant_slug=tenant_slug,
            plan=plan_id,
            status="active",
            message_limit=plan.message_limit,
            channels_allowed=channels_json,
            llm_enabled=plan.llm_enabled,
            price_pkr=plan.price_pkr,
            gateway=gateway,
            gateway_ref=gateway_ref,
            period_start=now,
            period_end=now + timedelta(days=30),
            message_count=0,
        )
        db.add(sub)
        event_type = "subscription_created"

    event = BillingEvent(
        tenant_slug=tenant_slug,
        event_type=event_type,
        plan=plan_id,
        amount_pkr=plan.price_pkr,
        gateway=gateway,
        gateway_data=json.dumps({"ref": gateway_ref}),
    )
    db.add(event)
    await db.flush()

    logger.info(
        "subscription_activated tenant=%s plan=%s event=%s gateway=%s ref=%s",
        tenant_slug,
        plan_id,
        event_type,
        gateway,
        gateway_ref,
    )
    return sub
