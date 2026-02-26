"""Session management for MFA authentication."""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from jose import JWTError, jwt

from src.auth.mfa_models import MFASession
from src.core.database import get_session_context

logger = logging.getLogger(__name__)


class SessionConfig:
    """Session configuration."""

    # JWT configuration
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS = 24
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    # Session configuration
    SESSION_TIMEOUT_MINUTES = 30  # Inactivity timeout
    MFA_GRACE_PERIOD_MINUTES = 5  # Time to complete MFA after initial auth

    @staticmethod
    def get_secret_key() -> str:
        """Get JWT secret key from environment."""
        secret = os.getenv("JWT_SECRET_KEY")
        if not secret:
            raise ValueError("JWT_SECRET_KEY environment variable not set")
        return secret

    @staticmethod
    def get_encryption_key() -> bytes:
        """Get session encryption key."""
        key = os.getenv("SESSION_ENCRYPTION_KEY")
        if not key:
            # Generate default key if not set (development only)
            key = Fernet.generate_key().decode()
        return key.encode() if isinstance(key, str) else key


class SessionTokenManager:
    """Manage JWT tokens for authenticated sessions."""

    def __init__(self):
        """Initialize token manager."""
        self.secret_key = SessionConfig.get_secret_key()
        self.algorithm = SessionConfig.ALGORITHM

    def create_access_token(
        self,
        client_id: str,
        phone_number: str,
        mfa_verified: bool = False,
        additional_claims: Dict[str, Any] = None,
    ) -> str:
        """Create JWT access token.

        Args:
            client_id: Client ID
            phone_number: User's phone number
            mfa_verified: Whether MFA has been verified
            additional_claims: Extra claims to include

        Returns:
            JWT token string
        """
        expire = datetime.utcnow() + timedelta(
            hours=SessionConfig.ACCESS_TOKEN_EXPIRE_HOURS
        )

        claims = {
            "sub": str(client_id),
            "phone": phone_number,
            "mfa_verified": mfa_verified,
            "exp": expire,
            "iat": datetime.utcnow(),
            "token_type": "access",
            "jti": uuid.uuid4().hex,
        }

        if additional_claims:
            claims.update(additional_claims)

        token = jwt.encode(claims, self.secret_key, algorithm=self.algorithm)

        logger.info(f"Created access token for client {client_id}")
        return token

    def create_refresh_token(self, client_id: str, phone_number: str) -> str:
        """Create JWT refresh token.

        Args:
            client_id: Client ID
            phone_number: User's phone number

        Returns:
            JWT refresh token
        """
        expire = datetime.utcnow() + timedelta(
            days=SessionConfig.REFRESH_TOKEN_EXPIRE_DAYS
        )

        claims = {
            "sub": str(client_id),
            "phone": phone_number,
            "exp": expire,
            "iat": datetime.utcnow(),
            "token_type": "refresh",
            "jti": uuid.uuid4().hex,
        }

        token = jwt.encode(claims, self.secret_key, algorithm=self.algorithm)

        logger.info(f"Created refresh token for client {client_id}")
        return token

    def create_mfa_provisional_token(
        self,
        client_id: str,
        phone_number: str,
        expires_in_minutes: int = SessionConfig.MFA_GRACE_PERIOD_MINUTES,
    ) -> str:
        """Create provisional token for MFA completion.

        Token allows user to complete MFA setup before getting full access.

        Args:
            client_id: Client ID
            phone_number: User's phone
            expires_in_minutes: Expiration time

        Returns:
            JWT token
        """
        expire = datetime.utcnow() + timedelta(minutes=expires_in_minutes)

        claims = {
            "sub": str(client_id),
            "phone": phone_number,
            "mfa_required": True,
            "exp": expire,
            "iat": datetime.utcnow(),
            "token_type": "mfa_provisional",
            "jti": uuid.uuid4().hex,
        }

        token = jwt.encode(claims, self.secret_key, algorithm=self.algorithm)

        logger.info(f"Created MFA provisional token for client {client_id}")
        return token

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token.

        Args:
            token: JWT token string

        Returns:
            Token claims if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None

    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired.

        Args:
            token: JWT token

        Returns:
            True if expired, False otherwise
        """
        claims = self.verify_token(token)
        if not claims:
            return True

        exp_time = datetime.fromtimestamp(claims.get("exp", 0))
        return datetime.utcnow() > exp_time

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Create new access token from refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token or None if refresh token invalid
        """
        claims = self.verify_token(refresh_token)

        if not claims or claims.get("token_type") != "refresh":
            logger.warning("Invalid refresh token")
            return None

        return self.create_access_token(
            client_id=claims["sub"],
            phone_number=claims["phone"],
            mfa_verified=True,  # Refresh implies MFA already done
        )


class SessionManager:
    """Manage user sessions in database."""

    def __init__(self):
        """Initialize session manager."""
        self.token_manager = SessionTokenManager()
        self.encryption_key = SessionConfig.get_encryption_key()

    def create_session(
        self,
        client_id: str,
        phone_number: str,
        ip_address: str = None,
        device_info: str = None,
        mfa_verified: bool = False,
    ) -> Dict[str, Any]:
        """Create authenticated session.

        Args:
            client_id: Client ID
            phone_number: User's phone
            ip_address: Client IP address
            device_info: Device information
            mfa_verified: MFA completion status

        Returns:
            Dict with tokens and session info
        """
        access_token = self.token_manager.create_access_token(
            client_id, phone_number, mfa_verified
        )
        refresh_token = self.token_manager.create_refresh_token(client_id, phone_number)

        expire_time = datetime.utcnow() + timedelta(
            hours=SessionConfig.ACCESS_TOKEN_EXPIRE_HOURS
        )

        with get_session_context() as session:
            # Create database session record
            db_session = MFASession(
                client_id=client_id,
                phone_number=phone_number,
                session_token=access_token,
                refresh_token=refresh_token,
                ip_address=ip_address,
                device_info=device_info,
                mfa_verified=mfa_verified,
                expires_at=expire_time,
                created_at=datetime.utcnow(),
                is_active=True,
            )
            session.add(db_session)
            session.commit()

            logger.info(f"Created session for client {client_id} from IP {ip_address}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": SessionConfig.ACCESS_TOKEN_EXPIRE_HOURS * 3600,
            "mfa_verified": mfa_verified,
        }

    def validate_session(self, client_id: str, token: str) -> bool:
        """Validate active session.

        Args:
            client_id: Client ID
            token: Session token

        Returns:
            True if session valid, False otherwise
        """
        with get_session_context() as session:
            db_session = (
                session.query(MFASession)
                .filter(
                    MFASession.client_id == client_id,
                    MFASession.session_token == token,
                    MFASession.is_active == True,
                )
                .first()
            )

            if not db_session:
                return False

            # Check expiration
            if db_session.is_expired():
                db_session.is_active = False
                session.commit()
                return False

            return True

    def invalidate_session(self, client_id: str, token: str = None):
        """Invalidate user session.

        Args:
            client_id: Client ID
            token: Specific token to invalidate (None = all sessions)
        """
        with get_session_context() as session:
            query = session.query(MFASession).filter(MFASession.client_id == client_id)

            if token:
                query = query.filter(MFASession.session_token == token)

            sessions = query.all()
            for sess in sessions:
                sess.is_active = False

            session.commit()

            logger.info(f"Invalidated session(s) for client {client_id}")

    def get_active_sessions(self, client_id: str) -> list:
        """Get all active sessions for client.

        Args:
            client_id: Client ID

        Returns:
            List of active session info
        """
        with get_session_context() as session:
            sessions = (
                session.query(MFASession)
                .filter(MFASession.client_id == client_id, MFASession.is_active == True)
                .all()
            )

            return [
                {
                    "id": s.id,
                    "ip_address": s.ip_address,
                    "device_info": s.device_info,
                    "created_at": s.created_at.isoformat(),
                    "expires_at": s.expires_at.isoformat(),
                    "mfa_verified": s.mfa_verified,
                }
                for s in sessions
                if not s.is_expired()
            ]

    def refresh_session_token(
        self, client_id: str, refresh_token: str
    ) -> Optional[Dict]:
        """Refresh access token.

        Args:
            client_id: Client ID
            refresh_token: Valid refresh token

        Returns:
            New token info or None if refresh failed
        """
        # Verify token
        new_access_token = self.token_manager.refresh_access_token(refresh_token)
        if not new_access_token:
            return None

        # Update database record
        with get_session_context() as session:
            db_session = (
                session.query(MFASession)
                .filter(
                    MFASession.client_id == client_id,
                    MFASession.refresh_token == refresh_token,
                )
                .first()
            )

            if not db_session or db_session.is_expired():
                return None

            db_session.session_token = new_access_token
            db_session.updated_at = datetime.utcnow()
            session.commit()

            logger.info(f"Refreshed session token for client {client_id}")

        return {
            "access_token": new_access_token,
            "token_type": "Bearer",
            "expires_in": SessionConfig.ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        }

    def mark_mfa_verified(self, client_id: str, token: str):
        """Mark session as MFA verified.

        Args:
            client_id: Client ID
            token: Session token
        """
        with get_session_context() as session:
            db_session = (
                session.query(MFASession)
                .filter(
                    MFASession.client_id == client_id, MFASession.session_token == token
                )
                .first()
            )

            if db_session:
                db_session.mfa_verified = True
                db_session.updated_at = datetime.utcnow()
                session.commit()
                logger.info(f"Marked session as MFA verified for client {client_id}")


class DeviceFingerprint:
    """Generate device fingerprints for session security."""

    @staticmethod
    def generate(ip_address: str, user_agent: str) -> str:
        """Generate device fingerprint.

        Args:
            ip_address: Client IP
            user_agent: Browser/client user agent

        Returns:
            Device fingerprint hash
        """
        from hashlib import sha256

        fingerprint_data = f"{ip_address}:{user_agent}"
        return sha256(fingerprint_data.encode()).hexdigest()

    @staticmethod
    def verify(ip_address: str, user_agent: str, stored_fingerprint: str) -> bool:
        """Verify device fingerprint.

        Args:
            ip_address: Client IP
            user_agent: User agent
            stored_fingerprint: Stored fingerprint

        Returns:
            True if matches
        """
        current = DeviceFingerprint.generate(ip_address, user_agent)
        return current == stored_fingerprint
