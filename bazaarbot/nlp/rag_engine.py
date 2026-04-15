"""TF-IDF RAG engine — intent classification + knowledge retrieval.

No external API required. Runs fully offline.
"""
import os
import glob as _glob
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from bazaarbot.database import get_knowledge_docs

# ── Intent training phrases ───────────────────────────────────────────────
# Each list includes common English terms + Urdu romanisation used in
# Pakistani WhatsApp chats.
INTENT_PATTERNS = {
    "greet": [
        "hi", "hello", "hey", "start", "menu", "assalam", "salam", "aoa",
        "salaam", "adaab", "shuru", "start karo",
        "assalamualaikum", "waalaikumsalam",
    ],
    "stock_check": [
        "stock", "inventory", "maal", "saman", "check stock", "kitna maal hai",
        "available", "remaining", "kya hai", "kya available", "stock check",
        "show stock", "apna stock", "meri inventory", "items", "products",
    ],
    "add_stock": [
        "add stock", "stock add", "naya maal", "add product", "new product",
        "add item", "stock update", "update stock", "maal aaya", "naya item",
        "product add karo",
    ],
    "sell": [
        "becha", "sale", "sell", "sold", "customer ko diya", "nikala",
        "biko", "farokht", "sell product", "item becha", "bechna",
    ],
    "order": [
        "order", "buy", "purchase", "kharidna", "order karna", "place order",
        "mujhe chahiye", "send karo", "bhejo", "deliver karo",
    ],
    "payment": [
        "payment", "pay", "easypaisa", "jazzcash", "jazz cash", "easy paisa",
        "easypaisa number kya hai", "jazzcash number", "payment method",
        "paisay", "payment karna", "paise bhejo", "bank transfer", "iban",
        "how to pay", "paisa kaise", "payment info",
        "send money", "raast", "payment details",
    ],
    "market_finder": [
        "market", "bazaar", "wholesale", "supplier", "mandi", "karachi market",
        "lahore market", "where to buy", "sasta maal", "jodia bazaar",
        "anarkali", "market kahan", "thok bazaar", "market dhundhna",
    ],
    "appointment": [
        "appointment", "time", "milna", "visit", "mulaqat", "booking",
        "book karo", "schedule", "time lena", "meeting", "dukan aana",
        "book appointment", "appoint", "date fix", "milne ka waqt",
    ],
    "transactions": [
        "transaction", "history", "orders", "past orders", "purane order",
        "meri history", "purani sale", "order history", "meri orders",
    ],
    "price": [
        "price", "qeemat", "rate", "how much", "kitna", "kitni qeemat",
        "rate kya hai", "price batao", "daam", "bhav", "cost",
    ],
    "help": [
        "help", "madad", "guide", "how to", "kaise karu", "samajh nahi",
        "kaise", "bata do", "guide karo", "commands",
    ],
    "escalate": [
        "human", "agent", "manager", "malik", "owner", "baat karo",
        "insan se baat", "real person", "call karo", "phone karo",
        "support", "contact",
    ],
}

# Intents that have a built-in direct response (no handler needed)
_DIRECT_RESPONSES = {
    "escalate": (
        "👤 *Insan se Baat Karein*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Hum apke agent ko inform kar rahe hain.\n"
        "Business hours: Mon-Sat 9AM-6PM\n\n"
        "📱 Support: support@bazaarbot.pk\n"
        "⏰ Response time: 2-4 hours\n\n"
        "Wapas jaane ke liye *menu* likhein."
    ),
}

_KB_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")


class RAGEngine:
    def __init__(self):
        self._intent_vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        self._intent_labels: list = []
        self._intent_matrix = None
        self._doc_vectorizer = TfidfVectorizer(
            ngram_range=(1, 2), stop_words="english"
        )
        self._docs: list = []
        self._doc_matrix = None
        self._fit_intents()

    def _fit_intents(self):
        texts, labels = [], []
        for intent, phrases in INTENT_PATTERNS.items():
            for phrase in phrases:
                texts.append(phrase)
                labels.append(intent)
        if texts:
            self._intent_labels = labels
            self._intent_matrix = self._intent_vectorizer.fit_transform(texts)

    def classify_intent(self, query: str) -> str:
        """Return the most likely intent label for *query*."""
        if not query.strip():
            return "greet"
        q = self._intent_vectorizer.transform([query.lower()])
        sims = cosine_similarity(q, self._intent_matrix)[0]
        best = int(np.argmax(sims))
        if sims[best] < 0.12:
            return "unknown"
        return self._intent_labels[best]

    def load_tenant_docs(self, tenant_slug: str):
        """Reload knowledge docs from filesystem + DB for *tenant_slug*."""
        # Sanitize tenant_slug to prevent path traversal
        import re as _re
        safe_slug = _re.sub(r"[^a-zA-Z0-9_-]", "", tenant_slug)[:50]

        fs_docs = []
        # Load all .md files from the built-in knowledge_base directory
        for path in _glob.glob(os.path.join(_KB_DIR, "*.md")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                title = os.path.splitext(os.path.basename(path))[0]
                fs_docs.append({"title": title, "content": content})
            except OSError:
                pass
        # Per-tenant sub-folder (only if slug is safe and directory is under _KB_DIR)
        if safe_slug:
            tenant_kb = os.path.realpath(os.path.join(_KB_DIR, safe_slug))
            kb_base = os.path.realpath(_KB_DIR)
            if tenant_kb.startswith(kb_base + os.sep) and os.path.isdir(tenant_kb):
                for path in _glob.glob(os.path.join(tenant_kb, "*.md")):
                    real_path = os.path.realpath(path)
                    if not real_path.startswith(tenant_kb + os.sep):
                        continue
                    try:
                        with open(real_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        title = os.path.splitext(os.path.basename(real_path))[0]
                        fs_docs.append({"title": title, "content": content})
                    except OSError:
                        pass
        # DB docs
        db_docs = get_knowledge_docs(tenant_slug)
        all_docs = fs_docs + [
            {"title": d["title"], "content": d["content"]} for d in db_docs
        ]
        if all_docs:
            self._docs = all_docs
            texts = [f"{d['title']} {d['content']}" for d in all_docs]
            self._doc_matrix = self._doc_vectorizer.fit_transform(texts)

    def retrieve(self, query: str, top_k: int = 2) -> str:
        """Return the top-k most relevant knowledge snippets."""
        if self._doc_matrix is None or not self._docs:
            return ""
        try:
            q = self._doc_vectorizer.transform([query])
            sims = cosine_similarity(q, self._doc_matrix)[0]
            idxs = np.argsort(sims)[::-1][:top_k]
            snippets = [
                self._docs[i]["content"][:300].strip()
                for i in idxs if sims[i] > 0.05
            ]
            return "\n\n".join(snippets)
        except Exception:
            return ""

    def answer(self, query: str) -> tuple:
        """Return (intent, direct_response_or_None).

        If the intent has a built-in response, return it.
        For 'unknown', try to answer from knowledge base.
        Otherwise return (intent, None) so the router can handle it.
        """
        intent = self.classify_intent(query)
        direct = _DIRECT_RESPONSES.get(intent)
        if direct:
            return intent, direct
        if intent == "unknown":
            snippet = self.retrieve(query)
            if snippet:
                return intent, (
                    "🤖 *BazaarBot Assistant*\n"
                    "━━━━━━━━━━━━━━━━━━\n"
                    f"{snippet[:400]}\n"
                    "━━━━━━━━━━━━━━━━━━\n"
                    "Aur madad ke liye *menu* likhein."
                )
        return intent, None


_engine: RAGEngine | None = None


def get_engine() -> RAGEngine:
    global _engine
    if _engine is None:
        _engine = RAGEngine()
    return _engine
