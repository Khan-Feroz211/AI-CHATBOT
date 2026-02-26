"""Utilities package for WhatsApp Inventory Bot."""

from src.utils.db_helpers import (
    client_exists,
    get_client_by_phone,
    get_low_stock_items,
    get_or_create_client,
    get_order_by_number,
    get_otp_session,
    get_pending_orders,
    get_stock_item_by_sku,
    get_transaction_by_id,
    is_admin,
    is_verified,
)
from src.utils.formatters import WhatsAppFormatter
from src.utils.logger import (
    AuditLogger,
    get_logger,
    log_auth_event,
    log_database_operation,
    log_execution,
    log_order_event,
    log_payment_event,
    log_stock_alert,
    log_whatsapp_message,
)
from src.utils.validators import (
    validate_email,
    validate_order_number,
    validate_order_status,
    validate_otp,
    validate_payment_status,
    validate_phone_number,
    validate_price,
    validate_quantity,
    validate_role,
    validate_selection,
    validate_sku,
    validate_text_input,
)

__all__ = [
    # Database helpers
    "get_client_by_phone",
    "get_or_create_client",
    "get_order_by_number",
    "get_stock_item_by_sku",
    "get_low_stock_items",
    "get_pending_orders",
    "get_transaction_by_id",
    "get_otp_session",
    "client_exists",
    "is_admin",
    "is_verified",
    # Validators
    "validate_phone_number",
    "validate_otp",
    "validate_sku",
    "validate_quantity",
    "validate_price",
    "validate_email",
    "validate_order_number",
    "validate_text_input",
    "validate_selection",
    "validate_order_status",
    "validate_payment_status",
    "validate_role",
    # Formatters
    "WhatsAppFormatter",
    # Logging
    "get_logger",
    "log_execution",
    "log_database_operation",
    "log_whatsapp_message",
    "log_order_event",
    "log_auth_event",
    "log_stock_alert",
    "log_payment_event",
    "AuditLogger",
]
