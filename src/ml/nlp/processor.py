"""
CPU-friendly NLP Processing Module
Provides sentiment analysis, intent classification, NER, and summarization
No GPU required - uses lightweight transformers
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Try importing lightweight transformers
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers not available - NLP features will use fallback")

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import sent_tokenize, word_tokenize
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logger.warning("nltk not available")


@dataclass
class SentimentResult:
    """Sentiment analysis result"""
    label: str
    score: float
    
    def to_dict(self) -> Dict:
        return {"label": self.label, "score": round(self.score, 4)}


@dataclass
class IntentResult:
    """Intent classification result"""
    intent: str
    confidence: float
    sub_intents: List[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "intent": self.intent,
            "confidence": round(self.confidence, 4),
            "sub_intents": self.sub_intents or []
        }


@dataclass
class EntityResult:
    """Named entity recognition result"""
    entity: str
    label: str
    start: int
    end: int
    score: float
    
    def to_dict(self) -> Dict:
        return {
            "entity": self.entity,
            "label": self.label,
            "position": {"start": self.start, "end": self.end},
            "confidence": round(self.score, 4)
        }


@dataclass
class SummaryResult:
    """Text summarization result"""
    original_length: int
    summary: str
    summary_length: int
    compression_ratio: float
    
    def to_dict(self) -> Dict:
        return {
            "original_length": self.original_length,
            "summary": self.summary,
            "summary_length": self.summary_length,
            "compression_ratio": round(self.compression_ratio, 2)
        }


class CPUFriendlyNLPProcessor:
    """
    NLP processor optimized for CPU usage
    Uses lightweight models that can run on CPU without GPU
    """
    
    def __init__(self):
        self.sentiment_pipeline = None
        self.intent_pipeline = None
        self.ner_pipeline = None
        self.summarizer_pipeline = None
        self.cache_dir = Path("./data/nlp_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._init_pipelines()
        
        # Intent patterns for fallback classification
        self.intent_patterns = {
            "greeting": ["hello", "hi", "hey", "greetings", "good morning", "good afternoon"],
            "question": ["what", "who", "when", "where", "why", "how", "can you", "could you"],
            "command": ["please", "do", "make", "create", "send", "delete", "update"],
            "help": ["help", "support", "assist", "problem", "issue", "error", "bug"],
            "feedback": ["good", "bad", "great", "poor", "awesome", "terrible", "feedback"],
            "goodbye": ["bye", "goodbye", "farewell", "see you", "cya", "ttyl"]
        }
    
    def _init_pipelines(self):
        """Initialize HuggingFace pipelines with lightweight models"""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers not available - using fallback methods")
            return
        
        try:
            # Sentiment analysis - lightweight DistilBERT
            logger.info("Loading sentiment analysis pipeline...")
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=-1  # CPU only
            )
            
            # Intent classification - uses zero-shot classification
            logger.info("Loading intent classification pipeline...")
            self.intent_pipeline = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=-1  # CPU only
            )
            
            # Named Entity Recognition - lightweight DistilBERT
            logger.info("Loading NER pipeline...")
            self.ner_pipeline = pipeline(
                "ner",
                model="distilbert-base-uncased",
                aggregation_strategy="simple",
                device=-1  # CPU only
            )
            
            logger.info("All NLP pipelines loaded successfully")
            
        except Exception as e:
            logger.error(f"Error initializing NLP pipelines: {e}")
            logger.info("Will use fallback methods")
    
    def analyze_sentiment(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of text
        Returns: positive, negative, or neutral
        """
        if not text or len(text.strip()) == 0:
            return SentimentResult(label="neutral", score=0.0)
        
        try:
            if self.sentiment_pipeline:
                result = self.sentiment_pipeline(text[:512])[0]  # Limit to 512 tokens
                label = result["label"].lower()
                score = result["score"]
                return SentimentResult(label=label, score=score)
            else:
                return self._fallback_sentiment(text)
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return self._fallback_sentiment(text)
    
    def _fallback_sentiment(self, text: str) -> SentimentResult:
        """Fallback sentiment analysis using keyword matching"""
        text_lower = text.lower()
        
        positive_words = {"good", "great", "awesome", "excellent", "love", "amazing", "wonderful", "fantastic"}
        negative_words = {"bad", "hate", "terrible", "awful", "poor", "horrible", "worst", "stupid"}
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            return SentimentResult(label="positive", score=0.7 + (pos_count * 0.05))
        elif neg_count > pos_count:
            return SentimentResult(label="negative", score=0.7 + (neg_count * 0.05))
        else:
            return SentimentResult(label="neutral", score=0.5)
    
    def classify_intent(self, text: str, custom_intents: Optional[List[str]] = None) -> IntentResult:
        """
        Classify user intent
        """
        if not text or len(text.strip()) == 0:
            return IntentResult(intent="unknown", confidence=0.0)
        
        try:
            intents = custom_intents or list(self.intent_patterns.keys())
            
            if self.intent_pipeline:
                result = self.intent_pipeline(text[:512], intents)
                return IntentResult(
                    intent=result["labels"][0],
                    confidence=result["scores"][0],
                    sub_intents=result["labels"][1:3]
                )
            else:
                return self._fallback_intent_classification(text)
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return self._fallback_intent_classification(text)
    
    def _fallback_intent_classification(self, text: str) -> IntentResult:
        """Fallback intent classification using pattern matching"""
        text_lower = text.lower()
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            matches = sum(1 for pattern in patterns if pattern in text_lower)
            intent_scores[intent] = matches
        
        if not any(intent_scores.values()):
            return IntentResult(intent="unknown", confidence=0.0)
        
        best_intent = max(intent_scores, key=intent_scores.get)
        score = intent_scores[best_intent]
        confidence = min(0.5 + (score * 0.1), 0.99)
        
        return IntentResult(intent=best_intent, confidence=confidence)
    
    def extract_entities(self, text: str) -> List[EntityResult]:
        """
        Extract named entities (person, location, organization, etc.)
        """
        if not text or len(text.strip()) == 0:
            return []
        
        try:
            if self.ner_pipeline:
                entities = self.ner_pipeline(text[:512])
                results = []
                for entity in entities:
                    if entity.get("score", 0) > 0.7:  # Filter low confidence
                        results.append(EntityResult(
                            entity=entity["word"],
                            label=entity["entity_group"],
                            start=entity.get("start", 0),
                            end=entity.get("end", 0),
                            score=entity["score"]
                        ))
                return results
            else:
                return self._fallback_ner(text)
        except Exception as e:
            logger.error(f"NER error: {e}")
            return self._fallback_ner(text)
    
    def _fallback_ner(self, text: str) -> List[EntityResult]:
        """Fallback NER using basic patterns"""
        results = []
        
        # Simple pattern for email addresses
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            results.append(EntityResult(
                entity=match.group(),
                label="EMAIL",
                start=match.start(),
                end=match.end(),
                score=0.95
            ))
        
        # Simple pattern for phone numbers
        phone_pattern = r'\b\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}\b'
        for match in re.finditer(phone_pattern, text):
            results.append(EntityResult(
                entity=match.group(),
                label="PHONE",
                start=match.start(),
                end=match.end(),
                score=0.90
            ))
        
        return results
    
    def summarize_text(self, text: str, max_length: int = 150, min_length: int = 50) -> SummaryResult:
        """
        Summarize text using abstractive summarization
        max_length: maximum summary length in tokens
        min_length: minimum summary length in tokens
        """
        if not text or len(text.strip()) < 100:
            return SummaryResult(
                original_length=len(text),
                summary=text,
                summary_length=len(text),
                compression_ratio=1.0
            )
        
        try:
            if self.summarizer_pipeline:
                summary = self.summarizer_pipeline(text[:1024], max_length=max_length, min_length=min_length)
                summary_text = summary[0]["summary_text"]
            else:
                summary_text = self._fallback_summarize(text, max_length)
            
            compression_ratio = len(text) / len(summary_text) if summary_text else 1.0
            
            return SummaryResult(
                original_length=len(text),
                summary=summary_text,
                summary_length=len(summary_text),
                compression_ratio=compression_ratio
            )
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return self._fallback_summarize_result(text)
    
    def _fallback_summarize(self, text: str, max_length: int = 150) -> str:
        """Fallback summarization using sentence extraction"""
        if not NLTK_AVAILABLE:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        try:
            sentences = sent_tokenize(text)
            summary_sentence_count = max(1, len(sentences) // 3)
            return " ".join(sentences[:summary_sentence_count])
        except:
            return text[:max_length] + "..." if len(text) > max_length else text
    
    def _fallback_summarize_result(self, text: str) -> SummaryResult:
        """Fallback summarization result"""
        summary = self._fallback_summarize(text)
        return SummaryResult(
            original_length=len(text),
            summary=summary,
            summary_length=len(summary),
            compression_ratio=len(text) / len(summary) if summary else 1.0
        )
    
    def extract_keywords(self, text: str, num_keywords: int = 5) -> List[Tuple[str, float]]:
        """
        Extract keywords using TF-IDF-like scoring
        Returns list of (keyword, score) tuples
        """
        if not text or len(text.strip()) == 0:
            return []
        
        try:
            if not NLTK_AVAILABLE:
                return []
            
            words = word_tokenize(text.lower())
            stop_words = set(stopwords.words('english'))
            
            # Filter out stopwords and short words
            filtered_words = [
                word for word in words 
                if word.isalnum() and len(word) > 2 and word not in stop_words
            ]
            
            # Calculate frequency
            from collections import Counter
            word_freq = Counter(filtered_words)
            
            # Sort and return top keywords
            keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:num_keywords]
            
            # Normalize scores
            if keywords:
                max_freq = keywords[0][1]
                keywords = [(word, freq / max_freq) for word, freq in keywords]
            
            return keywords
        except Exception as e:
            logger.error(f"Keyword extraction error: {e}")
            return []
