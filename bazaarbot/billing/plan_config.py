"""SaaS plan configuration for BazaarBot.

Three tiers: Starter / Business / Pro.
All pricing is in PKR (Pakistani Rupees).
"""
from dataclasses import dataclass, field

# ── Free-trial constants ───────────────────────────────────────────────────

FREE_TRIAL_DAYS = 14
FREE_TRIAL_MESSAGES = 200


# ── Plan dataclass ─────────────────────────────────────────────────────────

@dataclass
class PlanConfig:
    plan_id: str
    name: str
    price_pkr: int
    message_limit: int
    channels_allowed: list[str]
    llm_enabled: bool
    max_knowledge_docs: int
    api_access: bool
    features: list[str] = field(default_factory=list)


# ── Tier definitions ───────────────────────────────────────────────────────

PLANS: dict[str, PlanConfig] = {
    "starter": PlanConfig(
        plan_id="starter",
        name="Starter",
        price_pkr=999,
        message_limit=500,
        channels_allowed=["whatsapp"],
        llm_enabled=False,
        max_knowledge_docs=10,
        api_access=False,
        features=[
            "500 messages/month",
            "WhatsApp channel",
            "TF-IDF smart replies",
            "Inventory management",
            "Order tracking",
            "Email support",
        ],
    ),
    "business": PlanConfig(
        plan_id="business",
        name="Business",
        price_pkr=2999,
        message_limit=5000,
        channels_allowed=["whatsapp", "telegram"],
        llm_enabled=True,
        max_knowledge_docs=50,
        api_access=False,
        features=[
            "5,000 messages/month",
            "WhatsApp + Telegram",
            "AI-powered replies (LLM)",
            "Advanced analytics",
            "Appointment management",
            "Priority support",
        ],
    ),
    "pro": PlanConfig(
        plan_id="pro",
        name="Pro",
        price_pkr=7999,
        message_limit=999_999,
        channels_allowed=["whatsapp", "telegram", "web", "api"],
        llm_enabled=True,
        max_knowledge_docs=100,
        api_access=True,
        features=[
            "Unlimited messages",
            "All channels",
            "Full LLM integration",
            "Custom knowledge base (100 docs)",
            "REST API access",
            "Dedicated support",
            "White-label option",
        ],
    ),
}


# ── Helper functions ───────────────────────────────────────────────────────

def get_plan(plan_id: str) -> PlanConfig:
    """Return the PlanConfig for *plan_id*, falling back to Starter."""
    return PLANS.get(plan_id, PLANS["starter"])


def check_channel_allowed(plan_id: str, channel: str) -> bool:
    """Return True when *channel* is included in the plan's allowed channels."""
    return channel in get_plan(plan_id).channels_allowed


def check_llm_allowed(plan_id: str) -> bool:
    """Return True when the plan permits LLM-powered replies."""
    return get_plan(plan_id).llm_enabled


def check_api_allowed(plan_id: str) -> bool:
    """Return True when the plan includes REST API access."""
    return get_plan(plan_id).api_access
