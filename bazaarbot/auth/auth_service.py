"""JWT + bcrypt authentication service for BazaarBot.

Provides password hashing, JWT creation/decoding, API key generation,
and tenant lookup by API key.  All crypto operations are stateless so
this module can safely be imported from any context.
"""
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, status
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bazaarbot.config import config
from bazaarbot.models import Tenant

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS: int = config.JWT_EXPIRE_HOURS
API_KEY_LENGTH: int = 32  # bytes → ~43 URL-safe base64 chars


# ── Password helpers ──────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password* (work-factor 12)."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT helpers ───────────────────────────────────────────────────────────

def create_access_token(
    tenant_slug: str,
    user_id: int,
    role: str,
) -> str:
    """Create a signed JWT access token for a regular user / admin."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": tenant_slug,
        "user_id": user_id,
        "role": role,
        "exp": now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
        "iat": now,
        "type": "access",
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token.

    Raises:
        HTTPException 401 — if the token is expired or invalid.

    Returns:
        The decoded payload dict.
    """
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_superadmin_token() -> str:
    """Create a special long-lived token for the superadmin.

    The token has a 7-day expiry and is scoped to the ``__superadmin__``
    pseudo-tenant with the ``superadmin`` role.  It should only be used
    for bootstrapping or emergency access — regular admin operations
    should use per-tenant tokens.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "__superadmin__",
        "user_id": 0,
        "role": "superadmin",
        "exp": now + timedelta(days=7),
        "iat": now,
        "type": "access",
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=ALGORITHM)


# ── API key helpers ───────────────────────────────────────────────────────

def generate_api_key() -> str:
    """Generate a cryptographically secure URL-safe API key."""
    return secrets.token_urlsafe(API_KEY_LENGTH)


# ── Database helpers ──────────────────────────────────────────────────────

async def get_tenant_by_api_key(
    api_key: str,
    db: AsyncSession,
) -> Tenant | None:
    """Look up a Tenant by its ``api_key`` column.

    Returns the ``Tenant`` ORM object if found and active, or ``None``
    if the key does not exist or the tenant is inactive.
    """
    result = await db.scalar(
        select(Tenant).where(
            Tenant.api_key == api_key,
            Tenant.is_active.is_(True),
        )
    )
    return result
