"""NLP Processing Module"""
from .processor import (
    CPUFriendlyNLPProcessor,
    SentimentResult,
    IntentResult,
    EntityResult,
    SummaryResult
)

__all__ = [
    "CPUFriendlyNLPProcessor",
    "SentimentResult",
    "IntentResult",
    "EntityResult",
    "SummaryResult"
]
