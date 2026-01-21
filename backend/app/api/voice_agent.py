"""
SmartCrop Pakistan - Voice AI Agent API Endpoints
Urdu/Punjabi/Sindhi conversational AI for farmers
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import io

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import Farm, ConversationLog, CropHealthRecord

router = APIRouter()


class TextQueryRequest(BaseModel):
    """Text query to AI agent."""
    message: str
    language: str = "ur"  # ur, pa, sd (Urdu, Punjabi, Sindhi)
    farm_id: Optional[int] = None


class AgentResponse(BaseModel):
    """AI agent response."""
    response_text: str
    response_audio_url: Optional[str]
    language: str
    confidence: float
    
    # Context used
    farm_context_used: bool
    sources: List[str]
    
    # Follow-up
    suggested_questions: List[str]
    
    # Actions suggested
    recommended_actions: List[dict]


class ConversationHistoryItem(BaseModel):
    """Single conversation item."""
    id: int
    timestamp: datetime
    input_text: str
    response_text: str
    input_type: str
    language: str


# Knowledge base responses (simplified - would use RAG in production)
AGRICULTURAL_KNOWLEDGE = {
    "water": {
        "ur": "آپ کے کھیت کو موجودہ NDVI کی بنیاد پر ہفتے میں 2-3 بار آبپاشی کی ضرورت ہے۔",
        "en": "Based on current NDVI, your field needs irrigation 2-3 times per week."
    },
    "pest": {
        "ur": "کیڑوں سے بچاؤ کے لیے نیم کا تیل یا مناسب کیڑے مار دوا استعمال کریں۔",
        "en": "Use neem oil or appropriate pesticide for pest prevention."
    },
    "fertilizer": {
        "ur": "گندم کے لیے DAP کھاد بوائی کے وقت اور یوریا دو حصوں میں لگائیں۔",
        "en": "For wheat, apply DAP at sowing and urea in two splits."
    },
    "disease": {
        "ur": "پیلے پتوں کا سبب نائٹروجن کی کمی یا پانی کا دباؤ ہو سکتا ہے۔",
        "en": "Yellow leaves may indicate nitrogen deficiency or water stress."
    },
    "harvest": {
        "ur": "جب دانے سخت ہو جائیں اور نمی 14% سے کم ہو تو فصل کاٹیں۔",
        "en": "Harvest when grains are hard and moisture is below 14%."
    }
}

# Common farmer questions patterns
QUESTION_PATTERNS = {
    "پانی": "water",
    "آبپاشی": "water",
    "کیڑے": "pest",
    "کیڑوں": "pest",
    "کھاد": "fertilizer",
    "یوریا": "fertilizer",
    "DAP": "fertilizer",
    "بیماری": "disease",
    "پیلے پتے": "disease",
    "زرد": "disease",
    "کاٹنا": "harvest",
    "فصل کاٹ": "harvest"
}


def detect_topic(message: str) -> str:
    """Detect topic from farmer's question."""
    message_lower = message.lower()
    
    for pattern, topic in QUESTION_PATTERNS.items():
        if pattern in message or pattern.lower() in message_lower:
            return topic
    
    return "general"


def get_farm_context(farm: Farm) -> str:
    """Generate context string from farm data."""
    context = f"""
    کھیت کا نام: {farm.name}
    رقبہ: {farm.area_acres} ایکڑ
    فصل: {farm.current_crop.value if farm.current_crop else 'نامعلوم'}
    صحت سکور: {farm.health_score or 'تجزیہ نہیں ہوا'}%
    NDVI: {farm.ndvi_latest or 'نامعلوم'}
    آبپاشی کا طریقہ: {farm.irrigation_type}
    """
    return context


@router.post("/query", response_model=AgentResponse)
async def query_agent(
    request: TextQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Send text query to AI agent.
    
    AI ایجنٹ سے سوال پوچھیں
    """
    farm = None
    farm_context = ""
    
    # Get farm context if provided
    if request.farm_id:
        farm_result = await db.execute(
            select(Farm).where(
                Farm.id == request.farm_id,
                Farm.farmer_id == int(current_user["user_id"])
            )
        )
        farm = farm_result.scalar_one_or_none()
        if farm:
            farm_context = get_farm_context(farm)
    
    # Detect topic and generate response
    topic = detect_topic(request.message)
    
    if topic in AGRICULTURAL_KNOWLEDGE:
        base_response = AGRICULTURAL_KNOWLEDGE[topic]["ur"]
    else:
        base_response = "آپ کا سوال موصول ہوا۔ براہ کرم مزید تفصیل دیں یا اپنے علاقے کے زرعی ماہر سے رابطہ کریں۔"
    
    # Add farm-specific context
    if farm and farm.health_score:
        if farm.health_score < 60:
            base_response += f"\n\n⚠️ آپ کے کھیت کی صحت {farm.health_score}% ہے جو کم ہے۔ فوری توجہ دیں۔"
        elif farm.health_score >= 80:
            base_response += f"\n\n✅ آپ کا کھیت اچھی حالت میں ہے (صحت: {farm.health_score}%)۔"
    
    # Log conversation
    log = ConversationLog(
        farmer_id=int(current_user["user_id"]),
        farm_id=request.farm_id,
        input_text=request.message,
        input_language=request.language,
        input_type="text",
        response_text=base_response,
        context_used={"topic": topic, "farm_context": bool(farm)}
    )
    db.add(log)
    await db.commit()
    
    return AgentResponse(
        response_text=base_response,
        response_audio_url=None,  # Would be TTS URL
        language=request.language,
        confidence=0.85,
        farm_context_used=bool(farm),
        sources=["Pakistan Agriculture Research Council", "Punjab Agriculture Department"],
        suggested_questions=[
            "میری فصل کو کتنا پانی چاہیے؟",
            "کون سی کھاد استعمال کروں؟",
            "کیڑوں سے بچاؤ کیسے کروں؟"
        ],
        recommended_actions=[
            {
                "action": "check_health",
                "label_ur": "کھیت کی صحت چیک کریں",
                "label_en": "Check farm health",
                "priority": "medium"
            }
        ] if farm else []
    )


@router.post("/voice-query", response_model=AgentResponse)
async def voice_query(
    audio: UploadFile = File(...),
    farm_id: Optional[int] = None,
    language: str = "ur",
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Send voice query to AI agent (Urdu/Punjabi/Sindhi).
    
    آواز سے سوال پوچھیں
    """
    # Read audio file
    audio_bytes = await audio.read()
    
    # TODO: Process with Whisper
    # For now, simulate transcription
    
    # Simulated transcription
    transcribed_text = "میری گندم کی فصل کو کتنا پانی چاہیے؟"
    
    # Get farm context
    farm = None
    if farm_id:
        farm_result = await db.execute(
            select(Farm).where(
                Farm.id == farm_id,
                Farm.farmer_id == int(current_user["user_id"])
            )
        )
        farm = farm_result.scalar_one_or_none()
    
    # Generate response
    topic = detect_topic(transcribed_text)
    response_text = AGRICULTURAL_KNOWLEDGE.get(topic, {}).get("ur", 
        "آپ کا سوال موصول ہوا۔ براہ کرم دوبارہ کوشش کریں۔"
    )
    
    # Add farm-specific advice
    if farm and farm.ndwi_latest:
        if farm.ndwi_latest < 0.2:
            response_text = f"آپ کے کھیت میں پانی کی کمی ہے (NDWI: {farm.ndwi_latest:.2f})۔ فوری آبپاشی کریں۔ " + response_text
        else:
            response_text = f"آپ کے کھیت میں پانی کی مقدار مناسب ہے (NDWI: {farm.ndwi_latest:.2f})۔ " + response_text
    
    # Log conversation
    log = ConversationLog(
        farmer_id=int(current_user["user_id"]),
        farm_id=farm_id,
        input_text=transcribed_text,
        input_language=language,
        input_type="voice",
        response_text=response_text,
        context_used={"topic": topic, "transcribed": True}
    )
    db.add(log)
    await db.commit()
    
    return AgentResponse(
        response_text=response_text,
        response_audio_url="/api/v1/agent/tts/response_123.mp3",  # Would be generated
        language=language,
        confidence=0.82,
        farm_context_used=bool(farm),
        sources=["Pakistan Agriculture Research Council"],
        suggested_questions=[
            "کھاد کب لگائیں؟",
            "فصل کی بیماری کیسے پہچانیں؟",
            "موسم کی پیش گوئی بتائیں"
        ],
        recommended_actions=[
            {
                "action": "schedule_irrigation",
                "label_ur": "آبپاشی کا شیڈول بنائیں",
                "label_en": "Schedule irrigation",
                "priority": "high"
            }
        ]
    )


@router.get("/conversation-history", response_model=List[ConversationHistoryItem])
async def get_conversation_history(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get conversation history with AI agent.
    
    گفتگو کی تاریخ حاصل کریں
    """
    result = await db.execute(
        select(ConversationLog)
        .where(ConversationLog.farmer_id == int(current_user["user_id"]))
        .order_by(ConversationLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    
    return [
        ConversationHistoryItem(
            id=log.id,
            timestamp=log.created_at,
            input_text=log.input_text,
            response_text=log.response_text,
            input_type=log.input_type,
            language=log.input_language
        )
        for log in logs
    ]


@router.post("/feedback/{conversation_id}")
async def submit_feedback(
    conversation_id: int,
    rating: int,
    feedback_text: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Submit feedback on AI response.
    
    AI جواب پر رائے دیں
    """
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")
    
    result = await db.execute(
        select(ConversationLog).where(
            ConversationLog.id == conversation_id,
            ConversationLog.farmer_id == int(current_user["user_id"])
        )
    )
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    log.feedback_rating = rating
    log.feedback_text = feedback_text
    
    await db.commit()
    
    return {
        "message": "شکریہ! آپ کی رائے سے ہم بہتر ہوں گے۔ / Thank you for your feedback!",
        "conversation_id": conversation_id,
        "rating": rating
    }


@router.get("/suggested-questions")
async def get_suggested_questions(
    language: str = "ur",
    category: Optional[str] = None
):
    """
    Get suggested questions for farmers.
    
    تجویز کردہ سوالات
    """
    suggestions = {
        "irrigation": [
            {"ur": "میری فصل کو کتنا پانی چاہیے؟", "en": "How much water does my crop need?"},
            {"ur": "آبپاشی کا بہترین وقت کیا ہے؟", "en": "What is the best time for irrigation?"},
            {"ur": "ٹیوب ویل کتنی دیر چلائیں؟", "en": "How long should I run the tubewell?"}
        ],
        "fertilizer": [
            {"ur": "گندم میں کون سی کھاد لگائیں؟", "en": "Which fertilizer for wheat?"},
            {"ur": "یوریا کب اور کتنی لگائیں؟", "en": "When and how much urea?"},
            {"ur": "DAP کی مقدار کیا ہونی چاہیے؟", "en": "What should be the DAP quantity?"}
        ],
        "pest": [
            {"ur": "کیڑوں سے بچاؤ کیسے کریں؟", "en": "How to prevent pests?"},
            {"ur": "کون سی دوا چھڑکاؤ کریں؟", "en": "Which pesticide to spray?"},
            {"ur": "جڑی بوٹیوں کا تدارک کیسے کریں؟", "en": "How to control weeds?"}
        ],
        "disease": [
            {"ur": "پیلے پتوں کا علاج کیا ہے؟", "en": "Treatment for yellow leaves?"},
            {"ur": "گندم میں سرخی کا علاج؟", "en": "Treatment for wheat rust?"},
            {"ur": "فصل کی بیماری کیسے پہچانیں؟", "en": "How to identify crop disease?"}
        ]
    }
    
    if category and category in suggestions:
        return {"category": category, "questions": suggestions[category]}
    
    # Return all
    all_questions = []
    for cat, questions in suggestions.items():
        all_questions.extend([{**q, "category": cat} for q in questions])
    
    return {"questions": all_questions}
