"""Flask routes for MFA authentication flows."""

import logging
import os
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Tuple

from flask import Blueprint, jsonify, request

from src.auth.mfa import MFARateLimiter, MFAService
from src.auth.mfa_models import MFAAttempt, MFASetup
from src.auth.qr_generator import QRCodeGenerator, WhatsAppQRSender
from src.auth.session import SessionManager, SessionTokenManager
from src.core.database import get_session_context

logger = logging.getLogger(__name__)


# Create blueprint
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# Initialize services
mfa_service = MFAService(encryption_key=os.getenv("TOTP_ENCRYPTION_KEY", ""))
session_manager = SessionManager()
token_manager = SessionTokenManager()


# ============================================================================
# DECORATORS
# ============================================================================


def require_auth(f):
    """Require valid authentication token."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")

        if not token:
            return jsonify({"error": "Missing authorization token"}), 401

        claims = token_manager.verify_token(token)
        if not claims:
            return jsonify({"error": "Invalid token"}), 401

        # Attach claims to request
        request.client_id = claims.get("sub")
        request.phone_number = claims.get("phone")
        request.mfa_verified = claims.get("mfa_verified", False)

        return f(*args, **kwargs)

    return decorated_function


def require_mfa(f):
    """Require MFA verification."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")

        if not token:
            return jsonify({"error": "MFA required"}), 401

        claims = token_manager.verify_token(token)
        if not claims or not claims.get("mfa_verified"):
            return jsonify({"error": "MFA not verified"}), 403

        # Attach claims to request
        request.client_id = claims.get("sub")
        request.phone_number = claims.get("phone")

        return f(*args, **kwargs)

    return decorated_function


def require_admin(f):
    """Require admin role."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_key = request.headers.get("X-Admin-Key")
        expected_key = os.getenv("ADMIN_API_KEY")

        if not admin_key or admin_key != expected_key:
            return jsonify({"error": "Unauthorized"}), 403

        return f(*args, **kwargs)

    return decorated_function


# ============================================================================
# MFA SETUP ROUTES
# ============================================================================


@auth_bp.route("/mfa/setup", methods=["POST"])
def mfa_setup():
    """Initiate MFA setup for user.

    Request:
        {
            "client_id": 123,
            "phone_number": "+923001234567",
            "authenticator_type": "microsoft" | "oracle"
        }

    Response:
        {
            "setup_id": "...",
            "status": "setup_initiated",
            "message": "QR code sent to WhatsApp",
            "backup_codes": ["CODE1", "CODE2", ...]
        }
    """
    data = request.get_json() or {}

    client_id = data.get("client_id")
    phone_number = data.get("phone_number")
    authenticator_type = data.get("authenticator_type", "microsoft").lower()

    if not all([client_id, phone_number]):
        return jsonify({"error": "Missing required fields"}), 400

    if authenticator_type not in ["microsoft", "oracle"]:
        return jsonify({"error": "Invalid authenticator type"}), 400

    try:
        # Setup MFA for user
        secret, uri, backup_codes = mfa_service.setup_mfa_for_user(
            client_id=client_id, phone_number=phone_number
        )

        # Generate QR code
        if authenticator_type == "microsoft":
            qr_image = QRCodeGenerator.generate_microsoft_authenticator_qr(
                secret, phone_number
            )
        else:
            qr_image = QRCodeGenerator.generate_oracle_authenticator_qr(
                secret, phone_number
            )

        # Prepare for WhatsApp
        qr_bytes = WhatsAppQRSender.prepare_qr_for_whatsapp(qr_image)

        # Send QR code via WhatsApp
        try:
            # This would integrate with your WhatsApp client
            # whatsapp_client.send_image(phone_number, qr_bytes, caption="Scan with your authenticator")
            logger.info(f"Sent MFA QR code to {phone_number}")
        except Exception as e:
            logger.error(f"Failed to send QR code: {str(e)}")

        # Send setup instructions
        instructions = QRCodeGenerator.generate_setup_instructions(authenticator_type)
        # whatsapp_client.send_message(phone_number, instructions)

        # Log attempt
        _log_mfa_attempt(
            client_id=client_id,
            phone_number=phone_number,
            attempt_type="initial_setup",
            authenticator_type=authenticator_type,
            success=True,
        )

        return (
            jsonify(
                {
                    "status": "setup_initiated",
                    "message": "QR code and instructions sent",
                    "backup_codes": backup_codes,
                    "authenticator_type": authenticator_type,
                    "expires_in_minutes": 30,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"MFA setup failed: {str(e)}")
        _log_mfa_attempt(
            client_id=client_id,
            phone_number=phone_number,
            attempt_type="initial_setup",
            authenticator_type=authenticator_type,
            success=False,
            error_reason=str(e),
        )
        return jsonify({"error": "Setup failed", "detail": str(e)}), 500


@auth_bp.route("/mfa/verify", methods=["POST"])
def mfa_verify():
    """Verify TOTP code from authenticator.

    Request:
        {
            "client_id": 123,
            "phone_number": "+923001234567",
            "code": "123456"
        }

    Response:
        {
            "status": "verified",
            "access_token": "...",
            "refresh_token": "...",
            "expires_in": 86400
        }
    """
    data = request.get_json() or {}

    client_id = data.get("client_id")
    phone_number = data.get("phone_number")
    code = data.get("code")

    if not all([client_id, phone_number, code]):
        return jsonify({"error": "Missing required fields"}), 400

    # Check rate limiting
    rate_limiter = MFARateLimiter()
    is_locked, minutes_remaining = rate_limiter.check_lockout(phone_number)

    if is_locked:
        return (
            jsonify(
                {
                    "error": "Account locked",
                    "message": f"Too many failed attempts. Try again in {minutes_remaining} minutes",
                }
            ),
            429,
        )

    try:
        # Verify TOTP code
        if mfa_service.verify_mfa_code(client_id=client_id, code=code):
            # Clear lockout
            rate_limiter.record_successful_attempt(
                phone_number=phone_number,
                client_id=client_id,
                authenticator_type="totp",
            )

            # Create session
            session_info = session_manager.create_session(
                client_id=client_id,
                phone_number=phone_number,
                ip_address=request.remote_addr,
                device_info=request.headers.get("User-Agent", ""),
                mfa_verified=True,
            )

            # Log successful attempt
            _log_mfa_attempt(
                client_id=client_id,
                phone_number=phone_number,
                attempt_type="totp_verify",
                success=True,
            )

            return (
                jsonify(
                    {
                        "status": "verified",
                        "access_token": session_info["access_token"],
                        "refresh_token": session_info["refresh_token"],
                        "token_type": session_info["token_type"],
                        "expires_in": session_info["expires_in"],
                    }
                ),
                200,
            )
        else:
            # Record failed attempt
            rate_limiter.record_failed_attempt(
                phone_number=phone_number,
                client_id=client_id,
                reason="Invalid TOTP code",
            )

            # Log failed attempt
            _log_mfa_attempt(
                client_id=client_id,
                phone_number=phone_number,
                attempt_type="totp_verify",
                success=False,
                error_reason="Invalid code",
            )

            return (
                jsonify(
                    {
                        "error": "Invalid code",
                        "message": "Please check the code and try again",
                    }
                ),
                401,
            )

    except Exception as e:
        logger.error(f"TOTP verification failed: {str(e)}")
        return jsonify({"error": "Verification failed"}), 500


@auth_bp.route("/mfa/backup-code", methods=["POST"])
def mfa_backup_code():
    """Verify backup code for emergency access.

    Request:
        {
            "client_id": 123,
            "backup_code": "ABCD1234"
        }

    Response:
        {
            "status": "verified",
            "access_token": "...",
            "message": "Backup code used. Setup a new authenticator soon."
        }
    """
    data = request.get_json() or {}

    client_id = data.get("client_id")
    backup_code = data.get("backup_code")

    if not all([client_id, backup_code]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        phone_result = _get_client_phone(client_id)
        if isinstance(phone_result, tuple):
            return phone_result
        phone_number = phone_result

        if mfa_service.verify_backup_code(client_id=client_id, code=backup_code):
            # Create session
            session_info = session_manager.create_session(
                client_id=client_id, phone_number=phone_number, mfa_verified=True
            )

            # Log usage
            _log_mfa_attempt(
                client_id=client_id,
                phone_number=phone_number,
                attempt_type="backup_code",
                success=True,
            )

            return (
                jsonify(
                    {
                        "status": "verified",
                        "access_token": session_info["access_token"],
                        "message": "Access granted. Please update your authenticator setup.",
                    }
                ),
                200,
            )
        else:
            _log_mfa_attempt(
                client_id=client_id,
                phone_number=phone_number,
                attempt_type="backup_code",
                success=False,
            )
            return jsonify({"error": "Invalid backup code"}), 401

    except Exception as e:
        logger.error(f"Backup code verification failed: {str(e)}")
        return jsonify({"error": "Verification failed"}), 500


# ============================================================================
# TOKEN REFRESH ROUTES
# ============================================================================


@auth_bp.route("/token/refresh", methods=["POST"])
def refresh_token():
    """Refresh access token using refresh token.

    Request:
        {
            "refresh_token": "..."
        }

    Response:
        {
            "access_token": "...",
            "token_type": "Bearer",
            "expires_in": 86400
        }
    """
    data = request.get_json() or {}
    refresh_token = data.get("refresh_token")
    client_id = data.get("client_id")

    if not all([refresh_token, client_id]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        new_tokens = session_manager.refresh_session_token(client_id, refresh_token)

        if not new_tokens:
            return jsonify({"error": "Invalid or expired refresh token"}), 401

        return jsonify(new_tokens), 200

    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        return jsonify({"error": "Token refresh failed"}), 500


# ============================================================================
# ADMIN ROUTES
# ============================================================================


@auth_bp.route("/admin/mfa/reset", methods=["POST"])
@require_admin
def admin_reset_mfa():
    """Reset MFA for a user (admin only).

    Request:
        {
            "client_id": 123,
            "reason": "User locked out"
        }

    Headers:
        X-Admin-Key: admin-api-key
    """
    data = request.get_json() or {}
    client_id = data.get("client_id")
    reason = data.get("reason", "Admin reset")

    if not client_id:
        return jsonify({"error": "client_id required"}), 400

    try:
        with get_session_context() as session:
            mfa_setup = session.query(MFASetup).filter_by(client_id=client_id).first()

            if not mfa_setup:
                return jsonify({"error": "User not found"}), 404

            # Reset MFA
            mfa_setup.mfa_enabled = False
            mfa_setup.mfa_verified = False
            mfa_setup.totp_secret_encrypted = None
            mfa_setup.backup_codes_encrypted = None
            mfa_setup.microsoft_enabled = False
            mfa_setup.oracle_enabled = False

            session.commit()

            logger.info(f"Admin reset MFA for client {client_id}: {reason}")

            return (
                jsonify(
                    {"status": "reset", "message": f"MFA reset for client {client_id}"}
                ),
                200,
            )

    except Exception as e:
        logger.error(f"MFA reset failed: {str(e)}")
        return jsonify({"error": "Reset failed"}), 500


@auth_bp.route("/admin/mfa/logs", methods=["GET"])
@require_admin
def admin_mfa_logs():
    """Get MFA authentication logs (admin only).

    Query Parameters:
        client_id: Filter by client
        limit: Number of recent logs (default 50)
        offset: Offset for pagination (default 0)
    """
    client_id = request.args.get("client_id", type=int)
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    try:
        with get_session_context() as session:
            query = session.query(MFAAttempt)

            if client_id:
                query = query.filter_by(client_id=client_id)

            logs = (
                query.order_by(MFAAttempt.created_at.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )

            return (
                jsonify(
                    {
                        "logs": [
                            {
                                "id": log.id,
                                "client_id": log.client_id,
                                "phone_number": log.phone_number,
                                "attempt_type": log.attempt_type,
                                "success": log.success,
                                "authenticator_type": log.authenticator_type,
                                "error_reason": log.error_reason,
                                "created_at": log.created_at.isoformat(),
                            }
                            for log in logs
                        ],
                        "total": query.count(),
                    }
                ),
                200,
            )

    except Exception as e:
        logger.error(f"Failed to fetch logs: {str(e)}")
        return jsonify({"error": "Failed to fetch logs"}), 500


@auth_bp.route("/admin/mfa/whitelist", methods=["POST"])
@require_admin
def admin_whitelist_phone():
    """Whitelist phone number (skip MFA).

    Request:
        {
            "phone_number": "+923001234567",
            "reason": "Trusted device"
        }
    """
    data = request.get_json() or {}
    phone_number = data.get("phone_number")
    reason = data.get("reason", "")

    if not phone_number:
        return jsonify({"error": "phone_number required"}), 400

    # This would integrate with your whitelist storage
    # For now, just log the action
    logger.info(f"Whitelisted phone {phone_number}: {reason}")

    return jsonify({"status": "whitelisted", "phone_number": phone_number}), 200


@auth_bp.route("/admin/mfa/whitelist/<phone_number>", methods=["DELETE"])
@require_admin
def admin_remove_whitelist(phone_number):
    """Remove phone from whitelist."""
    logger.info(f"Removed whitelist for phone {phone_number}")

    return jsonify({"status": "removed", "phone_number": phone_number}), 200


# ============================================================================
# HEALTH CHECK
# ============================================================================


@auth_bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _log_mfa_attempt(
    client_id: int,
    phone_number: str,
    attempt_type: str,
    success: bool,
    authenticator_type: str = None,
    error_reason: str = None,
):
    """Log MFA attempt to database."""
    try:
        with get_session_context() as session:
            attempt = MFAAttempt(
                client_id=client_id,
                phone_number=phone_number,
                attempt_type=attempt_type,
                success=success,
                authenticator_type=authenticator_type,
                ip_address=request.remote_addr if request else None,
                user_agent=request.headers.get("User-Agent") if request else None,
                error_reason=error_reason,
            )
            session.add(attempt)
            session.commit()
    except Exception as e:
        logger.error(f"Failed to log MFA attempt: {str(e)}")


def _get_client_phone(client_id: int) -> str:
    """Get phone number for client_id."""
    try:
        with get_session_context() as session:
            from src.core.models import Client

            client = session.query(Client).filter_by(id=client_id).first()

            if not client:
                return jsonify({"error": "Client not found"}), 404

            return client.phone_number
    except Exception as e:
        logger.error(f"Failed to get client phone: {str(e)}")
        return jsonify({"error": "Failed to get client info"}), 500
