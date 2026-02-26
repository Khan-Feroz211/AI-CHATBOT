"""Utility functions for common operations."""

from datetime import datetime
from typing import Optional

from src.core.database import get_session_context
from src.core.models import Client, Order, OTPSession, StockItem, Transaction


def get_client_by_phone(phone_number: str) -> Optional[Client]:
    """Get client by phone number.

    Args:
        phone_number: Client phone number

    Returns:
        Client object or None if not found
    """
    with get_session_context() as session:
        return session.query(Client).filter(Client.phone_number == phone_number).first()


def get_or_create_client(
    phone_number: str, name: str = None, auto_commit: bool = True
) -> Client:
    """Get existing client or create new one.

    Args:
        phone_number: Client phone number
        name: Client name (for new clients)
        auto_commit: Whether to commit changes

    Returns:
        Client object
    """
    with get_session_context() as session:
        client = (
            session.query(Client).filter(Client.phone_number == phone_number).first()
        )

        if not client:
            client = Client(phone_number=phone_number, name=name or phone_number)
            session.add(client)
            session.flush()  # Get the ID without committing

        # Return a detached copy with ID populated
        return client


def get_order_by_number(order_number: str) -> Optional[Order]:
    """Get order by order number.

    Args:
        order_number: Order number

    Returns:
        Order object or None if not found
    """
    with get_session_context() as session:
        return session.query(Order).filter(Order.order_number == order_number).first()


def get_stock_item_by_sku(sku: str) -> Optional[StockItem]:
    """Get stock item by SKU.

    Args:
        sku: Stock keeping unit

    Returns:
        StockItem object or None if not found
    """
    with get_session_context() as session:
        return session.query(StockItem).filter(StockItem.sku == sku).first()


def get_low_stock_items(threshold_percent: float = 0.25) -> list:
    """Get items with low stock.

    Args:
        threshold_percent: Threshold percentage (default 25% of reorder_qty)

    Returns:
        List of low stock items
    """
    with get_session_context() as session:
        items = (
            session.query(StockItem)
            .filter(StockItem.reorder_quantity.isnot(None))
            .all()
        )

        low_stock = []
        for item in items:
            threshold = item.reorder_quantity * threshold_percent
            if item.current_quantity <= threshold:
                low_stock.append(item)

        return low_stock


def get_pending_orders(client_id: int = None) -> list:
    """Get pending/active orders.

    Args:
        client_id: Filter by client (optional)

    Returns:
        List of pending orders
    """
    with get_session_context() as session:
        query = session.query(Order).filter(Order.status.in_(["pending", "confirmed"]))

        if client_id:
            query = query.filter(Order.client_id == client_id)

        return query.order_by(Order.created_at.desc()).all()


def get_transaction_by_id(transaction_id: str) -> Optional[Transaction]:
    """Get transaction by ID.

    Args:
        transaction_id: Transaction ID

    Returns:
        Transaction object or None if not found
    """
    with get_session_context() as session:
        return (
            session.query(Transaction)
            .filter(Transaction.transaction_id == transaction_id)
            .first()
        )


def get_otp_session(phone_number: str) -> Optional[OTPSession]:
    """Get active OTP session for phone number.

    Args:
        phone_number: Phone number

    Returns:
        OTPSession object or None if not found/expired
    """
    with get_session_context() as session:
        session_obj = (
            session.query(OTPSession)
            .filter(
                OTPSession.phone_number == phone_number,
                OTPSession.expires_at > datetime.utcnow(),
                OTPSession.is_verified == False,
            )
            .order_by(OTPSession.created_at.desc())
            .first()
        )

        return session_obj


def client_exists(phone_number: str) -> bool:
    """Check if client exists.

    Args:
        phone_number: Phone number

    Returns:
        True if client exists, False otherwise
    """
    with get_session_context() as session:
        return (
            session.query(Client).filter(Client.phone_number == phone_number).first()
            is not None
        )


def is_admin(client_id: int) -> bool:
    """Check if client is admin.

    Args:
        client_id: Client ID

    Returns:
        True if client is admin, False otherwise
    """
    with get_session_context() as session:
        client = session.query(Client).filter(Client.id == client_id).first()
        return client and client.role == "admin" if client else False


def is_verified(client_id: int) -> bool:
    """Check if client is verified.

    Args:
        client_id: Client ID

    Returns:
        True if verified, False otherwise
    """
    with get_session_context() as session:
        client = session.query(Client).filter(Client.id == client_id).first()
        return client.is_verified if client else False
