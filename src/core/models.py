"""Database models for WhatsApp Inventory Bot."""

from datetime import datetime

from sqlalchemy import (
    DECIMAL,
    JSON,
    TEXT,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Client(Base):
    """Client/User model."""

    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100))
    role = Column(String(20), default="client")  # 'client', 'admin', 'manager'
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    orders = relationship("Order", back_populates="client")
    customer_profile = relationship(
        "CustomerProfile", uselist=False, back_populates="client"
    )
    transactions = relationship("Transaction", back_populates="client")
    messages = relationship("WhatsAppMessage", back_populates="client")
    complaints = relationship("Complaint", back_populates="client")
    activity_logs = relationship("ActivityLog", back_populates="client")

    def __repr__(self):
        return f"<Client {self.phone_number}>"


class StockItem(Base):
    """Stock/Inventory item model."""

    __tablename__ = "stock_items"

    id = Column(Integer, primary_key=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(TEXT)
    current_quantity = Column(Integer, default=0)
    reorder_threshold = Column(Integer)
    reorder_quantity = Column(Integer)
    unit_price = Column(DECIMAL(10, 2))
    unit = Column(String(20))  # 'pcs', 'kg', 'liters', etc.
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    movements = relationship("StockMovement", back_populates="stock_item")
    supplier_prices = relationship("SupplierPrice", back_populates="stock_item")
    order_items = relationship("OrderItem", back_populates="stock_item")

    def __repr__(self):
        return f"<StockItem {self.sku} - {self.name}>"


class StockMovement(Base):
    """Stock movement/transaction log."""

    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True)
    stock_item_id = Column(Integer, ForeignKey("stock_items.id"), nullable=False)
    movement_type = Column(String(20), nullable=False)  # 'in', 'out', 'adjustment'
    quantity = Column(Integer, nullable=False)
    reason = Column(String(100))  # 'order', 'return', 'damaged', etc.
    initiated_by = Column(Integer, ForeignKey("clients.id"))
    reference_id = Column(String(50))  # Order/Transaction ID
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    stock_item = relationship("StockItem", back_populates="movements")

    def __repr__(self):
        return f"<StockMovement {self.stock_item_id} - {self.movement_type}>"


class Supplier(Base):
    """Supplier/Vendor model."""

    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100))
    phone = Column(String(20))
    website = Column(String(200))
    api_key = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    stock_items = relationship("StockItem")
    prices = relationship("SupplierPrice", back_populates="supplier")

    def __repr__(self):
        return f"<Supplier {self.name}>"


class SupplierPrice(Base):
    """Supplier pricing information."""

    __tablename__ = "supplier_prices"

    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    stock_item_id = Column(Integer, ForeignKey("stock_items.id"), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    minimum_order_qty = Column(Integer)
    lead_time_days = Column(Integer)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier = relationship("Supplier", back_populates="prices")
    stock_item = relationship("StockItem", back_populates="supplier_prices")

    def __repr__(self):
        return f"<SupplierPrice {self.supplier_id} - {self.stock_item_id}>"


class Order(Base):
    """Customer order model."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    status = Column(
        String(20), default="pending"
    )  # pending, confirmed, shipped, delivered, cancelled
    total_amount = Column(DECIMAL(10, 2))
    payment_status = Column(String(20), default="unpaid")  # unpaid, paid, partial
    notes = Column(TEXT)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    delivered_at = Column(DateTime)

    # Relationships
    client = relationship("Client", back_populates="orders")
    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    transactions = relationship("Transaction", back_populates="order")
    complaints = relationship("Complaint", back_populates="order")

    def __repr__(self):
        return f"<Order {self.order_number}>"


class OrderItem(Base):
    """Individual items in an order."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    stock_item_id = Column(Integer, ForeignKey("stock_items.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(10, 2))
    subtotal = Column(DECIMAL(10, 2))

    # Relationships
    order = relationship("Order", back_populates="items")
    stock_item = relationship("StockItem", back_populates="order_items")

    def __repr__(self):
        return f"<OrderItem {self.order_id}>"


class CustomerProfile(Base):
    """Customer profile and credit information."""

    __tablename__ = "customer_profiles"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), unique=True, nullable=False)
    business_name = Column(String(100))
    address = Column(TEXT)
    credit_limit = Column(DECIMAL(10, 2))
    credit_used = Column(DECIMAL(10, 2), default=0)
    total_spent = Column(DECIMAL(12, 2), default=0)
    total_orders = Column(Integer, default=0)
    preferred_payment_method = Column(String(50))
    notes = Column(TEXT)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", back_populates="customer_profile")

    def __repr__(self):
        return f"<CustomerProfile {self.client_id}>"


class Transaction(Base):
    """Payment/Transaction record."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    transaction_id = Column(String(50), unique=True, nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    payment_method = Column(
        String(50)
    )  # 'cash', 'bank_transfer', 'jazzcash', 'easypaisa'
    status = Column(
        String(20), default="pending"
    )  # pending, completed, failed, refunded
    reference_number = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="transactions")
    client = relationship("Client", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction {self.transaction_id}>"


class WhatsAppMessage(Base):
    """WhatsApp message history for audit."""

    __tablename__ = "whatsapp_messages"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    message_type = Column(String(20), nullable=False)  # 'incoming', 'outgoing'
    content = Column(TEXT)
    media_url = Column(String(500))
    message_id = Column(String(100), unique=True, index=True)
    status = Column(String(20), default="delivered")  # sent, delivered, read, failed
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    client = relationship("Client", back_populates="messages")

    def __repr__(self):
        return f"<WhatsAppMessage {self.message_id}>"


class OTPSession(Base):
    """OTP authentication session."""

    __tablename__ = "otp_sessions"

    id = Column(Integer, primary_key=True)
    phone_number = Column(String(20), nullable=False, index=True)
    otp_code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<OTPSession {self.phone_number}>"


class ActivityLog(Base):
    """Activity/Audit log."""

    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    action = Column(String(100), nullable=False)
    resource = Column(String(50))
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    client = relationship("Client", back_populates="activity_logs")

    def __repr__(self):
        return f"<ActivityLog {self.action}>"


class Complaint(Base):
    """Customer complaint/issue tracking."""

    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True)
    complaint_id = Column(String(50), unique=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"))
    issue_description = Column(TEXT, nullable=False)
    status = Column(String(20), default="open")  # open, investigating, resolved, closed
    resolution = Column(TEXT)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime)

    # Relationships
    client = relationship("Client", back_populates="complaints")
    order = relationship("Order", back_populates="complaints")

    def __repr__(self):
        return f"<Complaint {self.complaint_id}>"
