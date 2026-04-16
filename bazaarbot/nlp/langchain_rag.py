"""LangChain RAG over the Markdown knowledge base.

Provides richer semantic retrieval using FAISS + HuggingFace embeddings
as a complement to the existing TF-IDF RAG engine.

Key design decisions:
- Uses sentence-transformers/all-MiniLM-L6-v2 (CPU-only, no API key)
- Loaded lazily; falls back silently to TF-IDF if anything goes wrong
- Thread-safe re-initialisation via module-level lock
- `retrieve_langchain()` always returns a string (never raises)
"""

import logging
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

KNOWLEDGE_BASE_DIR = Path(__file__).parent / "knowledge_base"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50

_vectorstore = None
_lock = threading.Lock()

# Module-level splitter — re-used across calls
_splitter = None


def _get_splitter():
    """Return a cached RecursiveCharacterTextSplitter (lazy import)."""
    global _splitter
    if _splitter is None:
        from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore[import]  # Optional dependency

        _splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", " "],
        )
    return _splitter


def load_knowledge_base(
    tenant_docs: Optional[list] = None,
) -> None:
    """Load all .md files from knowledge_base plus optional per-tenant docs.

    Builds a FAISS vectorstore in memory using HuggingFace embeddings
    (no API key required).  Called once at startup and whenever
    tenant documents change.

    Falls back silently to TF-IDF RAG if loading fails for any reason.

    Parameters
    ----------
    tenant_docs: Optional list of ``{"title": str, "content": str}``
                 dicts from the database for a specific tenant.
    """
    global _vectorstore

    try:
        from langchain.schema import Document  # type: ignore[import]  # Optional dependency
        from langchain_community.vectorstores import FAISS  # type: ignore[import]  # Optional dependency
        from langchain_community.embeddings import HuggingFaceEmbeddings  # type: ignore[import]  # Optional dependency
    except ImportError as exc:
        logger.warning(
            "LangChain dependencies not installed, skipping LangChain RAG: %s", exc
        )
        return

    splitter = _get_splitter()
    docs: list = []

    # Load built-in .md knowledge base files
    for md_file in sorted(KNOWLEDGE_BASE_DIR.glob("*.md")):
        try:
            text = md_file.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("Could not read %s: %s", md_file, exc)
            continue
        for chunk in splitter.split_text(text):
            docs.append(
                Document(
                    page_content=chunk,
                    metadata={"source": md_file.name},
                )
            )

    # Load optional per-tenant documents from the database
    if tenant_docs:
        for doc in tenant_docs:
            content = doc.get("content", "")
            if not content:
                continue
            for chunk in splitter.split_text(content):
                docs.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "source": "tenant",
                            "title": doc.get("title", ""),
                        },
                    )
                )

    if not docs:
        logger.warning("LangChain RAG: no documents found, vectorstore not built.")
        return

    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBED_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        new_store = FAISS.from_documents(docs, embeddings)
        with _lock:
            _vectorstore = new_store
        logger.info(
            "LangChain RAG: vectorstore built with %d chunks.", len(docs)
        )
    except Exception as exc:
        logger.warning(
            "LangChain RAG load failed: %s. Using TF-IDF fallback.", exc
        )
        with _lock:
            _vectorstore = None


def retrieve_langchain(
    query: str,
    top_k: int = 3,
) -> str:
    """Retrieve the top-k relevant chunks for *query*.

    Returns a single concatenated context string, or an empty string
    when the vectorstore is not loaded or retrieval fails.
    """
    with _lock:
        store = _vectorstore

    if store is None:
        return ""

    try:
        results = store.similarity_search(query, k=top_k)
        return "\n\n".join(r.page_content for r in results)
    except Exception as exc:
        logger.warning("LangChain retrieval failed: %s", exc)
        return ""
