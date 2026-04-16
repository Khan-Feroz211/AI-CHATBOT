"""Optional LLM fallback service for BazaarBot.

Supports OpenAI (gpt-4o-mini) and Groq (llama-3.1-8b-instant).
Activated only when USE_LLM_FALLBACK=true, a provider is set,
and a valid API key is present.  Never raises — always returns
gracefully so the TF-IDF path can take over on any failure.
"""

import logging
from typing import Optional

from bazaarbot.config import Config

SUPPORTED_PROVIDERS = ["openai", "groq", "none"]

logger = logging.getLogger(__name__)


def is_llm_enabled() -> bool:
    """Return True when LLM fallback is fully configured."""
    return (
        Config.USE_LLM_FALLBACK
        and Config.LLM_PROVIDER not in ("none", "")
        and bool(Config.LLM_API_KEY)
    )


def _build_system_prompt(
    tenant_data: dict,
    context: str,
    language: str,
) -> str:
    """Build the system prompt with business context and instructions."""
    name = tenant_data.get("name", "a business")
    city = tenant_data.get("city", "Pakistan")
    business_type = tenant_data.get("business_type", "retail")
    easypaisa = tenant_data.get("easypaisa_number", "N/A")
    jazzcash = tenant_data.get("jazzcash_number", "N/A")
    bank = tenant_data.get("bank_title", "N/A")

    # Language instruction based on detected script/language
    if language == "ur":
        lang_instruction = (
            "Respond in Roman Urdu (Urdu written in English letters). "
            "Example: 'Aap ka stock 50 units hai.'"
        )
    elif language == "en":
        lang_instruction = "Respond in English."
    else:
        # Mixed / ur-en default
        lang_instruction = (
            "Respond in Roman Urdu mixed with English "
            "(e.g. 'Aap ka stock 50 units hai, price 200 rupees hai')."
        )

    return f"""You are a helpful business assistant for {name} in {city}.

Business type: {business_type}

Payment methods available:
- Easypaisa: {easypaisa}
- JazzCash: {jazzcash}
- Bank: {bank}

Context from knowledge base:
{context}

Instructions:
- Keep responses short (2-4 sentences max)
- {lang_instruction}
- Be friendly and helpful
- Only answer based on the provided context
- If unsure, say "Mujhe yeh maloom nahi, please call karen"
"""


def _detect_language(query: str) -> str:
    """Detect query language: 'ur' (Urdu script), 'en', or 'ur-en' (mixed)."""
    urdu_range = range(0x0600, 0x06FF + 1)
    has_urdu = any(ord(ch) in urdu_range for ch in query)
    has_latin = any(ch.isascii() and ch.isalpha() for ch in query)
    if has_urdu and not has_latin:
        return "ur"
    if has_latin and not has_urdu:
        return "en"
    return "ur-en"


async def call_llm(
    query: str,
    context: str,
    tenant_data: dict,
    language: str = "ur-en",
) -> Optional[str]:
    """Call the configured LLM with business context.

    Returns the response string or None on failure.
    Never raises — always returns gracefully.

    Parameters
    ----------
    query:       The user's message.
    context:     Retrieved RAG context snippets (from LangChain or TF-IDF).
    tenant_data: Business info dict (name, city, payment numbers, etc.).
    language:    Hint for response language: 'ur', 'en', or 'ur-en'.
                 If not provided, auto-detected from query.
    """
    if not is_llm_enabled():
        return None

    # Auto-detect if caller passes the default placeholder
    if language == "ur-en":
        language = _detect_language(query)

    system_prompt = _build_system_prompt(tenant_data, context, language)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]

    try:
        if Config.LLM_PROVIDER == "openai":
            from openai import AsyncOpenAI  # type: ignore[import]

            client = AsyncOpenAI(api_key=Config.LLM_API_KEY)
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=300,
                temperature=0.3,
                timeout=8,
            )
            return resp.choices[0].message.content

        elif Config.LLM_PROVIDER == "groq":
            from groq import AsyncGroq  # type: ignore[import]

            client = AsyncGroq(api_key=Config.LLM_API_KEY)
            resp = await client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                max_tokens=300,
                temperature=0.3,
                timeout=8,
            )
            return resp.choices[0].message.content

        else:
            logger.warning(
                "LLM fallback: unsupported provider '%s'", Config.LLM_PROVIDER
            )
            return None

    except Exception as exc:
        logger.warning("LLM fallback failed: %s", exc)
        return None
