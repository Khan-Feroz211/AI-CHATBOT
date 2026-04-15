"""BazaarBot test suite — Pakistani market chatbot."""
import os
import sys
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Use an in-memory DB for tests
os.environ.setdefault("DATABASE_PATH", ":memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_PASSWORD", "testpass")

from bazaarbot.web.app import app as flask_app
from bazaarbot import database as db
from bazaarbot.nlp.rag_engine import RAGEngine, INTENT_PATTERNS
from bazaarbot.bot.intent_router import process_message
from bazaarbot.bot.menu import get_main_menu, get_payment_menu


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    """Each test gets its own SQLite database."""
    import bazaarbot.config as cfg
    import bazaarbot.web.app as web_app
    import importlib

    db_path = str(tmp_path / "test.db")
    cfg.config.DATABASE_PATH = db_path
    importlib.reload(db)
    db.init_db()

    # Reset flask app's lazy-init flag
    web_app._db_initialised = False

    yield

    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False
    with flask_app.test_client() as c:
        yield c


# ── NLP engine tests ──────────────────────────────────────────────────────

class TestRAGEngine:
    def setup_method(self):
        self.engine = RAGEngine()
        self.engine.load_tenant_docs("default")

    def test_greet_intents(self):
        for phrase in ("hi", "hello", "salam", "aoa", "menu"):
            assert self.engine.classify_intent(phrase) == "greet", phrase

    def test_stock_intent(self):
        assert self.engine.classify_intent("stock check karein") == "stock_check"
        assert self.engine.classify_intent("kitna maal hai") == "stock_check"

    def test_payment_intent(self):
        assert self.engine.classify_intent("easypaisa payment details") == "payment"
        assert self.engine.classify_intent("jazzcash se payment karna") == "payment"

    def test_market_intent(self):
        assert self.engine.classify_intent("karachi market kahan hai") == "market_finder"

    def test_appointment_intent(self):
        assert self.engine.classify_intent("appointment book karna") == "appointment"

    def test_sell_intent(self):
        assert self.engine.classify_intent("item becha 5") == "sell"

    def test_help_intent(self):
        assert self.engine.classify_intent("madad chahiye") == "help"

    def test_retrieve_pakistan_markets(self):
        snippet = self.engine.retrieve("karachi wholesale market")
        assert len(snippet) > 0

    def test_retrieve_payments(self):
        snippet = self.engine.retrieve("easypaisa jazzcash payment")
        assert "EasyPaisa" in snippet or "JazzCash" in snippet

    def test_all_intents_covered(self):
        """All key intents must be classifiable from their most distinct phrase."""
        key_samples = {
            "greet": "salam",
            "stock_check": "kitna maal hai",
            "add_stock": "naya maal add karo",
            "sell": "item becha",
            "order": "order karna hai",
            "payment": "easypaisa payment details",
            "market_finder": "karachi wholesale mandi",
            "appointment": "appointment book karna",
            "transactions": "order history",
            "price": "rate kya hai",
            "help": "madad chahiye",
            "escalate": "insan se baat karo",
        }
        for intent, phrase in key_samples.items():
            result = self.engine.classify_intent(phrase)
            assert result == intent, (
                f"Expected {intent}, got {result} for '{phrase}'"
            )


# ── Database tests ────────────────────────────────────────────────────────

class TestDatabase:
    def test_init_db_creates_tables(self):
        items = db.get_inventory("default")
        assert isinstance(items, list)

    def test_upsert_and_get_product(self):
        db.upsert_product("default", "Test Atta", quantity=100, unit="kg",
                          sell_price=70)
        item = db.get_product("default", "test atta")
        assert item is not None
        assert item["quantity"] == 100

    def test_update_stock_delta(self):
        db.upsert_product("default", "Chawal", quantity=50, unit="kg",
                          sell_price=180)
        db.update_stock("default", "Chawal", -10)
        item = db.get_product("default", "chawal")
        assert item["quantity"] == 40

    def test_update_stock_no_negative(self):
        db.upsert_product("default", "Sugar", quantity=5, unit="kg",
                          sell_price=140)
        db.update_stock("default", "Sugar", -100)
        item = db.get_product("default", "sugar")
        assert item["quantity"] == 0

    def test_create_order(self):
        db.upsert_product("default", "Oil", quantity=20, unit="litre",
                          sell_price=420)
        ref, total = db.create_order("default", "+923000000000", "Oil", 2, 420)
        assert ref.startswith("ORD-")
        assert total == 840.0
        orders = db.get_orders("default")
        assert len(orders) >= 1

    def test_sessions(self):
        db.set_session("default", "+923001", "placing_order", {"step": 1})
        sess = db.get_session("default", "+923001")
        assert sess["state"] == "placing_order"
        assert sess["context"]["step"] == 1
        db.clear_session("default", "+923001")
        assert db.get_session("default", "+923001")["state"] == "idle"

    def test_appointment_booking(self):
        apt_id = db.book_appointment(
            "default", "+923001", "Test User",
            "2099-12-31", "10:00", "Demo visit"
        )
        assert isinstance(apt_id, int)
        apts = db.get_appointments("default", upcoming_only=False)
        assert any(a["id"] == apt_id for a in apts)

    def test_low_stock_detection(self):
        db.upsert_product("default", "LowItem", quantity=2, unit="pieces",
                          sell_price=50, reorder_level=10)
        low = db.get_low_stock("default")
        names = [i["product_name"] for i in low]
        assert "LowItem" in names

    def test_analytics(self):
        analytics = db.get_analytics("default")
        assert "total_messages" in analytics
        assert "total_revenue" in analytics


# ── Intent router tests ───────────────────────────────────────────────────

class TestIntentRouter:
    def test_greet_returns_menu(self):
        r = process_message("+923001", "hi")
        assert "BazaarBot" in r or "BazaarBot" in r

    def test_stock_check(self):
        r = process_message("+923001", "1")
        assert "Stock" in r or "inventory" in r.lower()

    def test_add_stock(self):
        r = process_message("+923001", "add product TestMaal 50 kg 80")
        assert "✅" in r or "add" in r.lower()

    def test_sell_flow(self):
        db.upsert_product("default", "Atta", quantity=100, unit="kg",
                          sell_price=70)
        r = process_message("+923001", "sell Atta 5")
        assert "Sale" in r or "✅" in r

    def test_payment_info(self):
        r = process_message("+923001", "payment")
        assert "Payment" in r

    def test_market_karachi(self):
        r = process_message("+923001", "market karachi")
        assert "Karachi" in r or "Jodia" in r

    def test_market_lahore(self):
        r = process_message("+923001", "market lahore")
        assert "Lahore" in r or "Anarkali" in r

    def test_appointment_start(self):
        r = process_message("+923001", "5")
        assert "Appointment" in r or "appointment" in r.lower()

    def test_help(self):
        r = process_message("+923001", "help")
        assert "madad" in r.lower() or "BazaarBot" in r

    def test_menu_trigger(self):
        r = process_message("+923001", "menu")
        assert "BazaarBot" in r

    def test_session_multi_turn_add(self):
        process_message("+923099", "naya maal")
        r2 = process_message("+923099", "add product Daal 40 kg 250")
        assert "✅" in r2 or "Daal" in r2

    def test_unknown_fallback(self):
        r = process_message("+923001", "xyzxyz123gibberish_qwerty")
        assert len(r) > 5  # any response

    def test_order_insufficient_stock(self):
        db.upsert_product("default", "LimitedItem", quantity=1, unit="pieces",
                          sell_price=500)
        r = process_message("+923001", "order LimitedItem 999")
        assert "available" in r.lower() or "stock" in r.lower()


# ── Webhook tests ─────────────────────────────────────────────────────────

class TestWebhook:
    def test_webhook_get_health(self, client):
        r = client.get("/webhook")
        assert r.status_code == 200

    def test_webhook_post_hi(self, client):
        r = client.post("/webhook", data={
            "Body": "hi", "From": "whatsapp:+923000000000"
        })
        assert r.status_code == 200
        assert b"BazaarBot" in r.data or b"xml" in r.content_type.lower()

    def test_webhook_post_menu(self, client):
        r = client.post("/webhook", data={
            "Body": "menu", "From": "whatsapp:+923000000001"
        })
        assert r.status_code == 200

    def test_webhook_post_stock(self, client):
        r = client.post("/webhook", data={
            "Body": "1", "From": "whatsapp:+923000000002"
        })
        assert r.status_code == 200

    def test_webhook_hub_challenge(self, client):
        import bazaarbot.config as cfg
        cfg.config.WEBHOOK_VERIFY_TOKEN = "mytoken"
        r = client.get("/webhook", query_string={
            "hub.mode": "subscribe",
            "hub.verify_token": "mytoken",
            "hub.challenge": "1234567890"
        })
        assert r.status_code == 200
        assert b"1234567890" in r.data

    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        d = json.loads(r.data)
        assert d["status"] == "ok"


# ── REST API tests ────────────────────────────────────────────────────────

class TestRestAPI:
    def test_api_message_hi(self, client):
        r = client.post("/api/message",
                        data=json.dumps({"phone": "+923001", "message": "hi"}),
                        content_type="application/json")
        assert r.status_code == 200
        d = json.loads(r.data)
        assert "response" in d
        assert "intent" in d

    def test_api_message_missing_body(self, client):
        r = client.post("/api/message",
                        data=json.dumps({}),
                        content_type="application/json")
        assert r.status_code == 400

    def test_api_stock_intent(self, client):
        r = client.post("/api/message",
                        data=json.dumps({"phone": "+923001", "message": "stock"}),
                        content_type="application/json")
        d = json.loads(r.data)
        assert d["intent"] in ("stock_check", "greet", "unknown")


# ── Chat widget tests ─────────────────────────────────────────────────────

class TestChatWidget:
    def test_chat_post(self, client):
        r = client.post("/chat",
                        data=json.dumps({"message": "hello", "phone": "web1"}),
                        content_type="application/json")
        assert r.status_code == 200
        d = json.loads(r.data)
        assert "response" in d

    def test_chat_empty_message(self, client):
        r = client.post("/chat",
                        data=json.dumps({"message": ""}),
                        content_type="application/json")
        assert r.status_code == 200


# ── Menu/bot helpers ──────────────────────────────────────────────────────

def test_main_menu_contains_brand():
    m = get_main_menu("TestShop")
    assert "TestShop" in m
    assert "1" in m  # menu option 1


def test_payment_menu_no_config():
    m = get_payment_menu({})
    assert "Payment" in m


def test_payment_menu_easypaisa():
    tenant = {"easypaisa_number": "0311-1234567", "jazzcash_number": ""}
    m = get_payment_menu(tenant)
    assert "0311-1234567" in m

