"""
NLP API endpoints for sentiment analysis, intent classification, etc.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.ml.nlp.processor import (
    CPUFriendlyNLPProcessor,
    EntityResult,
    IntentResult,
    SentimentResult,
    SummaryResult,
)

# Initialize router
router = APIRouter(prefix="/api/v1/nlp", tags=["NLP"])

# Initialize processor
nlp_processor = CPUFriendlyNLPProcessor()


# ============ Request/Response Models ============


class SentimentAnalysisRequest(BaseModel):
    """Sentiment analysis request"""

    text: str = Field(..., min_length=1, max_length=2000)


class SentimentAnalysisResponse(BaseModel):
    """Sentiment analysis response"""

    label: str
    score: float
    status: str = "success"


class IntentClassificationRequest(BaseModel):
    """Intent classification request"""

    text: str = Field(..., min_length=1, max_length=2000)
    custom_intents: Optional[List[str]] = None


class IntentClassificationResponse(BaseModel):
    """Intent classification response"""

    intent: str
    confidence: float
    sub_intents: List[str] = []
    status: str = "success"


class EntityExtractionRequest(BaseModel):
    """Entity extraction request"""

    text: str = Field(..., min_length=1, max_length=2000)


class EntityResult_API(BaseModel):
    """Entity result"""

    entity: str
    label: str
    position: dict
    confidence: float


class EntityExtractionResponse(BaseModel):
    """Entity extraction response"""

    entities: List[EntityResult_API]
    entity_count: int
    status: str = "success"


class TextSummarizationRequest(BaseModel):
    """Text summarization request"""

    text: str = Field(..., min_length=100, max_length=4096)
    max_length: int = Field(150, ge=50, le=500)
    min_length: int = Field(50, ge=10, le=200)


class TextSummarizationResponse(BaseModel):
    """Text summarization response"""

    original_length: int
    summary: str
    summary_length: int
    compression_ratio: float
    status: str = "success"


class KeywordExtractionRequest(BaseModel):
    """Keyword extraction request"""

    text: str = Field(..., min_length=1, max_length=4096)
    num_keywords: int = Field(5, ge=1, le=20)


class Keyword(BaseModel):
    """Keyword with score"""

    text: str
    score: float


class KeywordExtractionResponse(BaseModel):
    """Keyword extraction response"""

    keywords: List[Keyword]
    status: str = "success"


class ComprehensiveAnalysisRequest(BaseModel):
    """Request for comprehensive NLP analysis"""

    text: str = Field(..., min_length=1, max_length=2000)
    include_sentiment: bool = True
    include_intent: bool = True
    include_entities: bool = True
    include_keywords: bool = True


class ComprehensiveAnalysisResponse(BaseModel):
    """Comprehensive NLP analysis response"""

    sentiment: Optional[SentimentAnalysisResponse] = None
    intent: Optional[IntentClassificationResponse] = None
    entities: Optional[EntityExtractionResponse] = None
    keywords: Optional[KeywordExtractionResponse] = None
    status: str = "success"


# ============ Endpoints ============


@router.post("/sentiment", response_model=SentimentAnalysisResponse)
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
) -> SentimentAnalysisResponse:
    """
    Analyze sentiment of input text.

    Returns:
    - label: "positive", "negative", or "neutral"
    - score: confidence score (0-1)

    Example:
    ```json
    {
        "text": "I love this product! It's amazing!"
    }
    ```
    """
    try:
        result: SentimentResult = nlp_processor.analyze_sentiment(request.text)
        return SentimentAnalysisResponse(label=result.label, score=result.score)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Sentiment analysis failed: {str(e)}"
        )


@router.post("/intent", response_model=IntentClassificationResponse)
async def classify_intent(
    request: IntentClassificationRequest,
) -> IntentClassificationResponse:
    """
    Classify user intent from text.

    Returns:
    - intent: classified intent (greeting, question, command, help, etc.)
    - confidence: confidence score (0-1)
    - sub_intents: alternative intents ranked by confidence

    Example:
    ```json
    {
        "text": "Can you help me with my order?"
    }
    ```
    """
    try:
        result: IntentResult = nlp_processor.classify_intent(
            request.text, custom_intents=request.custom_intents
        )
        return IntentClassificationResponse(
            intent=result.intent,
            confidence=result.confidence,
            sub_intents=result.sub_intents or [],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Intent classification failed: {str(e)}"
        )


@router.post("/entities", response_model=EntityExtractionResponse)
async def extract_entities(
    request: EntityExtractionRequest,
) -> EntityExtractionResponse:
    """
    Extract named entities from text.

    Returns:
    - entities: list of extracted entities with types (PERSON, ORG, LOCATION, EMAIL, PHONE, etc.)

    Example:
    ```json
    {
        "text": "John Smith from Microsoft can be reached at john@example.com or 555-1234"
    }
    ```
    """
    try:
        entities: List[EntityResult] = nlp_processor.extract_entities(request.text)

        entity_results = [
            EntityResult_API(
                entity=e.entity,
                label=e.label,
                position={"start": e.start, "end": e.end},
                confidence=e.score,
            )
            for e in entities
        ]

        return EntityExtractionResponse(
            entities=entity_results, entity_count=len(entity_results)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Entity extraction failed: {str(e)}"
        )


@router.post("/summarize", response_model=TextSummarizationResponse)
async def summarize_text(
    request: TextSummarizationRequest,
) -> TextSummarizationResponse:
    """
    Summarize long text into concise summary.

    Returns:
    - summary: summarized text
    - compression_ratio: original_length / summary_length

    Example:
    ```json
    {
        "text": "Long article text here...",
        "max_length": 150,
        "min_length": 50
    }
    ```
    """
    try:
        result: SummaryResult = nlp_processor.summarize_text(
            request.text, max_length=request.max_length, min_length=request.min_length
        )
        return TextSummarizationResponse(
            original_length=result.original_length,
            summary=result.summary,
            summary_length=result.summary_length,
            compression_ratio=result.compression_ratio,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")


@router.post("/keywords", response_model=KeywordExtractionResponse)
async def extract_keywords(
    request: KeywordExtractionRequest,
) -> KeywordExtractionResponse:
    """
    Extract important keywords from text.

    Returns:
    - keywords: list of extracted keywords with importance scores

    Example:
    ```json
    {
        "text": "Python is great for machine learning and data science...",
        "num_keywords": 5
    }
    ```
    """
    try:
        keywords = nlp_processor.extract_keywords(request.text, request.num_keywords)

        keyword_results = [Keyword(text=word, score=score) for word, score in keywords]

        return KeywordExtractionResponse(keywords=keyword_results)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Keyword extraction failed: {str(e)}"
        )


@router.post("/analyze", response_model=ComprehensiveAnalysisResponse)
async def comprehensive_analysis(
    request: ComprehensiveAnalysisRequest,
) -> ComprehensiveAnalysisResponse:
    """
    Perform comprehensive NLP analysis on text.

    Combines sentiment, intent, entity extraction, and keyword extraction.

    Example:
    ```json
    {
        "text": "I love the product and want to order more for my team!",
        "include_sentiment": true,
        "include_intent": true,
        "include_entities": true,
        "include_keywords": true
    }
    ```
    """
    try:
        response_data = {"status": "success"}

        # Sentiment analysis
        if request.include_sentiment:
            sentiment = nlp_processor.analyze_sentiment(request.text)
            response_data["sentiment"] = SentimentAnalysisResponse(
                label=sentiment.label, score=sentiment.score
            )

        # Intent classification
        if request.include_intent:
            intent = nlp_processor.classify_intent(request.text)
            response_data["intent"] = IntentClassificationResponse(
                intent=intent.intent,
                confidence=intent.confidence,
                sub_intents=intent.sub_intents or [],
            )

        # Entity extraction
        if request.include_entities:
            entities = nlp_processor.extract_entities(request.text)
            entity_results = [
                EntityResult_API(
                    entity=e.entity,
                    label=e.label,
                    position={"start": e.start, "end": e.end},
                    confidence=e.score,
                )
                for e in entities
            ]
            response_data["entities"] = EntityExtractionResponse(
                entities=entity_results, entity_count=len(entity_results)
            )

        # Keyword extraction
        if request.include_keywords:
            keywords = nlp_processor.extract_keywords(request.text)
            keyword_results = [
                Keyword(text=word, score=score) for word, score in keywords
            ]
            response_data["keywords"] = KeywordExtractionResponse(
                keywords=keyword_results
            )

        return ComprehensiveAnalysisResponse(**response_data)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Comprehensive analysis failed: {str(e)}"
        )


@router.get("/health")
async def nlp_health():
    """Check NLP service health"""
    return {
        "status": "healthy",
        "service": "NLP",
        "features": {
            "sentiment_analysis": True,
            "intent_classification": True,
            "entity_extraction": True,
            "text_summarization": True,
            "keyword_extraction": True,
        },
    }
