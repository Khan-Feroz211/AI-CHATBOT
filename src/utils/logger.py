"""Logging configuration and utilities."""

import logging
import os
from datetime import datetime
from functools import wraps


class LoggerConfig:
    """Logging configuration."""

    LOG_DIR = "data/logs"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    @staticmethod
    def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
        """Setup logger with file and console handlers.

        Args:
            name: Logger name
            level: Logging level

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Avoid duplicate handlers
        if logger.hasHandlers():
            return logger

        # Create log directory if it doesn't exist
        os.makedirs(LoggerConfig.LOG_DIR, exist_ok=True)

        # Formatter
        formatter = logging.Formatter(
            LoggerConfig.LOG_FORMAT, datefmt=LoggerConfig.DATE_FORMAT
        )

        # File handler
        log_file = os.path.join(LoggerConfig.LOG_DIR, f"{name}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger


def get_logger(name: str) -> logging.Logger:
    """Get or create logger.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return LoggerConfig.setup_logger(name)


def log_execution(func):
    """Decorator to log function execution.

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """
    logger = get_logger(func.__module__)

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Executing {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"Completed {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise

    return wrapper


def log_database_operation(operation: str):
    """Decorator to log database operations.

    Args:
        operation: Operation name (e.g., 'CREATE', 'UPDATE', 'DELETE')

    Returns:
        Decorator function
    """

    def decorator(func):
        logger = get_logger("database")

        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"DB {operation}: {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"DB {operation} SUCCESS: {func.__name__}")
                return result
            except Exception as e:
                logger.error(
                    f"DB {operation} FAILED: {func.__name__}: {str(e)}", exc_info=True
                )
                raise

        return wrapper

    return decorator


def log_whatsapp_message(phone: str, direction: str, content: str):
    """Log WhatsApp message.

    Args:
        phone: Phone number
        direction: 'incoming' or 'outgoing'
        content: Message content
    """
    logger = get_logger("whatsapp")
    logger.info(f"[{direction.upper()}] {phone}: {content[:100]}")


def log_order_event(order_number: str, event: str, details: str = None):
    """Log order event.

    Args:
        order_number: Order number
        event: Event type (created, confirmed, shipped, etc.)
        details: Additional details
    """
    logger = get_logger("orders")
    msg = f"Order {order_number}: {event}"
    if details:
        msg += f" - {details}"
    logger.info(msg)


def log_auth_event(phone: str, event: str, success: bool, details: str = None):
    """Log authentication event.

    Args:
        phone: Phone number
        event: Event type (otp_requested, verified, failed, etc.)
        success: Whether operation was successful
        details: Additional details
    """
    logger = get_logger("auth")
    level = logging.INFO if success else logging.WARNING
    msg = f"{phone}: {event} - {'SUCCESS' if success else 'FAILED'}"
    if details:
        msg += f" - {details}"
    logger.log(level, msg)


def log_stock_alert(sku: str, alert_type: str, details: str):
    """Log stock alert.

    Args:
        sku: Stock keeping unit
        alert_type: 'low_stock', 'out_of_stock', 'overstock', etc.
        details: Alert details
    """
    logger = get_logger("stock")
    logger.warning(f"SKU {sku}: {alert_type} - {details}")


def log_payment_event(transaction_id: str, event: str, amount: float, success: bool):
    """Log payment event.

    Args:
        transaction_id: Transaction ID
        event: Event type
        amount: Amount involved
        success: Whether operation was successful
    """
    logger = get_logger("payments")
    level = logging.INFO if success else logging.WARNING
    msg = f"Transaction {transaction_id}: {event} - Rs. {amount:,.2f} - {'SUCCESS' if success else 'FAILED'}"
    logger.log(level, msg)


class AuditLogger:
    """Audit logging for compliance."""

    @staticmethod
    def log_user_action(user_id: int, action: str, resource: str, details: dict = None):
        """Log user action for audit.

        Args:
            user_id: User ID
            action: Action performed (CREATE, UPDATE, DELETE, READ)
            resource: Resource name (order, stock, customer, etc.)
            details: Additional details as dict
        """
        logger = get_logger("audit")
        timestamp = datetime.utcnow().isoformat()
        msg = f"[{timestamp}] USER={user_id} ACTION={action} RESOURCE={resource}"
        if details:
            msg += f" DETAILS={details}"
        logger.info(msg)

    @staticmethod
    def log_data_export(user_id: int, export_type: str, record_count: int):
        """Log data export for audit.

        Args:
            user_id: User ID
            export_type: Type of export (orders, customers, stock, etc.)
            record_count: Number of records exported
        """
        logger = get_logger("audit")
        timestamp = datetime.utcnow().isoformat()
        msg = f"[{timestamp}] DATA_EXPORT USER={user_id} TYPE={export_type} RECORDS={record_count}"
        logger.info(msg)
