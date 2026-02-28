import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from run import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def test_webhook_get(client):
    r = client.get("/webhook")
    assert r.status_code == 200

def test_webhook_post_hi(client):
    r = client.post("/webhook", data={"Body": "hi", "From": "whatsapp:+923000000000"})
    assert r.status_code == 200
    assert b"AI Business Bot" in r.data or b"Welcome" in r.data

def test_webhook_post_menu(client):
    r = client.post("/webhook", data={"Body": "menu", "From": "whatsapp:+923000000001"})
    assert r.status_code == 200

def test_webhook_post_unknown(client):
    r = client.post("/webhook", data={"Body": "xyz123random", "From": "whatsapp:+923000000002"})
    assert r.status_code == 200
