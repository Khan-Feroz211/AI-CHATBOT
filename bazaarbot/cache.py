"""Redis cache layer for BazaarBot.

Provides a thin, gracefully-degrading wrapper around Redis so that any
Redis downtime never causes the application to error — callers simply
receive ``None`` on a miss and ``False`` on a failed write.

Key namespaces
--------------
``inventory:<tenant_slug>``       — full inventory list, TTL 5 min
``tenant:<tenant_slug>``          — tenant config dict, TTL 10 min
``session:<tenant_slug>:<phone>`` — bot conversation state, TTL 30 min
"""
import json
import logging
from typing import Any

import redis as redis_lib

from bazaarbot.config import Config

logger = logging.getLogger(__name__)

# Module-level singleton — lazily initialised on first use.
_client: redis_lib.Redis | None = None


def get_redis() -> redis_lib.Redis:
    """Return (and lazily create) the module-level Redis client.

    Uses a single persistent connection pool configured with short
    socket timeouts so that a Redis outage surfaces quickly and the
    caller can fall back to the DB.
    """
    global _client
    if _client is None:
        _client = redis_lib.from_url(
            Config.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
    return _client


# ── Low-level helpers ─────────────────────────────────────────────────────

def cache_get(key: str) -> Any | None:
    """Retrieve a JSON-serialised value from Redis.

    Returns ``None`` when the key is absent *or* when Redis is
    unavailable — callers should treat ``None`` as a cache miss and
    fall through to the database.  Never raises.
    """
    try:
        raw = get_redis().get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.warning("cache_get(%s) failed: %s", key, exc)
        return None


def cache_set(
    key: str,
    value: Any,
    ttl_seconds: int = 300,
) -> bool:
    """Store *value* as JSON in Redis with a TTL.

    Returns ``True`` on success, ``False`` on any failure.  Never raises.
    """
    try:
        get_redis().setex(key, ttl_seconds, json.dumps(value))
        return True
    except Exception as exc:
        logger.warning("cache_set(%s) failed: %s", key, exc)
        return False


def cache_delete(key: str) -> None:
    """Delete a Redis key, silently ignoring any errors."""
    try:
        get_redis().delete(key)
    except Exception as exc:
        logger.warning("cache_delete(%s) failed: %s", key, exc)


# ── Key builders ──────────────────────────────────────────────────────────

def cache_key_inventory(tenant_slug: str) -> str:
    return f"inventory:{tenant_slug}"


def cache_key_tenant(tenant_slug: str) -> str:
    return f"tenant:{tenant_slug}"


def cache_key_session(tenant_slug: str, phone: str) -> str:
    return f"session:{tenant_slug}:{phone}"


# ── Inventory cache helpers ───────────────────────────────────────────────

def get_cached_inventory(tenant_slug: str) -> list[dict] | None:
    """Return the cached inventory list for *tenant_slug*, or ``None``.

    Cache TTL: 5 minutes.
    """
    return cache_get(cache_key_inventory(tenant_slug))


def set_cached_inventory(
    tenant_slug: str,
    inventory: list[dict],
) -> None:
    """Write *inventory* to the Redis cache (TTL 5 minutes)."""
    cache_set(cache_key_inventory(tenant_slug), inventory, ttl_seconds=300)


def invalidate_inventory_cache(tenant_slug: str) -> None:
    """Bust the inventory cache for *tenant_slug*.

    Must be called whenever any product is created, updated, or deleted
    so that the next read fetches fresh data from the database.
    """
    cache_delete(cache_key_inventory(tenant_slug))


# ── Session cache helpers ─────────────────────────────────────────────────

def get_cached_session(tenant_slug: str, phone: str) -> dict | None:
    """Return the cached bot session, or ``None``.

    Cache TTL: 30 minutes (active conversation window).
    """
    return cache_get(cache_key_session(tenant_slug, phone))


def set_cached_session(
    tenant_slug: str,
    phone: str,
    session: dict,
) -> None:
    """Store *session* in Redis (TTL 30 minutes)."""
    cache_set(
        cache_key_session(tenant_slug, phone),
        session,
        ttl_seconds=1800,
    )


def invalidate_session_cache(tenant_slug: str, phone: str) -> None:
    """Bust the session cache for a specific user."""
    cache_delete(cache_key_session(tenant_slug, phone))


# ── Tenant cache helpers ──────────────────────────────────────────────────

def get_cached_tenant(tenant_slug: str) -> dict | None:
    """Return the cached tenant config, or ``None``.

    Cache TTL: 10 minutes.
    """
    return cache_get(cache_key_tenant(tenant_slug))


def set_cached_tenant(tenant_slug: str, tenant: dict) -> None:
    """Store *tenant* config in Redis (TTL 10 minutes)."""
    cache_set(cache_key_tenant(tenant_slug), tenant, ttl_seconds=600)


def invalidate_tenant_cache(tenant_slug: str) -> None:
    """Bust the tenant config cache."""
    cache_delete(cache_key_tenant(tenant_slug))


# ── Health check ──────────────────────────────────────────────────────────

def health_check() -> dict:
    """Ping Redis and return a status dict.

    Returns ``{"status": "ok"}`` when reachable, or
    ``{"status": "error", "error": "<message>"}`` when not.
    """
    try:
        get_redis().ping()
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
