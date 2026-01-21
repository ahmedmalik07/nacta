"""
SmartCrop Pakistan - Farms API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import Farm, Farmer, Province, CropType

router = APIRouter()


# Pydantic Schemas
class FarmBoundaryPoint(BaseModel):
    """GPS coordinate point."""
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class FarmCreate(BaseModel):
    """Schema for creating a new farm."""
    name: str = Field(..., min_length=1, max_length=100)
    area_acres: float = Field(..., gt=0)
    boundary_points: List[FarmBoundaryPoint] = Field(..., min_length=3)
    current_crop: Optional[CropType] = None
    planting_date: Optional[datetime] = None
    irrigation_type: str = Field(default="canal")
    soil_type: Optional[str] = None


class FarmResponse(BaseModel):
    """Schema for farm response."""
    id: int
    name: str
    area_acres: float
    center_lat: float
    center_lon: float
    current_crop: Optional[CropType]
    planting_date: Optional[datetime]
    irrigation_type: str
    health_score: Optional[float]
    ndvi_latest: Optional[float]
    last_satellite_analysis: Optional[datetime]
    
    class Config:
        from_attributes = True


class FarmListResponse(BaseModel):
    """Schema for list of farms."""
    farms: List[FarmResponse]
    total: int


class FarmHealthSummary(BaseModel):
    """Quick health summary for a farm."""
    farm_id: int
    farm_name: str
    health_score: float
    health_status: str
    ndvi: float
    ndwi: float
    last_updated: datetime
    alerts_count: int


@router.post("/", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
async def create_farm(
    farm_data: FarmCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Register a new farm with GPS boundary.
    
    نیا کھیت رجسٹر کریں - GPS باؤنڈری کے ساتھ
    """
    # Calculate center point from boundary
    lats = [p.lat for p in farm_data.boundary_points]
    lons = [p.lon for p in farm_data.boundary_points]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)
    
    # Create polygon WKT from boundary points
    points_wkt = ", ".join([f"{p.lon} {p.lat}" for p in farm_data.boundary_points])
    # Close the polygon
    first_point = farm_data.boundary_points[0]
    points_wkt += f", {first_point.lon} {first_point.lat}"
    polygon_wkt = f"POLYGON(({points_wkt}))"
    
    # Create farm record
    farm = Farm(
        farmer_id=int(current_user["user_id"]),
        name=farm_data.name,
        area_acres=farm_data.area_acres,
        boundary=polygon_wkt,
        center_lat=center_lat,
        center_lon=center_lon,
        current_crop=farm_data.current_crop,
        planting_date=farm_data.planting_date,
        irrigation_type=farm_data.irrigation_type,
        soil_type=farm_data.soil_type
    )
    
    db.add(farm)
    await db.commit()
    await db.refresh(farm)
    
    return farm


@router.get("/", response_model=FarmListResponse)
async def get_farms(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all farms for the current farmer.
    
    کسان کے تمام کھیتوں کی فہرست
    """
    result = await db.execute(
        select(Farm).where(Farm.farmer_id == int(current_user["user_id"]))
    )
    farms = result.scalars().all()
    
    return FarmListResponse(
        farms=[FarmResponse.model_validate(f) for f in farms],
        total=len(farms)
    )


@router.get("/{farm_id}", response_model=FarmResponse)
async def get_farm(
    farm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get details of a specific farm.
    
    کھیت کی تفصیلات حاصل کریں
    """
    result = await db.execute(
        select(Farm).where(
            Farm.id == farm_id,
            Farm.farmer_id == int(current_user["user_id"])
        )
    )
    farm = result.scalar_one_or_none()
    
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found / کھیت نہیں ملا"
        )
    
    return farm


@router.get("/{farm_id}/health-summary", response_model=FarmHealthSummary)
async def get_farm_health_summary(
    farm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get quick health summary for a farm.
    
    کھیت کی صحت کا خلاصہ
    """
    result = await db.execute(
        select(Farm).where(
            Farm.id == farm_id,
            Farm.farmer_id == int(current_user["user_id"])
        )
    )
    farm = result.scalar_one_or_none()
    
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found"
        )
    
    # Determine health status from score
    health_status = "Unknown"
    if farm.health_score:
        if farm.health_score >= 80:
            health_status = "Healthy / صحت مند"
        elif farm.health_score >= 60:
            health_status = "Moderate / معتدل"
        elif farm.health_score >= 40:
            health_status = "Stressed / دباؤ میں"
        else:
            health_status = "Critical / نازک"
    
    return FarmHealthSummary(
        farm_id=farm.id,
        farm_name=farm.name,
        health_score=farm.health_score or 0,
        health_status=health_status,
        ndvi=farm.ndvi_latest or 0,
        ndwi=farm.ndwi_latest or 0,
        last_updated=farm.last_satellite_analysis or farm.updated_at,
        alerts_count=0  # TODO: Count active alerts
    )


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_farm(
    farm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a farm.
    
    کھیت حذف کریں
    """
    result = await db.execute(
        select(Farm).where(
            Farm.id == farm_id,
            Farm.farmer_id == int(current_user["user_id"])
        )
    )
    farm = result.scalar_one_or_none()
    
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found"
        )
    
    await db.delete(farm)
    await db.commit()
