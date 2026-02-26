"""MFA/2FA handler - TOTP implementation with Microsoft & Oracle Authenticator support."""

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import List, Tuple

import pyotp
from cryptography.fernet import Fernet

from src.auth.mfa_models import MFAAttempt, MFABackupCode, MFALockout, MFASetup
from src.core.database import get_session_context

logger = logging.getLogger(__name__)


class TOTPEncryption:
    """Handle encryption of TOTP secrets."""

    def __init__(self, encryption_key: str = None):
        """Initialize encryption.

        Args:
            encryption_key: Base64-encoded encryption key. If None, uses TOTP_ENCRYPTION_KEY env var.
        """
        if encryption_key is None:
            encryption_key = os.getenv(
                "TOTP_ENCRYPTION_KEY", Fernet.generate_key().decode()
            )

        self.cipher = Fernet(
            encryption_key.encode()
            if isinstance(encryption_key, str)
            else encryption_key
        )

    def encrypt_secret(self, secret: str) -> str:
        """Encrypt TOTP secret.

        Args:
            secret: PlainText TOTP secret

        Returns:
            Encrypted secret string
        """
        encrypted = self.cipher.encrypt(secret.encode())
        return encrypted.decode()

    def decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt TOTP secret.

        Args:
            encrypted_secret: Encrypted TOTP secret

        Returns:
            PlainText secret

        Raises:
            ValueError: If decryption fails
        """
        try:
            decrypted = self.cipher.decrypt(encrypted_secret.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt TOTP secret: {str(e)}")
            raise ValueError("Invalid or corrupted TOTP secret")


class TOTPManager:
    """TOTP generation and verification."""

    # Configuration
    TOTP_WINDOW = 1  # Allow 1 step tolerance (±30 seconds)
    TOTP_DIGITS = 6  # 6-digit codes
    TOTP_PERIOD = 30  # 30-second windows

    def __init__(self, encryption_key: str = None):
        """Initialize TOTP manager.

        Args:
            encryption_key: Encryption key for storing secrets
        """
        self.encryption = TOTPEncryption(encryption_key)

    def generate_secret(self) -> str:
        """Generate new TOTP secret key.

        Returns:
            32-character base32-encoded secret
        """
        secret = pyotp.random_base32()
        logger.info(f"Generated new TOTP secret")
        return secret

    def get_totp_uri(
        self, secret: str, name: str, issuer: str = "WhatsApp Inventory Bot"
    ) -> str:
        """Generate otpauth:// URI for QR code.

        Compatible with:
        - Microsoft Authenticator
        - Google Authenticator
        - Authy
        - Oracle Mobile Authenticator

        Args:
            secret: TOTP secret key
            name: Account identifier (email or phone)
            issuer: App/company name displayed in authenticator

        Returns:
            otpauth:// URI string
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=name, issuer_name=issuer)

    def get_current_code(self, secret: str) -> str:
        """Get current TOTP code.

        Args:
            secret: TOTP secret key

        Returns:
            6-digit TOTP code
        """
        totp = pyotp.TOTP(secret)
        return totp.now()

    def verify_code(self, secret: str, code: str, valid_window: int = None) -> bool:
        """Verify TOTP code.

        Args:
            secret: TOTP secret key
            code: 6-digit code to verify
            valid_window: Number of time windows to accept (default: TOTP_WINDOW)

        Returns:
            True if code is valid, False otherwise
        """
        if valid_window is None:
            valid_window = self.TOTP_WINDOW

        try:
            totp = pyotp.TOTP(secret)
            # verify_totp accepts valid_window parameter
            is_valid = totp.verify(code, valid_window=valid_window)
            return is_valid
        except Exception as e:
            logger.error(f"TOTP verification failed: {str(e)}")
            return False

    def get_provisioning_time_remaining(self) -> int:
        """Get seconds remaining in current TOTP window.

        Useful for showing countdown timer to user.

        Returns:
            Seconds remaining (0-30)
        """
        return self.TOTP_PERIOD - (
            int(datetime.utcnow().timestamp()) % self.TOTP_PERIOD
        )


class BackupCodeManager:
    """Generate and manage backup codes for MFA."""

    BACKUP_CODE_COUNT = 8
    BACKUP_CODE_LENGTH = 8

    @staticmethod
    def generate_backup_codes() -> List[str]:
        """Generate 8 backup codes.

        Each code is 8 characters of alphanumeric (uppercase, lowercase, digits).

        Returns:
            List of 8 backup codes
        """
        codes = []
        for _ in range(BackupCodeManager.BACKUP_CODE_COUNT):
            code = secrets.token_hex(4).upper()  # 8 hex characters
            codes.append(code)

        logger.info(f"Generated {len(codes)} backup codes")
        return codes

    @staticmethod
    def hash_code(code: str) -> str:
        """Hash a backup code for secure storage.

        Args:
            code: Backup code

        Returns:
            SHA-256 hash
        """
        return hashlib.sha256(code.encode()).hexdigest()

    @staticmethod
    def verify_code(code: str, code_hash: str) -> bool:
        """Verify a backup code against stored hash.

        Args:
            code: Backup code to verify
            code_hash: Stored hash

        Returns:
            True if matches
        """
        return BackupCodeManager.hash_code(code) == code_hash


class MFARateLimiter:
    """Rate limiting for MFA attempts."""

    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15

    @staticmethod
    def check_lockout(phone_number: str) -> Tuple[bool, int]:
        """Check if phone is locked out.

        Args:
            phone_number: Phone number to check

        Returns:
            Tuple of (is_locked, minutes_remaining)
        """
        with get_session_context() as session:
            lockout = (
                session.query(MFALockout)
                .filter(MFALockout.phone_number == phone_number)
                .first()
            )

            if not lockout:
                return False, 0

            if lockout.is_locked():
                minutes_remaining = (
                    lockout.locked_until - datetime.utcnow()
                ).total_seconds() / 60
                return True, int(minutes_remaining)

            return False, 0

    @staticmethod
    def record_failed_attempt(
        phone_number: str, client_id: int = None, reason: str = None
    ):
        """Record a failed MFA attempt.

        Locks account after MAX_FAILED_ATTEMPTS.

        Args:
            phone_number: Phone number
            client_id: Client ID (optional)
            reason: Reason for failure
        """
        with get_session_context() as session:
            lockout = (
                session.query(MFALockout)
                .filter(MFALockout.phone_number == phone_number)
                .first()
            )

            if not lockout:
                lockout = MFALockout(phone_number=phone_number, failed_attempts=1)
                session.add(lockout)
            else:
                lockout.failed_attempts += 1

            # Lock account if too many failed attempts
            if lockout.failed_attempts >= MFARateLimiter.MAX_FAILED_ATTEMPTS:
                lockout.locked_until = datetime.utcnow() + timedelta(
                    minutes=MFARateLimiter.LOCKOUT_DURATION_MINUTES
                )
                logger.warning(
                    f"MFA account locked for {phone_number} after {lockout.failed_attempts} attempts"
                )

            session.commit()

            # Log attempt
            if client_id:
                attempt = MFAAttempt(
                    client_id=client_id,
                    phone_number=phone_number,
                    attempt_type="totp_verify",
                    success=False,
                    error_reason=reason,
                )
                session.add(attempt)
                session.commit()

    @staticmethod
    def record_successful_attempt(
        phone_number: str, client_id: int = None, authenticator_type: str = None
    ):
        """Record successful MFA verification.

        Clears failed attempt counter.

        Args:
            phone_number: Phone number
            client_id: Client ID
            authenticator_type: 'microsoft' or 'oracle'
        """
        with get_session_context() as session:
            # Clear lockout
            lockout = (
                session.query(MFALockout)
                .filter(MFALockout.phone_number == phone_number)
                .first()
            )

            if lockout:
                lockout.failed_attempts = 0
                lockout.locked_until = None
                session.commit()

            # Log attempt
            if client_id:
                attempt = MFAAttempt(
                    client_id=client_id,
                    phone_number=phone_number,
                    attempt_type="totp_verify",
                    success=True,
                    authenticator_type=authenticator_type,
                )
                session.add(attempt)
                session.commit()

            logger.info(f"Successful MFA verification for {phone_number}")


class MFAService:
    """High-level MFA service combining TOTP, QR, and rate limiting."""

    def __init__(self, encryption_key: str = None):
        """Initialize MFA service.

        Args:
            encryption_key: Encryption key for TOTP secrets
        """
        self.totp_manager = TOTPManager(encryption_key)
        self.rate_limiter = MFARateLimiter()

    def setup_mfa_for_user(
        self, client_id: int, phone_number: str
    ) -> Tuple[str, str, List[str]]:
        """Setup MFA for a new user.

        Args:
            client_id: Client ID
            phone_number: User's phone number

        Returns:
            Tuple of (secret, provisioning_uri)
        """
        with get_session_context() as session:
            # Check if MFA already set up
            existing = (
                session.query(MFASetup).filter(MFASetup.client_id == client_id).first()
            )

            if existing:
                logger.warning(f"MFA already setup for client {client_id}")
                raise ValueError("MFA already configured for this account")

            # Generate secret
            secret = self.totp_manager.generate_secret()
            encrypted_secret = self.totp_manager.encryption.encrypt_secret(secret)

            # Generate backup codes
            backup_codes = BackupCodeManager.generate_backup_codes()
            backup_codes_hashed = [
                BackupCodeManager.hash_code(code) for code in backup_codes
            ]

            # Create MFA setup record
            mfa_setup = MFASetup(
                client_id=client_id,
                totp_secret_encrypted=encrypted_secret,
                backup_codes_encrypted=str(
                    backup_codes_hashed
                ),  # Store as string representation
            )
            session.add(mfa_setup)
            session.flush()

            # Persist backup codes for one-time verification flow
            for code_hash in backup_codes_hashed:
                session.add(
                    MFABackupCode(client_id=client_id, code_hash=code_hash, used=False)
                )

            session.commit()

            # Generate provisioning URI
            uri = self.totp_manager.get_totp_uri(secret, phone_number)

            logger.info(f"MFA setup created for client {client_id}")
            return secret, uri, backup_codes  # Return unhashed codes to show to user

    def verify_mfa_code(self, client_id: int, code: str) -> bool:
        """Verify MFA code for user.

        Args:
            client_id: Client ID
            code: 6-digit code to verify

        Returns:
            True if code is valid
        """
        with get_session_context() as session:
            mfa_setup = (
                session.query(MFASetup).filter(MFASetup.client_id == client_id).first()
            )

            if not mfa_setup:
                logger.warning(f"MFA not setup for client {client_id}")
                return False

            # Decrypt secret
            try:
                secret = self.totp_manager.encryption.decrypt_secret(
                    mfa_setup.totp_secret_encrypted
                )
            except ValueError:
                logger.error(f"Failed to decrypt MFA secret for client {client_id}")
                return False

            # Verify code
            is_valid = self.totp_manager.verify_code(secret, code)
            return is_valid

    def verify_backup_code(self, client_id: int, code: str) -> bool:
        """Verify and use a backup code.

        Backup codes are single-use.

        Args:
            client_id: Client ID
            code: Backup code

        Returns:
            True if code is valid and not yet used
        """
        with get_session_context() as session:
            code_hash = BackupCodeManager.hash_code(code)

            # Find backup code
            backup_code = (
                session.query(MFABackupCode)
                .filter(
                    MFABackupCode.client_id == client_id,
                    MFABackupCode.code_hash == code_hash,
                    MFABackupCode.used == False,
                )
                .first()
            )

            if not backup_code:
                logger.warning(
                    f"Invalid or already-used backup code for client {client_id}"
                )
                return False

            # Mark as used
            backup_code.used = True
            backup_code.used_at = datetime.utcnow()
            session.commit()

            logger.info(f"Backup code used for client {client_id}")
            return True

    def is_mfa_enabled(self, client_id: int) -> bool:
        """Check if MFA is enabled for user.

        Args:
            client_id: Client ID

        Returns:
            True if MFA is enabled and verified
        """
        with get_session_context() as session:
            mfa_setup = (
                session.query(MFASetup).filter(MFASetup.client_id == client_id).first()
            )

            return mfa_setup and mfa_setup.mfa_enabled and mfa_setup.mfa_verified

    def enable_authenticator(self, client_id: int, authenticator_type: str):
        """Enable specific authenticator (Microsoft or Oracle).

        Args:
            client_id: Client ID
            authenticator_type: 'microsoft' or 'oracle'
        """
        with get_session_context() as session:
            mfa_setup = (
                session.query(MFASetup).filter(MFASetup.client_id == client_id).first()
            )

            if not mfa_setup:
                raise ValueError("MFA not setup for this client")

            if authenticator_type == "microsoft":
                mfa_setup.microsoft_enabled = True
                mfa_setup.microsoft_qr_generated = datetime.utcnow()
            elif authenticator_type == "oracle":
                mfa_setup.oracle_enabled = True
                mfa_setup.oracle_qr_generated = datetime.utcnow()
            else:
                raise ValueError(f"Unknown authenticator type: {authenticator_type}")

            session.commit()
            logger.info(
                f"Enabled {authenticator_type} authenticator for client {client_id}"
            )
