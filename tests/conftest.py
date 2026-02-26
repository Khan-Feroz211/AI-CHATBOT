"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import os
import uuid
from datetime import datetime

import pytest
from cryptography.fernet import Fernet


def _configure_test_environment() -> None:
    """Set required environment variables for test execution."""
    os.environ.setdefault("TOTP_ENCRYPTION_KEY", Fernet.generate_key().decode("utf-8"))
    os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    os.environ.setdefault("FLASK_ENV", "testing")


_configure_test_environment()

from src.auth.mfa import MFAService
from src.core.config import TestingConfig
from src.core.database import get_db, init_database
from src.core.models import Client, Order, StockItem, Supplier
from src.main import create_app


@pytest.fixture(scope="session", autouse=True)
def _init_database_for_all_tests():
    """Initialize global database manager for tests not using Flask app fixture."""
    init_database(TestingConfig())


@pytest.fixture(scope="session")
def app():
    """Create Flask app for testing."""
    config = TestingConfig()
    flask_app = create_app(config)

    with flask_app.app_context():
        get_db().init_db()

    return flask_app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create Flask CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture(scope="function")
def session(app):
    """Provide isolated database session for each test."""
    with app.app_context():
        db = get_db()
        db.drop_db()
        db.init_db()
        test_session = db.get_session()
        try:
            yield test_session
        finally:
            test_session.close()


@pytest.fixture(scope="function")
def db_session(session):
    """Backward-compatible alias used by auth tests."""
    return session


@pytest.fixture(scope="function")
def cleanup_db(app):
    """Reset database schema for isolated tests."""
    yield
    with app.app_context():
        db = get_db()
        db.drop_db()
        db.init_db()


@pytest.fixture
def test_client(session):
    """Create a sample client record."""
    client_obj = Client(
        phone_number="+923001234567",
        name="Test Client",
        role="client",
        is_verified=True,
        is_active=True,
    )
    session.add(client_obj)
    session.commit()
    return client_obj


@pytest.fixture
def test_admin(session):
    """Create a sample admin record."""
    admin = Client(
        phone_number="+923009999999",
        name="Test Admin",
        role="admin",
        is_verified=True,
        is_active=True,
    )
    session.add(admin)
    session.commit()
    return admin


@pytest.fixture
def test_stock_item(session):
    """Create a sample stock item."""
    item = StockItem(
        sku="TEST-001",
        name="Test Product",
        description="Test product for unit tests",
        current_quantity=100,
        reorder_threshold=20,
        reorder_quantity=50,
        unit_price=500.00,
        unit="pcs",
    )
    session.add(item)
    session.commit()
    return item


@pytest.fixture
def test_supplier(session):
    """Create a sample supplier record."""
    supplier = Supplier(
        name="Test Supplier",
        email="supplier@test.com",
        phone="+923001234567",
        is_active=True,
    )
    session.add(supplier)
    session.commit()
    return supplier


@pytest.fixture
def test_order(session, test_client, test_stock_item):
    """Create a sample order record."""
    order = Order(
        order_number="ORD-20240101-001",
        client_id=test_client.id,
        status="pending",
        total_amount=5000.00,
        payment_status="unpaid",
    )
    session.add(order)
    session.commit()
    return order


@pytest.fixture
def test_mfa_service() -> MFAService:
    """Provide MFA service instance for auth tests."""
    return MFAService()


class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_client(session, phone_number="+923001234567", **kwargs):
        """Create a test client."""
        defaults = {
            "name": f"Client {phone_number}",
            "role": "client",
            "is_verified": True,
            "is_active": True,
        }
        defaults.update(kwargs)

        client_obj = Client(phone_number=phone_number, **defaults)
        session.add(client_obj)
        session.commit()
        return client_obj

    @staticmethod
    def create_stock_item(session, sku="TEST-001", **kwargs):
        """Create a test stock item."""
        defaults = {
            "name": f"Product {sku}",
            "current_quantity": 100,
            "reorder_threshold": 20,
            "reorder_quantity": 50,
            "unit_price": 500.00,
            "unit": "pcs",
        }
        defaults.update(kwargs)

        item = StockItem(sku=sku, **defaults)
        session.add(item)
        session.commit()
        return item

    @staticmethod
    def create_order(session, client_id, **kwargs):
        """Create a test order."""
        defaults = {
            "order_number": f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:5].upper()}",
            "status": "pending",
            "total_amount": 5000.00,
            "payment_status": "unpaid",
        }
        defaults.update(kwargs)

        order = Order(client_id=client_id, **defaults)
        session.add(order)
        session.commit()
        return order


@pytest.fixture
def factory(session):
    """Provide test data factory."""
    return TestDataFactory()
