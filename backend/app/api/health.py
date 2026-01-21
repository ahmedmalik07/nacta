"""
SmartCrop Pakistan - Crop Health API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import io

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import Farm, CropHealthRecord, CropHealthStatus

router = APIRouter()


class HealthRecordResponse(BaseModel):
    """Crop health record response."""
    id: int
    farm_id: int
    analysis_date: datetime
    ndvi: float
    ndwi: float
    savi: Optional[float]
    health_status: CropHealthStatus
    health_score: float
    confidence: float
    affected_area_percent: Optional[float]
    source: str
    recommendations: Optional[dict]
    
    class Config:
        from_attributes = True


class HealthAnalysisRequest(BaseModel):
    """Request to trigger health analysis."""
    farm_id: int
    source: str = "sentinel-2"  # sentinel-2 or drone


class HealthAnalysisResponse(BaseModel):
    """Health analysis result."""
    farm_id: int
    farm_name: str
    analysis_date: datetime
    
    # Indices
    ndvi: float
    ndvi_interpretation: str
    ndwi: float
    ndwi_interpretation: str
    savi: float
    
    # Classification
    health_status: str
    health_status_urdu: str
    health_score: float
    confidence: float
    
    # Zones
    healthy_area_percent: float
    stressed_area_percent: float
    critical_area_percent: float
    
    # Recommendations
    recommendations: List[dict]
    
    # Visualization
    health_map_url: Optional[str]
    ndvi_map_url: Optional[str]


class DiseaseDetectionResponse(BaseModel):
    """Disease detection from uploaded image."""
    detected: bool
    disease_name_en: Optional[str]
    disease_name_ur: Optional[str]
    confidence: float
    affected_area_percent: Optional[float]
    severity: str  # mild, moderate, severe
    treatment_recommendations: List[dict]
    preventive_measures: List[str]


@router.get("/history/{farm_id}", response_model=List[HealthRecordResponse])
async def get_health_history(
    farm_id: int,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get health analysis history for a farm.
    
    کھیت کی صحت کی تاریخ حاصل کریں
    """
    # Verify farm ownership
    farm_result = await db.execute(
        select(Farm).where(
            Farm.id == farm_id,
            Farm.farmer_id == int(current_user["user_id"])
        )
    )
    farm = farm_result.scalar_one_or_none()
    
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    # Get health records
    since_date = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(CropHealthRecord)
        .where(
            CropHealthRecord.farm_id == farm_id,
            CropHealthRecord.analysis_date >= since_date
        )
        .order_by(desc(CropHealthRecord.analysis_date))
    )
    records = result.scalars().all()
    
    return records


@router.post("/analyze", response_model=HealthAnalysisResponse)
async def analyze_crop_health(
    request: HealthAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger crop health analysis for a farm using satellite/drone imagery.
    
    سیٹلائٹ/ڈرون تصاویر سے فصل کی صحت کا تجزیہ کریں
    """
    # Verify farm ownership
    farm_result = await db.execute(
        select(Farm).where(
            Farm.id == request.farm_id,
            Farm.farmer_id == int(current_user["user_id"])
        )
    )
    farm = farm_result.scalar_one_or_none()
    
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    # TODO: Call ML service for actual analysis
    # For now, return mock data demonstrating the API structure
    
    # Simulated analysis results
    ndvi = 0.72
    ndwi = 0.45
    savi = 0.68
    health_score = 78.5
    
    # NDVI interpretation
    if ndvi >= 0.6:
        ndvi_interp = "Healthy vegetation / صحت مند پودے"
    elif ndvi >= 0.3:
        ndvi_interp = "Moderate stress / معتدل دباؤ"
    else:
        ndvi_interp = "Severe stress / شدید دباؤ"
    
    # NDWI interpretation  
    if ndwi >= 0.3:
        ndwi_interp = "Adequate water / مناسب پانی"
    elif ndwi >= 0.1:
        ndwi_interp = "Slight water stress / ہلکا پانی کا دباؤ"
    else:
        ndwi_interp = "Water deficient / پانی کی کمی"
    
    # Health status
    if health_score >= 80:
        health_status = "Healthy"
        health_status_ur = "صحت مند"
    elif health_score >= 60:
        health_status = "Moderate Stress"
        health_status_ur = "معتدل دباؤ"
    elif health_score >= 40:
        health_status = "High Stress"
        health_status_ur = "زیادہ دباؤ"
    else:
        health_status = "Critical"
        health_status_ur = "نازک حالت"
    
    # Generate recommendations
    recommendations = []
    if ndwi < 0.3:
        recommendations.append({
            "type": "irrigation",
            "priority": "high",
            "message_en": "Increase irrigation frequency. Recommended: 2 additional waterings this week.",
            "message_ur": "آبپاشی کی تعداد بڑھائیں۔ سفارش: اس ہفتے 2 اضافی آبپاشی۔"
        })
    
    if ndvi < 0.5:
        recommendations.append({
            "type": "fertilizer",
            "priority": "medium",
            "message_en": "Consider nitrogen fertilizer application. Consult local agronomist.",
            "message_ur": "نائٹروجن کھاد کے استعمال پر غور کریں۔ مقامی ماہر زراعت سے مشورہ کریں۔"
        })
    
    # Save health record
    health_record = CropHealthRecord(
        farm_id=farm.id,
        analysis_date=datetime.utcnow(),
        ndvi=ndvi,
        ndwi=ndwi,
        savi=savi,
        health_status=CropHealthStatus.HEALTHY if health_score >= 70 else CropHealthStatus.WATER_STRESSED,
        health_score=health_score,
        confidence=0.89,
        source=request.source,
        recommendations={"items": recommendations}
    )
    db.add(health_record)
    
    # Update farm's latest metrics
    farm.health_score = health_score
    farm.ndvi_latest = ndvi
    farm.ndwi_latest = ndwi
    farm.last_satellite_analysis = datetime.utcnow()
    
    await db.commit()
    
    return HealthAnalysisResponse(
        farm_id=farm.id,
        farm_name=farm.name,
        analysis_date=datetime.utcnow(),
        ndvi=ndvi,
        ndvi_interpretation=ndvi_interp,
        ndwi=ndwi,
        ndwi_interpretation=ndwi_interp,
        savi=savi,
        health_status=health_status,
        health_status_urdu=health_status_ur,
        health_score=health_score,
        confidence=0.89,
        healthy_area_percent=75.0,
        stressed_area_percent=20.0,
        critical_area_percent=5.0,
        recommendations=recommendations,
        health_map_url=None,
        ndvi_map_url=None
    )


@router.post("/detect-disease", response_model=DiseaseDetectionResponse)
async def detect_disease(
    farm_id: int,
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Detect crop disease from uploaded photo.
    
    تصویر سے فصل کی بیماری کا پتہ لگائیں
    """
    # Verify farm ownership
    farm_result = await db.execute(
        select(Farm).where(
            Farm.id == farm_id,
            Farm.farmer_id == int(current_user["user_id"])
        )
    )
    farm = farm_result.scalar_one_or_none()
    
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    # Read image
    image_bytes = await image.read()
    
    # TODO: Call EfficientNet model for disease classification
    # For now, return demo response
    
    return DiseaseDetectionResponse(
        detected=True,
        disease_name_en="Wheat Leaf Rust (Puccinia triticina)",
        disease_name_ur="گندم کی پتی کی سرخی (زنگ)",
        confidence=0.87,
        affected_area_percent=15.0,
        severity="moderate",
        treatment_recommendations=[
            {
                "type": "fungicide",
                "product": "Propiconazole",
                "dosage": "1 liter per acre",
                "message_en": "Apply fungicide within 3 days. Spray in early morning.",
                "message_ur": "3 دن کے اندر فنگیسائڈ لگائیں۔ صبح سویرے چھڑکاؤ کریں۔"
            }
        ],
        preventive_measures=[
            "Use resistant wheat varieties / مزاحم گندم کی اقسام استعمال کریں",
            "Remove crop residue after harvest / فصل کاٹنے کے بعد بقایا ہٹائیں",
            "Avoid excessive nitrogen fertilization / زیادہ نائٹروجن کھاد سے پرہیز کریں"
        ]
    )
