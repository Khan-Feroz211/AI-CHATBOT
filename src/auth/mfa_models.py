"""MFA/2FA database models."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    TEXT,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from src.core.models import Base, Client


class MFASetup(Base):
    """User MFA setup and secrets."""

    __tablename__ = "mfa_setup"

    id = Column(Integer, primary_key=True)
    client_id = Column(
        Integer, ForeignKey("clients.id"), unique=True, nullable=False, index=True
    )

    # TOTP secrets (encrypted in application layer)
    totp_secret_encrypted = Column(String(255), nullable=True)  # Encrypted secret key

    # Microsoft Authenticator
    microsoft_enabled = Column(Boolean, default=False)
    microsoft_qr_generated = Column(DateTime, nullable=True)

    # Oracle Authenticator
    oracle_enabled = Column(Boolean, default=False)
    oracle_qr_generated = Column(DateTime, nullable=True)

    # Backup codes
    backup_codes_encrypted = Column(
        TEXT, nullable=True
    )  # JSON array of encrypted codes

    # Status
    mfa_enabled = Column(Boolean, default=False)
    mfa_verified = Column(
        Boolean, default=False
    )  # User has verified with authenticator
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", backref="mfa_setup")

    def __repr__(self):
        return f"<MFASetup {self.client_id}>"


class MFAAttempt(Base):
    """MFA authentication attempt log."""

    __tablename__ = "mfa_attempts"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    phone_number = Column(String(20), nullable=False, index=True)

    attempt_type = Column(String(20))  # 'totp_verify', 'backup_code', 'initial_setup'
    success = Column(Boolean, default=False)

    # Details about attempt
    authenticator_type = Column(String(50), nullable=True)  # 'microsoft', 'oracle'
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    error_reason = Column(String(255), nullable=True)  # Why it failed

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<MFAAttempt {self.phone_number} - {self.attempt_type}>"


class MFASession(Base):
    """Active MFA session tracking."""

    __tablename__ = "mfa_sessions"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    phone_number = Column(String(20), nullable=False, index=True)

    # Tokens
    session_token = Column(String(500), unique=True, nullable=False, index=True)
    refresh_token = Column(String(500), nullable=True)
    mfa_verified = Column(Boolean, default=False)

    # Session details
    authenticator_type = Column(String(50))  # 'microsoft', 'oracle'
    ip_address = Column(String(45))
    device_info = Column(String(500))  # Device/browser info
    user_agent = Column(String(255))

    # Status
    is_active = Column(Boolean, default=True, index=True)

    # Expiration
    expires_at = Column(DateTime, nullable=False, index=True)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def is_expired(self):
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at

    def is_valid(self):
        """Check if session is valid and not expired."""
        return not self.is_expired() and self.mfa_verified and self.is_active

    def __repr__(self):
        return f"<MFASession {self.phone_number}>"


class MFALockout(Base):
    """Track failed MFA attempts for rate limiting."""

    __tablename__ = "mfa_lockout"

    id = Column(Integer, primary_key=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)

    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True, index=True)
    last_attempt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def is_locked(self):
        """Check if phone is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until

    def __repr__(self):
        return f"<MFALockout {self.phone_number}>"


class MFABackupCode(Base):
    """Single-use backup codes for emergency access."""

    __tablename__ = "mfa_backup_codes"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)

    code_hash = Column(String(255), unique=True, nullable=False)  # Hashed code
    used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    generated_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MFABackupCode {self.client_id}>"
