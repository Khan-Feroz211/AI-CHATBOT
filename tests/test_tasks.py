"""Tests for BazaarBot Celery tasks and Redis cache layer.

All tasks run synchronously thanks to ``task_always_eager=True``, so no
real Redis or Celery worker is required.  Database and external-service
calls are fully mocked.
"""
import json
import os

import pytest
from unittest.mock import MagicMock, patch

# ── Force synchronous task execution before importing tasks ──────────────

os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/bazaarbot")
os.environ.setdefault("SECRET_KEY", "test-secret")

from bazaarbot.celery_app import celery  # noqa: E402 — env must be set first

celery.conf.update(
    task_always_eager=True,
    task_eager_propagates=True,
)


# ═══════════════════════════════════════════════════════════════════════════
# Email tasks
# ═══════════════════════════════════════════════════════════════════════════

class TestSendNotificationEmail:
    def test_success(self):
        """Task returns success dict and delegates to send_email."""
        with patch(
            "bazaarbot.tasks.email_tasks.send_email",
            return_value=True,
        ) as mock_send:
            from bazaarbot.tasks.email_tasks import send_notification_email

            result = send_notification_email.delay(
                to_email="test@example.com",
                subject="Test Subject",
                body="Test body",
                tenant_slug="test-tenant",
            ).get()

        assert result["success"] is True
        assert result["to"] == "test@example.com"
        mock_send.assert_called_once()

    def test_retry_on_failure(self):
        """Task raises after exhausting retries when send_email always fails."""
        with patch(
            "bazaarbot.tasks.email_tasks.send_email",
            side_effect=Exception("SMTP down"),
        ):
            from bazaarbot.tasks.email_tasks import send_notification_email
            from celery.exceptions import MaxRetriesExceededError

            with pytest.raises(Exception):
                send_notification_email.delay(
                    to_email="fail@example.com",
                    subject="Subject",
                    body="Body",
                    tenant_slug="test-tenant",
                ).get()


# ═══════════════════════════════════════════════════════════════════════════
# Order tasks
# ═══════════════════════════════════════════════════════════════════════════

_PRODUCT = {
    "product_name": "Rice",
    "quantity": 10,
    "sell_price": "150.00",
    "reorder_level": 2,
    "unit": "kg",
}


class TestProcessOrder:
    def test_success(self):
        """Order is created and returns a valid ORD- reference."""
        with (
            patch("bazaarbot.database_pg.get_product", return_value=_PRODUCT),
            patch(
                "bazaarbot.database_pg.create_order",
                return_value=("ORD-1a2b3c", 300.0),
            ),
            patch("bazaarbot.tasks.email_tasks.send_email"),
            patch("bazaarbot.database_pg.get_tenant", return_value=None),
            patch("bazaarbot.cache.get_redis"),
        ):
            from bazaarbot.tasks.order_tasks import process_order

            result = process_order.delay(
                "test-tenant", "+923001234567", "Rice", 2, "easypaisa"
            ).get()

        assert result["success"] is True
        assert result["order_ref"].startswith("ORD-")

    def test_insufficient_stock(self):
        """Returns failure dict when requested quantity exceeds stock."""
        low_stock_product = dict(_PRODUCT, quantity=1)
        with (
            patch("bazaarbot.database_pg.get_product", return_value=low_stock_product),
            patch("bazaarbot.cache.get_redis"),
        ):
            from bazaarbot.tasks.order_tasks import process_order

            result = process_order.delay(
                "test-tenant", "+923001234567", "Rice", 5, "cash"
            ).get()

        assert result["success"] is False
        assert result["error"] == "insufficient_stock"

    def test_product_not_found(self):
        """Returns failure dict when product does not exist in inventory."""
        with (
            patch("bazaarbot.database_pg.get_product", return_value=None),
            patch("bazaarbot.cache.get_redis"),
        ):
            from bazaarbot.tasks.order_tasks import process_order

            result = process_order.delay(
                "test-tenant", "+923001234567", "Ghost Product", 1, "cash"
            ).get()

        assert result["success"] is False
        assert result["error"] == "product_not_found"


# ═══════════════════════════════════════════════════════════════════════════
# Alert tasks
# ═══════════════════════════════════════════════════════════════════════════

_LOW_ITEM = {
    "product_name": "Sugar",
    "quantity": 2,
    "reorder_level": 5,
    "unit": "kg",
}
_OK_ITEM = {
    "product_name": "Flour",
    "quantity": 50,
    "reorder_level": 5,
    "unit": "kg",
}


class TestCheckLowStock:
    def test_sends_alert_when_low(self):
        """Dispatches low-stock email when quantity <= reorder_level."""
        with (
            patch(
                "bazaarbot.database_pg.get_inventory",
                return_value=[_LOW_ITEM],
            ),
            patch(
                "bazaarbot.tasks.email_tasks.send_email"
            ) as mock_email,
            patch(
                "bazaarbot.database_pg.get_tenant",
                return_value={
                    "name": "Test Shop",
                    "notify_email": "owner@test.pk",
                },
            ),
            patch("bazaarbot.cache.get_redis"),
        ):
            from bazaarbot.tasks.alert_tasks import check_low_stock

            result = check_low_stock.delay("test-tenant").get()

        assert result["alerts_sent"] == 1
        mock_email.assert_called_once()

    def test_no_alert_when_sufficient(self):
        """Does NOT send email when all items have sufficient stock."""
        with (
            patch(
                "bazaarbot.database_pg.get_inventory",
                return_value=[_OK_ITEM],
            ),
            patch("bazaarbot.tasks.email_tasks.send_email") as mock_email,
            patch("bazaarbot.cache.get_redis"),
        ):
            from bazaarbot.tasks.alert_tasks import check_low_stock

            result = check_low_stock.delay("test-tenant").get()

        assert result["alerts_sent"] == 0
        mock_email.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════
# Appointment tasks
# ═══════════════════════════════════════════════════════════════════════════

_APPOINTMENT = {
    "id": 1,
    "status": "booked",
    "phone": "+923001234567",
    "customer_name": "Ali",
    "appointment_time": "10:00",
    "purpose": "Hair cut",
}


class TestSendAppointmentReminder:
    def test_sends_whatsapp_reminder(self):
        """Queues a WhatsApp message that contains the word 'appointment'."""
        sent_messages: list[str] = []

        def fake_send_whatsapp(to, msg):
            sent_messages.append(msg)

        with (
            patch(
                "bazaarbot.database_pg.get_appointments",
                return_value=[_APPOINTMENT],
            ),
            patch(
                "bazaarbot.database_pg.get_tenant",
                return_value={"name": "Test Shop"},
            ),
            patch(
                "bazaarbot.channels.whatsapp.send_whatsapp",
                side_effect=fake_send_whatsapp,
            ),
            patch("bazaarbot.cache.get_redis"),
        ):
            from bazaarbot.tasks.appointment_tasks import send_appointment_reminder

            result = send_appointment_reminder.delay(1, "test-tenant").get()

        assert result["success"] is True
        assert len(sent_messages) == 1
        assert "appointment" in sent_messages[0].lower()

    def test_not_found_returns_failure(self):
        """Returns failure when appointment ID is not in the list."""
        with (
            patch(
                "bazaarbot.database_pg.get_appointments",
                return_value=[],
            ),
            patch("bazaarbot.cache.get_redis"),
        ):
            from bazaarbot.tasks.appointment_tasks import send_appointment_reminder

            result = send_appointment_reminder.delay(999, "test-tenant").get()

        assert result["success"] is False
        assert result["reason"] == "not_found"


# ═══════════════════════════════════════════════════════════════════════════
# Cache layer
# ═══════════════════════════════════════════════════════════════════════════

class TestCacheLayer:
    """Unit tests for bazaarbot.cache using a mocked Redis client."""

    def _make_mock_redis(self, stored: dict | None = None) -> MagicMock:
        """Return a MagicMock that mimics an in-memory Redis store."""
        store: dict = {}
        if stored:
            store.update({k: json.dumps(v) for k, v in stored.items()})

        mock = MagicMock()
        mock.get.side_effect = lambda key: store.get(key)
        mock.setex.side_effect = lambda key, ttl, val: store.update({key: val})
        mock.delete.side_effect = lambda key: store.pop(key, None)
        mock.ping.return_value = True
        return mock

    def test_cache_set_and_get(self):
        """cache_get returns the value previously written by cache_set."""
        mock_redis = self._make_mock_redis()

        with patch("bazaarbot.cache.get_redis", return_value=mock_redis):
            from bazaarbot.cache import cache_get, cache_set

            cache_set("test_key", {"data": "value"}, ttl_seconds=60)
            result = cache_get("test_key")

        assert result == {"data": "value"}

    def test_cache_graceful_on_redis_down(self):
        """cache_get returns None (never raises) when Redis is unavailable."""
        mock_redis = MagicMock()
        mock_redis.get.side_effect = ConnectionError("Redis is down")

        with patch("bazaarbot.cache.get_redis", return_value=mock_redis):
            from bazaarbot.cache import cache_get

            result = cache_get("any_key")

        assert result is None

    def test_cache_set_returns_false_on_error(self):
        """cache_set returns False (never raises) when Redis is unavailable."""
        mock_redis = MagicMock()
        mock_redis.setex.side_effect = ConnectionError("Redis is down")

        with patch("bazaarbot.cache.get_redis", return_value=mock_redis):
            from bazaarbot.cache import cache_set

            result = cache_set("key", {"x": 1})

        assert result is False

    def test_cache_delete_silences_errors(self):
        """cache_delete does not raise when Redis is unavailable."""
        mock_redis = MagicMock()
        mock_redis.delete.side_effect = ConnectionError("Redis is down")

        with patch("bazaarbot.cache.get_redis", return_value=mock_redis):
            from bazaarbot.cache import cache_delete

            cache_delete("some_key")  # must not raise

    def test_health_check_ok(self):
        """health_check returns {"status": "ok"} when Redis responds."""
        mock_redis = self._make_mock_redis()

        with patch("bazaarbot.cache.get_redis", return_value=mock_redis):
            from bazaarbot.cache import health_check

            result = health_check()

        assert result == {"status": "ok"}

    def test_health_check_error(self):
        """health_check returns {"status": "error"} when Redis is down."""
        mock_redis = MagicMock()
        mock_redis.ping.side_effect = ConnectionError("Redis is down")

        with patch("bazaarbot.cache.get_redis", return_value=mock_redis):
            from bazaarbot.cache import health_check

            result = health_check()

        assert result["status"] == "error"


# ═══════════════════════════════════════════════════════════════════════════
# Inventory cache integration
# ═══════════════════════════════════════════════════════════════════════════

class TestInventoryCacheIntegration:
    """Verify that get_inventory() uses cache-aside correctly."""

    _DB_ITEMS = [{"product_name": "Rice", "quantity": 10, "sell_price": "150"}]

    def test_db_called_only_once_across_two_reads(self):
        """Second call to get_inventory returns cached data without hitting DB."""
        store: dict = {}
        mock_redis = MagicMock()
        mock_redis.get.side_effect = lambda key: store.get(key)
        mock_redis.setex.side_effect = lambda key, ttl, val: store.update({key: val})

        # Patch async_get_inventory to be a regular (non-coroutine) mock so that
        # _run never has to await anything, avoiding RuntimeWarning about an
        # unawaited coroutine in the test process.
        mock_async = MagicMock(return_value=self._DB_ITEMS)

        with (
            patch("bazaarbot.cache.get_redis", return_value=mock_redis),
            patch("bazaarbot.database_pg.async_get_inventory", mock_async),
            patch(
                "bazaarbot.database_pg._run",
                side_effect=lambda coro: self._DB_ITEMS,
            ) as mock_run,
        ):
            from bazaarbot.database_pg import get_inventory

            first = get_inventory("test-tenant")
            second = get_inventory("test-tenant")

        assert first == self._DB_ITEMS
        assert second == self._DB_ITEMS
        # _run (async DB call) must only execute once; second read hits cache.
        assert mock_run.call_count == 1
