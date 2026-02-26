"""Authentication and MFA module."""

from src.auth.mfa import (
    BackupCodeManager,
    MFARateLimiter,
    MFAService,
    TOTPEncryption,
    TOTPManager,
)
from src.auth.mfa_models import (
    MFAAttempt,
    MFABackupCode,
    MFALockout,
    MFASession,
    MFASetup,
)
from src.auth.qr_generator import QRCodeGenerator, WhatsAppQRSender

# Blueprint for Flask integration
from src.auth.routes import auth_bp
from src.auth.session import (
    DeviceFingerprint,
    SessionConfig,
    SessionManager,
    SessionTokenManager,
)

__all__ = [
    # MFA Services
    "MFAService",
    "TOTPManager",
    "BackupCodeManager",
    "MFARateLimiter",
    "TOTPEncryption",
    # Session Management
    "SessionManager",
    "SessionTokenManager",
    "SessionConfig",
    "DeviceFingerprint",
    # QR Generation
    "QRCodeGenerator",
    "WhatsAppQRSender",
    # Database Models
    "MFASetup",
    "MFAAttempt",
    "MFASession",
    "MFALockout",
    "MFABackupCode",
    # Flask Integration
    "auth_bp",
]
