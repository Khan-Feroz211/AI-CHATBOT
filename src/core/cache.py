"""Redis cache setup with graceful fallback."""

from __future__ import annotations

import logging

import redis

from src.core.config import Config

logger = logging.getLogger(__name__)

_redis_client: redis.Redis | None = None


def init_redis(config: Config) -> redis.Redis | None:
    """Initialize Redis client from REDIS_URL with safe fallback."""
    global _redis_client

    if not config.REDIS_URL:
        logger.warning("REDIS_URL is not set. Continuing without Redis cache.")
        _redis_client = None
        return None

    try:
        client = redis.Redis.from_url(
            config.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=config.REDIS_CONNECT_TIMEOUT,
            socket_timeout=config.REDIS_READ_TIMEOUT,
            health_check_interval=30,
        )
        client.ping()
        _redis_client = client
        logger.info("Redis connection established")
    except redis.RedisError as exc:
        logger.exception("Redis unavailable. Running without cache. %s", exc)
        _redis_client = None

    return _redis_client


def get_redis() -> redis.Redis | None:
    return _redis_client
