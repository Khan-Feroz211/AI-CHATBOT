"""Tests for MFA/2FA authentication system."""

import time

import pytest

from src.auth.mfa import BackupCodeManager, MFARateLimiter, MFAService, TOTPManager
from src.auth.mfa_models import MFAAttempt, MFASession, MFASetup
from src.auth.qr_generator import QRCodeGenerator
from src.auth.session import SessionManager, SessionTokenManager


class TestTOTPSecretGeneration:
    """Test TOTP secret generation."""

    def test_generate_secret(self):
        """Test that TOTP secret is generated correctly."""
        totp = TOTPManager()
        secret = totp.generate_secret()

        assert secret is not None
        assert len(secret) > 0
        assert isinstance(secret, str)

    def test_secret_is_base32(self):
        """Test that generated secret is valid base32."""
        totp = TOTPManager()
        secret = totp.generate_secret()

        # Base32 only contains A-Z and 2-7
        import re

        assert re.match(r"^[A-Z2-7]+$", secret)

    def test_get_totp_uri(self):
        """Test otpauth URI generation."""
        totp = TOTPManager()
        secret = totp.generate_secret()

        uri = totp.get_totp_uri(secret, "+923001234567", "WhatsApp Bot")

        assert uri.startswith("otpauth://totp/")
        assert "%2B923001234567" in uri or "+923001234567" in uri  # URL encoded or raw
        assert "WhatsApp%20Bot" in uri


class TestQRCodeGeneration:
    """Test QR code generation."""

    def test_generate_microsoft_authenticator_qr(self):
        """Test QR code generation for Microsoft Authenticator."""
        from src.auth.mfa import TOTPManager

        totp = TOTPManager()
        secret = totp.generate_secret()

        qr = QRCodeGenerator.generate_microsoft_authenticator_qr(
            secret, "+923001234567"
        )

        assert qr is not None
        assert qr.width > 0 and qr.height > 0

    def test_generate_oracle_authenticator_qr(self):
        """Test QR code generation for Oracle Authenticator."""
        from src.auth.mfa import TOTPManager

        totp = TOTPManager()
        secret = totp.generate_secret()

        qr = QRCodeGenerator.generate_oracle_authenticator_qr(secret, "+923001234567")

        assert qr is not None
        assert qr.width > 0 and qr.height > 0

    def test_qr_to_bytes(self):
        """Test QR code conversion to bytes."""
        from src.auth.mfa import TOTPManager

        totp = TOTPManager()
        secret = totp.generate_secret()
        qr = QRCodeGenerator.generate_microsoft_authenticator_qr(
            secret, "+923001234567"
        )

        qr_bytes = QRCodeGenerator.image_to_bytes(qr)

        assert isinstance(qr_bytes, bytes)
        assert len(qr_bytes) > 0

    def test_qr_to_base64(self):
        """Test QR code conversion to base64."""
        from src.auth.mfa import TOTPManager

        totp = TOTPManager()
        secret = totp.generate_secret()
        qr = QRCodeGenerator.generate_microsoft_authenticator_qr(
            secret, "+923001234567"
        )

        b64 = QRCodeGenerator.image_to_base64(qr)

        assert isinstance(b64, str)
        assert len(b64) > 0
        # Base64 should not have special chars other than +/=
        assert all(c.isalnum() or c in "+/=" for c in b64)


class TestTOTPCodeVerification:
    """Test TOTP code verification."""

    def test_get_current_code(self):
        """Test getting current TOTP code."""
        totp = TOTPManager()
        secret = totp.generate_secret()

        code = totp.get_current_code(secret)

        assert code is not None
        assert len(code) == 6
        assert code.isdigit()

    def test_verify_current_code(self):
        """Test verifying current TOTP code."""
        totp = TOTPManager()
        secret = totp.generate_secret()

        code = totp.get_current_code(secret)
        is_valid = totp.verify_code(secret, code)

        assert is_valid is True

    def test_verify_invalid_code(self):
        """Test verifying invalid TOTP code."""
        totp = TOTPManager()
        secret = totp.generate_secret()

        is_valid = totp.verify_code(secret, "000000")

        assert is_valid is False

    def test_verify_code_with_time_window(self):
        """Test TOTP verification with time window tolerance."""
        totp = TOTPManager()
        secret = totp.generate_secret()

        code = totp.get_current_code(secret)

        # Should be valid with time window
        is_valid = totp.verify_code(secret, code, valid_window=1)
        assert is_valid is True

    def test_provisioning_time_remaining(self):
        """Test getting time remaining for current TOTP code."""
        totp = TOTPManager()

        remaining = totp.get_provisioning_time_remaining()

        assert 0 < remaining <= 30


class TestBackupCodes:
    """Test backup code generation and verification."""

    def test_generate_backup_codes(self):
        """Test generating backup codes."""
        manager = BackupCodeManager()

        codes = manager.generate_backup_codes()

        assert len(codes) == 8
        assert all(isinstance(code, str) for code in codes)
        assert all(len(code) == 8 for code in codes)

    def test_backup_codes_are_unique(self):
        """Test that generated backup codes are unique."""
        manager = BackupCodeManager()

        codes = manager.generate_backup_codes()

        assert len(codes) == len(set(codes))

    def test_hash_code(self):
        """Test hashing a backup code."""
        manager = BackupCodeManager()

        code = "ABCD1234"
        hashed = manager.hash_code(code)

        assert hashed is not None
        assert len(hashed) > 0
        assert hashed != code  # Should not be plaintext

    def test_verify_backup_code(self):
        """Test verifying a backup code."""
        manager = BackupCodeManager()

        code = "ABCD1234"
        hashed = manager.hash_code(code)

        is_valid = manager.verify_code(code, hashed)

        assert is_valid is True

    def test_verify_invalid_backup_code(self):
        """Test verifying invalid backup code."""
        manager = BackupCodeManager()

        code = "ABCD1234"
        hashed = manager.hash_code(code)

        is_valid = manager.verify_code("WRONG1234", hashed)

        assert is_valid is False


class TestRateLimiting:
    """Test rate limiting and lockout."""

    def test_check_lockout_not_locked(self):
        """Test checking lockout status when not locked."""
        limiter = MFARateLimiter()

        is_locked, minutes = limiter.check_lockout("+923001234567")

        assert is_locked is False
        assert minutes >= 0

    def test_lockout_after_failed_attempts(self):
        """Test that lockout occurs after 5 failed attempts."""
        limiter = MFARateLimiter()
        phone = "+923001234567"

        # Record 5 failed attempts
        for i in range(5):
            limiter.record_failed_attempt(phone, 1, f"Failed attempt {i+1}")

        # Should be locked
        is_locked, minutes = limiter.check_lockout(phone)

        assert is_locked is True
        assert minutes > 0

    def test_lockout_duration(self):
        """Test that lockout lasts 15 minutes."""
        limiter = MFARateLimiter()
        phone = "+923001234567"

        # Record 5 failed attempts
        for i in range(5):
            limiter.record_failed_attempt(phone, 1, "Failed attempt")

        is_locked, minutes = limiter.check_lockout(phone)

        assert is_locked is True
        assert minutes <= 15
        assert minutes > 0

    def test_successful_attempt_clears_lockout(self):
        """Test that successful attempt clears lockout."""
        limiter = MFARateLimiter()
        phone = "+923001234567"

        # Record 5 failed attempts
        for i in range(5):
            limiter.record_failed_attempt(phone, 1, "Failed attempt")

        # Record successful attempt
        limiter.record_successful_attempt(phone, 1, "totp")

        # Should not be locked
        is_locked, minutes = limiter.check_lockout(phone)

        assert is_locked is False


class TestSessionTokens:
    """Test session token creation and validation."""

    def test_create_access_token(self):
        """Test creating access token."""
        manager = SessionTokenManager()

        token = manager.create_access_token(
            client_id="123", phone_number="+923001234567", mfa_verified=True
        )

        assert token is not None
        assert isinstance(token, str)

    def test_verify_access_token(self):
        """Test verifying access token."""
        manager = SessionTokenManager()

        token = manager.create_access_token(
            client_id="123", phone_number="+923001234567", mfa_verified=True
        )

        claims = manager.verify_token(token)

        assert claims is not None
        assert claims["sub"] == "123"
        assert claims["phone"] == "+923001234567"
        assert claims["mfa_verified"] is True

    def test_invalid_token(self):
        """Test verifying invalid token."""
        manager = SessionTokenManager()

        claims = manager.verify_token("invalid.token.here")

        assert claims is None

    def test_token_expiration(self):
        """Test that token identifies as expired."""
        manager = SessionTokenManager()

        token = manager.create_access_token(
            client_id="123", phone_number="+923001234567", mfa_verified=True
        )

        is_expired = manager.is_token_expired(token)

        assert is_expired is False  # Should be valid immediately

    def test_refresh_token(self):
        """Test creating and using refresh token."""
        manager = SessionTokenManager()

        refresh_token = manager.create_refresh_token(
            client_id="123", phone_number="+923001234567"
        )

        new_access_token = manager.refresh_access_token(refresh_token)

        assert new_access_token is not None
        claims = manager.verify_token(new_access_token)
        assert claims is not None


class TestSessionManagement:
    """Test session management."""

    def test_create_session(self, db_session):
        """Test creating a session."""
        manager = SessionManager()

        session_info = manager.create_session(
            client_id=1,
            phone_number="+923001234567",
            ip_address="127.0.0.1",
            mfa_verified=True,
        )

        assert session_info is not None
        assert "access_token" in session_info
        assert "refresh_token" in session_info
        assert session_info["mfa_verified"] is True

    def test_validate_session(self, db_session):
        """Test validating a session."""
        manager = SessionManager()

        session_info = manager.create_session(
            client_id=1, phone_number="+923001234567", mfa_verified=True
        )

        token = session_info["access_token"]
        is_valid = manager.validate_session(client_id=1, token=token)

        assert is_valid is True

    def test_invalidate_session(self, db_session):
        """Test invalidating a session."""
        manager = SessionManager()

        session_info = manager.create_session(
            client_id=1, phone_number="+923001234567", mfa_verified=True
        )

        token = session_info["access_token"]
        manager.invalidate_session(client_id=1, token=token)

        is_valid = manager.validate_session(client_id=1, token=token)

        assert is_valid is False

    def test_refresh_session_token(self, db_session):
        """Test refreshing a session token."""
        manager = SessionManager()

        session_info = manager.create_session(
            client_id=1, phone_number="+923001234567", mfa_verified=True
        )

        refresh_token = session_info["refresh_token"]
        new_tokens = manager.refresh_session_token(
            client_id=1, refresh_token=refresh_token
        )

        assert new_tokens is not None
        assert "access_token" in new_tokens


class TestMFAService:
    """Test high-level MFA service."""

    def test_mfa_service_setup(self, test_mfa_service, db_session, test_client):
        """Test MFA setup."""
        secret, uri, backup_codes = test_mfa_service.setup_mfa_for_user(
            client_id=test_client.id, phone_number=test_client.phone_number
        )

        assert secret is not None
        assert uri is not None
        assert uri.startswith("otpauth://")
        assert len(backup_codes) == 8

    def test_mfa_service_verify_code(self, test_mfa_service, db_session, test_client):
        """Test MFA code verification."""
        # Setup MFA
        secret, uri, backup_codes = test_mfa_service.setup_mfa_for_user(
            client_id=test_client.id, phone_number=test_client.phone_number
        )

        # Get current code
        from src.auth.mfa import TOTPManager

        totp = TOTPManager()
        code = totp.get_current_code(secret)

        # Verify code
        is_valid = test_mfa_service.verify_mfa_code(client_id=test_client.id, code=code)

        assert is_valid is True

    def test_mfa_service_verify_backup_code(
        self, test_mfa_service, db_session, test_client
    ):
        """Test MFA backup code verification."""
        # Setup MFA
        secret, uri, backup_codes = test_mfa_service.setup_mfa_for_user(
            client_id=test_client.id, phone_number=test_client.phone_number
        )

        # Use first backup code
        is_valid = test_mfa_service.verify_backup_code(
            client_id=test_client.id, code=backup_codes[0]
        )

        assert is_valid is True

        # Using again should fail (single-use)
        is_valid = test_mfa_service.verify_backup_code(
            client_id=test_client.id, code=backup_codes[0]
        )

        assert is_valid is False
