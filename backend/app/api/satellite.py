"""
SmartCrop Pakistan - Satellite Imagery API Endpoints
Sentinel-2 integration for crop monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from enum import Enum

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import Farm

router = APIRouter()


class ImagerySource(str, Enum):
    """Available satellite imagery sources."""
    SENTINEL_2 = "sentinel-2"
    LANDSAT_8 = "landsat-8"
    DRONE = "drone"


class SatelliteImageRequest(BaseModel):
    """Request for satellite imagery."""
    farm_id: int
    source: ImagerySource = ImagerySource.SENTINEL_2
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_cloud_cover: float = 20.0


class SatelliteImageResponse(BaseModel):
    """Satellite image metadata."""
    image_id: str
    farm_id: int
    source: str
    acquisition_date: datetime
    cloud_cover_percent: float
    
    # URLs for different band combinations
    true_color_url: str
    ndvi_url: str
    ndwi_url: str
    false_color_url: str
    
    # Metadata
    resolution_meters: float
    tile_id: str
    processing_status: str


class NDVITimeseriesPoint(BaseModel):
    """Single NDVI measurement."""
    date: datetime
    ndvi_mean: float
    ndvi_min: float
    ndvi_max: float
    cloud_cover: float


class NDVITimeseriesResponse(BaseModel):
    """NDVI time series for a farm."""
    farm_id: int
    farm_name: str
    period_start: datetime
    period_end: datetime
    measurements: List[NDVITimeseriesPoint]
    trend: str  # increasing, decreasing, stable
    anomalies: List[dict]


class VegetationIndicesResponse(BaseModel):
    """All vegetation indices for a farm."""
    farm_id: int
    calculation_date: datetime
    
    # Indices
    ndvi: float  # Normalized Difference Vegetation Index
    ndvi_interpretation: str
    
    ndwi: float  # Normalized Difference Water Index
    ndwi_interpretation: str
    
    savi: float  # Soil-Adjusted Vegetation Index
    savi_interpretation: str
    
    evi: float  # Enhanced Vegetation Index
    evi_interpretation: str
    
    # Zonal statistics
    healthy_zone_percent: float
    moderate_zone_percent: float
    stressed_zone_percent: float
    
    # Comparison
    change_from_last_week: float
    seasonal_average: float


@router.post("/fetch", response_model=SatelliteImageResponse)
async def fetch_satellite_imagery(
    request: SatelliteImageRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch latest satellite imagery for a farm.
    
    کھیت کی سیٹلائٹ تصاویر حاصل کریں
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
    
    # Default date range: last 10 days
    end_date = request.end_date or datetime.utcnow()
    start_date = request.start_date or (end_date - timedelta(days=10))
    
    # TODO: Call Sentinel Hub API
    # For now, return mock response
    
    return SatelliteImageResponse(
        image_id=f"S2A_MSIL2A_{farm.id}_{datetime.utcnow().strftime('%Y%m%d')}",
        farm_id=farm.id,
        source=request.source.value,
        acquisition_date=datetime.utcnow() - timedelta(days=2),
        cloud_cover_percent=8.5,
        true_color_url=f"/api/v1/satellite/render/{farm.id}/true-color",
        ndvi_url=f"/api/v1/satellite/render/{farm.id}/ndvi",
        ndwi_url=f"/api/v1/satellite/render/{farm.id}/ndwi",
        false_color_url=f"/api/v1/satellite/render/{farm.id}/false-color",
        resolution_meters=10.0,
        tile_id="43RGM",  # Pakistan grid
        processing_status="completed"
    )


@router.get("/ndvi-timeseries/{farm_id}", response_model=NDVITimeseriesResponse)
async def get_ndvi_timeseries(
    farm_id: int,
    days: int = 90,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get NDVI time series for trend analysis.
    
    NDVI ٹائم سیریز حاصل کریں
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
    
    # Generate mock time series data
    # In production, this would come from stored satellite analysis
    measurements = []
    base_date = datetime.utcnow() - timedelta(days=days)
    
    for i in range(0, days, 5):  # Every 5 days (Sentinel-2 revisit)
        date = base_date + timedelta(days=i)
        # Simulate seasonal NDVI pattern
        seasonal_factor = 0.1 * (1 + 0.3 * (i / days))
        measurements.append(NDVITimeseriesPoint(
            date=date,
            ndvi_mean=0.55 + seasonal_factor + (0.05 * (i % 3 - 1)),
            ndvi_min=0.35 + seasonal_factor,
            ndvi_max=0.75 + seasonal_factor,
            cloud_cover=5 + (i % 20)
        ))
    
    # Determine trend
    if len(measurements) >= 2:
        first_half_avg = sum(m.ndvi_mean for m in measurements[:len(measurements)//2]) / (len(measurements)//2)
        second_half_avg = sum(m.ndvi_mean for m in measurements[len(measurements)//2:]) / (len(measurements)//2)
        
        if second_half_avg > first_half_avg * 1.05:
            trend = "increasing / بڑھ رہا ہے"
        elif second_half_avg < first_half_avg * 0.95:
            trend = "decreasing / کم ہو رہا ہے"
        else:
            trend = "stable / مستحکم"
    else:
        trend = "insufficient data"
    
    return NDVITimeseriesResponse(
        farm_id=farm_id,
        farm_name=farm.name,
        period_start=base_date,
        period_end=datetime.utcnow(),
        measurements=measurements,
        trend=trend,
        anomalies=[
            {
                "date": (datetime.utcnow() - timedelta(days=15)).isoformat(),
                "type": "sudden_drop",
                "severity": "medium",
                "message_en": "15% NDVI drop detected - possible water stress",
                "message_ur": "NDVI میں 15% کمی - ممکنہ پانی کا دباؤ"
            }
        ]
    )


@router.get("/indices/{farm_id}", response_model=VegetationIndicesResponse)
async def get_vegetation_indices(
    farm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all vegetation indices for a farm.
    
    تمام پودوں کے اشاریے حاصل کریں
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
    
    # Use farm's latest values or defaults
    ndvi = farm.ndvi_latest or 0.65
    ndwi = farm.ndwi_latest or 0.35
    
    # Calculate other indices (simplified)
    savi = ndvi * 1.5 / (ndvi + 0.5 + 1)  # Simplified SAVI
    evi = 2.5 * (ndvi - 0.1) / (ndvi + 6 * 0.1 - 7.5 * 0.05 + 1)  # Simplified EVI
    
    # Interpretations
    def interpret_ndvi(val):
        if val >= 0.6: return "Healthy dense vegetation / گھنے صحت مند پودے"
        elif val >= 0.4: return "Moderate vegetation / معتدل پودے"
        elif val >= 0.2: return "Sparse vegetation / کم پودے"
        else: return "Bare soil or water / خالی زمین یا پانی"
    
    def interpret_ndwi(val):
        if val >= 0.3: return "High water content / زیادہ پانی"
        elif val >= 0.1: return "Adequate water / کافی پانی"
        elif val >= 0: return "Low water content / کم پانی"
        else: return "Water stressed / پانی کی کمی"
    
    return VegetationIndicesResponse(
        farm_id=farm_id,
        calculation_date=datetime.utcnow(),
        ndvi=round(ndvi, 3),
        ndvi_interpretation=interpret_ndvi(ndvi),
        ndwi=round(ndwi, 3),
        ndwi_interpretation=interpret_ndwi(ndwi),
        savi=round(savi, 3),
        savi_interpretation="Good soil-adjusted index" if savi > 0.4 else "Low vegetation density",
        evi=round(evi, 3),
        evi_interpretation="Enhanced index within normal range",
        healthy_zone_percent=65.0,
        moderate_zone_percent=25.0,
        stressed_zone_percent=10.0,
        change_from_last_week=0.03,
        seasonal_average=0.58
    )


@router.get("/available-dates/{farm_id}")
async def get_available_imagery_dates(
    farm_id: int,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get dates when satellite imagery is available.
    
    دستیاب سیٹلائٹ تصاویر کی تاریخیں
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
    
    # Sentinel-2 has 5-day revisit time
    available_dates = []
    for i in range(0, days, 5):
        date = datetime.utcnow() - timedelta(days=i)
        available_dates.append({
            "date": date.date().isoformat(),
            "source": "sentinel-2",
            "cloud_cover_percent": 5 + (i % 30),  # Simulated
            "quality": "good" if (5 + i % 30) < 20 else "moderate"
        })
    
    return {
        "farm_id": farm_id,
        "available_dates": available_dates,
        "total_count": len(available_dates),
        "next_expected": (datetime.utcnow() + timedelta(days=5 - datetime.utcnow().day % 5)).date().isoformat()
    }
