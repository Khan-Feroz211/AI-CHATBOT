"""NLP Processing Module"""
from .processor import (
    CPUFriendlyNLPProcessor,
    EntityResult,
    IntentResult,
    SentimentResult,
    SummaryResult,
)

__all__ = [
    "CPUFriendlyNLPProcessor",
    "SentimentResult",
    "IntentResult",
    "EntityResult",
    "SummaryResult",
]
