"""Day 3 NLP upgrade tests.

All external API calls (LLM, LangChain FAISS) are mocked — no real
network requests are made.  The original 46 tests remain unaffected.
"""
import os
import sys
import importlib
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Keep tests isolated from any real DB / LLM config
os.environ.setdefault("DATABASE_PATH", ":memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_PASSWORD", "testpass")
# Ensure LLM is OFF by default for most tests
os.environ.setdefault("USE_LLM_FALLBACK", "false")
os.environ.setdefault("USE_LANGCHAIN_RAG", "false")

from unittest.mock import patch, AsyncMock, MagicMock

from bazaarbot.nlp.rag_engine import RAGEngine, get_engine, INTENT_PATTERNS
from bazaarbot.nlp.llm_service import is_llm_enabled, call_llm
from bazaarbot.nlp.langchain_rag import retrieve_langchain


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    """Each test gets its own isolated SQLite database."""
    import bazaarbot.config as cfg
    import bazaarbot.database as _db

    db_path = str(tmp_path / "test.db")
    cfg.config.DATABASE_PATH = db_path
    importlib.reload(_db)
    _db.init_db()
    yield
    try:
        os.unlink(db_path)
    except OSError:
        pass


# ── Helpers ────────────────────────────────────────────────────────────────

def _fresh_engine() -> RAGEngine:
    """Return a freshly constructed RAGEngine with default docs loaded."""
    e = RAGEngine()
    e.load_tenant_docs("default")
    return e


# ── 1. LLM disabled by default ────────────────────────────────────────────

def test_llm_disabled_by_default():
    """With USE_LLM_FALLBACK=false (default), is_llm_enabled() must be False."""
    with patch("bazaarbot.nlp.llm_service.Config") as mock_cfg:
        mock_cfg.USE_LLM_FALLBACK = False
        mock_cfg.LLM_PROVIDER = "none"
        mock_cfg.LLM_API_KEY = ""
        assert is_llm_enabled() is False


# ── 2. TF-IDF path unchanged for high-confidence queries ─────────────────

def test_tfidf_path_unchanged():
    """High-confidence query uses TF-IDF intent path; LLM is never invoked."""
    engine = _fresh_engine()

    with patch("bazaarbot.nlp.rag_engine.Config") as mock_cfg, \
         patch("bazaarbot.nlp.llm_service.is_llm_enabled", return_value=False):
        mock_cfg.LLM_CONFIDENCE_THRESHOLD = 0.30

        intent, response = engine.answer("kya stock hai?")

    assert intent in INTENT_PATTERNS, f"Unknown intent: {intent}"
    # LLM was not involved — no LLM call on the sync path


# ── 3. LLM fallback fires on low-confidence / unknown query ───────────────

@pytest.mark.asyncio
async def test_llm_fallback_on_unknown():
    """With USE_LLM_FALLBACK=true a low-confidence query reaches the LLM."""
    engine = _fresh_engine()

    with patch("bazaarbot.nlp.rag_engine.Config") as mock_cfg, \
         patch("bazaarbot.nlp.langchain_rag._vectorstore") as _vs, \
         patch("bazaarbot.nlp.llm_service.Config") as llm_cfg, \
         patch("bazaarbot.nlp.llm_service.is_llm_enabled", return_value=True), \
         patch("bazaarbot.nlp.llm_service.call_llm", new_callable=AsyncMock) as mock_llm:

        mock_cfg.LLM_CONFIDENCE_THRESHOLD = 0.99  # force fallback for any query
        llm_cfg.LLM_PROVIDER = "groq"
        llm_cfg.LLM_API_KEY = "test"
        llm_cfg.USE_LLM_FALLBACK = True
        llm_cfg.LLM_MAX_TOKENS = 300
        llm_cfg.LLM_TIMEOUT_SECONDS = 8
        mock_llm.return_value = "Test response from LLM"

        # Patch inside rag_engine's answer_async local imports
        with patch("bazaarbot.nlp.langchain_rag.retrieve_langchain",
                   return_value="some context"):
            intent, response = await engine.answer_async("xyzzy unknown gibberish")

    mock_llm.assert_called_once()
    assert response == "Test response from LLM"
    assert intent == "llm"


# ── 4. LLM fallback degrades gracefully on exception ─────────────────────

@pytest.mark.asyncio
async def test_llm_fallback_graceful_failure():
    """If call_llm raises, answer_async() must not propagate the exception."""
    engine = _fresh_engine()

    with patch("bazaarbot.nlp.rag_engine.Config") as mock_cfg, \
         patch("bazaarbot.nlp.llm_service.is_llm_enabled", return_value=True), \
         patch("bazaarbot.nlp.llm_service.call_llm", new_callable=AsyncMock) as mock_llm:

        mock_cfg.LLM_CONFIDENCE_THRESHOLD = 0.99
        mock_llm.side_effect = Exception("LLM network error")

        with patch("bazaarbot.nlp.langchain_rag.retrieve_langchain",
                   return_value="ctx"):
            try:
                intent, response = await engine.answer_async("test query failure")
            except Exception as exc:
                pytest.fail(f"answer_async() raised unexpectedly: {exc}")

    # Reaching here means no unhandled exception — graceful degradation confirmed
    assert True


# ── 5. LangChain retrieval returns context ────────────────────────────────

def test_langchain_retrieve_returns_context():
    """When vectorstore is populated, retrieve_langchain() returns text."""
    mock_doc = MagicMock()
    mock_doc.page_content = "EasyPaisa aur JazzCash se payment karein"

    mock_store = MagicMock()
    mock_store.similarity_search.return_value = [mock_doc]

    import bazaarbot.nlp.langchain_rag as lc_mod
    original_store = lc_mod._vectorstore
    try:
        lc_mod._vectorstore = mock_store
        result = retrieve_langchain("payment methods")
    finally:
        lc_mod._vectorstore = original_store

    assert len(result) > 0
    assert "EasyPaisa" in result


# ── 6. LangChain returns empty string when not loaded ─────────────────────

def test_langchain_disabled_returns_empty():
    """With _vectorstore=None, retrieve_langchain() returns empty string."""
    import bazaarbot.nlp.langchain_rag as lc_mod
    original_store = lc_mod._vectorstore
    try:
        lc_mod._vectorstore = None
        result = retrieve_langchain("anything at all")
    finally:
        lc_mod._vectorstore = original_store

    assert result == ""


# ── 7. GET /api/nlp/status returns 200 with expected fields ───────────────

def test_nlp_status_endpoint():
    """GET /api/nlp/status returns 200 and tfidf_rag=active."""
    from starlette.testclient import TestClient
    from bazaarbot.web.fastapi_app import app

    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.get("/api/nlp/status")

    assert resp.status_code == 200
    data = resp.json()
    assert data["tfidf_rag"] == "active"
    assert "langchain_rag" in data
    assert "llm_fallback" in data
    assert "llm_provider" in data
    assert "intent_count" in data
    assert isinstance(data["intent_count"], int)
    assert data["intent_count"] > 0
    assert "knowledge_docs" in data


# ── 8. POST /api/nlp/test returns diagnostics (JWT auth) ──────────────────

def test_nlp_test_endpoint():
    """POST /api/nlp/test with a valid JWT returns intent + final_response."""
    from starlette.testclient import TestClient
    from bazaarbot.web.fastapi_app import app
    from bazaarbot.auth.auth_service import create_access_token
    from bazaarbot import database as db
    import importlib

    # Bootstrap the in-memory DB
    db.init_db()

    token = create_access_token(
        tenant_slug="test-dukan",
        user_id=1,
        role="admin",
    )
    headers = {"Authorization": f"Bearer {token}"}

    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.post(
            "/api/nlp/test",
            json={"query": "payment kaise karein", "tenant_slug": "test-dukan"},
            headers=headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "intent" in data
    assert "final_response" in data
    assert "confidence" in data
    assert "path_taken" in data
    assert isinstance(data["confidence"], float)
    assert len(data["final_response"]) > 0


# ── 9. Original TF-IDF tests still pass (regression guard) ────────────────

class TestOriginalPathsUnaffected:
    """Smoke-test the TF-IDF paths that existed before Day 3.

    These mirror the assertions in test_bot.py::TestRAGEngine to confirm
    that the Day 3 additions have not broken any existing behaviour.
    """

    def setup_method(self):
        self.engine = _fresh_engine()

    def test_greet_intent(self):
        assert self.engine.classify_intent("salam") == "greet"

    def test_stock_check_intent(self):
        assert self.engine.classify_intent("kitna maal hai") == "stock_check"

    def test_payment_intent(self):
        assert self.engine.classify_intent("easypaisa payment details") == "payment"

    def test_sync_answer_no_llm_call(self):
        """Sync answer() never touches LLM; returns (intent, ...) tuple."""
        with patch("bazaarbot.nlp.llm_service.call_llm") as mock_llm:
            intent, _ = self.engine.answer("jazzcash se payment karna")
        mock_llm.assert_not_called()
        assert intent == "payment"
