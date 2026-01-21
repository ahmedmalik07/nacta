"""
SmartCrop Pakistan - Demo API (Simplified for local testing)
No database or ML models required - uses mock data
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import random

app = FastAPI(
    title="SmartCrop Pakistan API (Demo)",
    description="🌾 AI-Powered Precision Agriculture - Demo Mode",
    version="1.0.0-demo"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Mock Data ============

MOCK_FARMS = [
    {
        "id": 1,
        "name": "میرا گندم کا کھیت",
        "name_en": "My Wheat Farm",
        "area_acres": 5.0,
        "crop": "wheat",
        "province": "Punjab",
        "district": "Lahore",
        "health_score": 78.5,
        "ndvi": 0.65,
        "status": "healthy"
    },
    {
        "id": 2,
        "name": "چاول کا کھیت",
        "name_en": "Rice Field",
        "area_acres": 3.2,
        "crop": "rice",
        "province": "Sindh",
        "district": "Sukkur",
        "health_score": 62.0,
        "ndvi": 0.48,
        "status": "moderate_stress"
    }
]

# ============ Models ============

class Farm(BaseModel):
    id: int
    name: str
    name_en: str
    area_acres: float
    crop: str
    province: str
    district: str
    health_score: float
    ndvi: float
    status: str

class HealthAnalysis(BaseModel):
    farm_id: int
    farm_name: str
    analysis_date: str
    ndvi: float
    ndwi: float
    health_status: str
    health_status_urdu: str
    health_score: float
    healthy_percent: float
    stressed_percent: float
    recommendations: List[dict]

class YieldPrediction(BaseModel):
    farm_id: int
    crop: str
    crop_urdu: str
    predicted_yield_tons_per_hectare: float
    total_yield_tons: float
    confidence_percent: float
    estimated_revenue_pkr: int
    harvest_date: str

class VoiceResponse(BaseModel):
    query: str
    response_urdu: str
    response_english: str
    confidence: float
    suggestions: List[str]

# ============ API Endpoints ============

@app.get("/")
async def root():
    return {
        "message": "🌾 SmartCrop Pakistan API - خوش آمدید",
        "status": "running",
        "mode": "demo",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# --- Farms ---

@app.get("/api/v1/farms", response_model=List[Farm])
async def get_farms():
    """Get all farms / تمام کھیتوں کی فہرست"""
    return MOCK_FARMS

@app.get("/api/v1/farms/{farm_id}", response_model=Farm)
async def get_farm(farm_id: int):
    """Get farm by ID / کھیت کی تفصیلات"""
    for farm in MOCK_FARMS:
        if farm["id"] == farm_id:
            return farm
    raise HTTPException(status_code=404, detail="Farm not found / کھیت نہیں ملا")

# --- Health Analysis ---

@app.get("/api/v1/health/analyze/{farm_id}", response_model=HealthAnalysis)
async def analyze_health(farm_id: int):
    """Analyze crop health / فصل کی صحت کا تجزیہ"""
    farm = next((f for f in MOCK_FARMS if f["id"] == farm_id), None)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    ndvi = farm["ndvi"] + random.uniform(-0.05, 0.05)
    ndwi = random.uniform(0.3, 0.5)
    
    return {
        "farm_id": farm_id,
        "farm_name": farm["name"],
        "analysis_date": datetime.now().isoformat(),
        "ndvi": round(ndvi, 3),
        "ndwi": round(ndwi, 3),
        "health_status": "Healthy" if ndvi > 0.5 else "Moderate Stress",
        "health_status_urdu": "صحت مند" if ndvi > 0.5 else "معتدل دباؤ",
        "health_score": round(farm["health_score"] + random.uniform(-5, 5), 1),
        "healthy_percent": round(random.uniform(60, 80), 1),
        "stressed_percent": round(random.uniform(15, 30), 1),
        "recommendations": [
            {
                "type": "irrigation",
                "message_en": "Maintain current irrigation schedule",
                "message_ur": "موجودہ آبپاشی کا شیڈول جاری رکھیں"
            },
            {
                "type": "fertilizer",
                "message_en": "Apply nitrogen fertilizer in 2 weeks",
                "message_ur": "2 ہفتوں میں نائٹروجن کھاد لگائیں"
            }
        ]
    }

# --- Yield Prediction ---

@app.get("/api/v1/predictions/yield/{farm_id}", response_model=YieldPrediction)
async def predict_yield(farm_id: int):
    """Predict crop yield / پیداوار کی پیش گوئی"""
    farm = next((f for f in MOCK_FARMS if f["id"] == farm_id), None)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    crop_urdu = {"wheat": "گندم", "rice": "چاول", "cotton": "کپاس"}.get(farm["crop"], farm["crop"])
    base_yield = {"wheat": 3.2, "rice": 4.1, "cotton": 2.8}.get(farm["crop"], 3.0)
    predicted = base_yield + random.uniform(-0.3, 0.5)
    total = predicted * farm["area_acres"] * 0.4047  # acres to hectares
    price_per_ton = {"wheat": 112500, "rice": 95000, "cotton": 180000}.get(farm["crop"], 100000)
    
    return {
        "farm_id": farm_id,
        "crop": farm["crop"],
        "crop_urdu": crop_urdu,
        "predicted_yield_tons_per_hectare": round(predicted, 2),
        "total_yield_tons": round(total, 2),
        "confidence_percent": round(random.uniform(82, 92), 1),
        "estimated_revenue_pkr": int(total * price_per_ton),
        "harvest_date": "2026-04-15"
    }

# --- Satellite Data ---

@app.get("/api/v1/satellite/ndvi-timeseries/{farm_id}")
async def get_ndvi_timeseries(farm_id: int, days: int = 30):
    """Get NDVI time series / NDVI کا ٹائم سیریز"""
    farm = next((f for f in MOCK_FARMS if f["id"] == farm_id), None)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    base_ndvi = farm["ndvi"]
    data = []
    for i in range(days // 5):  # Every 5 days (Sentinel-2 revisit)
        data.append({
            "date": f"2026-01-{21 - (i * 5):02d}",
            "ndvi": round(base_ndvi + random.uniform(-0.08, 0.08), 3)
        })
    
    return {
        "farm_id": farm_id,
        "farm_name": farm["name"],
        "period_days": days,
        "measurements": list(reversed(data)),
        "trend": "increasing" if random.random() > 0.5 else "stable"
    }

# --- AI Voice Agent ---

@app.post("/api/v1/agent/query", response_model=VoiceResponse)
async def voice_query(message: str = "میری فصل کو پانی کب دوں؟", language: str = "ur"):
    """AI Agent query / AI ایجنٹ سے سوال"""
    
    responses = {
        "پانی": {
            "ur": "آپ کے کھیت میں پانی کی مقدار مناسب ہے۔ ہفتے میں 2-3 بار آبپاشی کافی ہے۔",
            "en": "Water levels in your farm are adequate. Irrigation 2-3 times per week is sufficient."
        },
        "کھاد": {
            "ur": "گندم کے لیے یوریا کھاد 1.5 بوری فی ایکڑ استعمال کریں۔",
            "en": "For wheat, use 1.5 bags of urea fertilizer per acre."
        },
        "بیماری": {
            "ur": "آپ کی فصل صحت مند ہے۔ پتوں پر زنگ کی علامات نہیں ہیں۔",
            "en": "Your crop is healthy. No signs of rust on leaves."
        }
    }
    
    # Simple keyword matching
    for keyword, resp in responses.items():
        if keyword in message:
            return {
                "query": message,
                "response_urdu": resp["ur"],
                "response_english": resp["en"],
                "confidence": round(random.uniform(0.85, 0.95), 2),
                "suggestions": ["کھاد کب لگائیں؟", "موسم کیسا رہے گا؟", "فصل کب کاٹیں؟"]
            }
    
    # Default response
    return {
        "query": message,
        "response_urdu": "میں آپ کی مدد کے لیے حاضر ہوں۔ براہ کرم اپنا سوال دوبارہ پوچھیں۔",
        "response_english": "I'm here to help. Please ask your question again.",
        "confidence": 0.75,
        "suggestions": ["میری فصل کو پانی کب دوں؟", "کھاد کتنی لگائیں؟", "فصل کی صحت کیسی ہے؟"]
    }

# --- Weather ---

@app.get("/api/v1/weather/{district}")
async def get_weather(district: str):
    """Get weather forecast / موسم کی پیش گوئی"""
    return {
        "district": district,
        "date": date.today().isoformat(),
        "temperature_c": random.randint(15, 25),
        "humidity_percent": random.randint(50, 75),
        "rainfall_mm": random.randint(0, 5),
        "forecast_urdu": "آج موسم صاف رہے گا",
        "forecast_english": "Weather will be clear today",
        "farming_advisory_urdu": "آج آبپاشی کے لیے اچھا دن ہے",
        "farming_advisory_english": "Good day for irrigation"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
