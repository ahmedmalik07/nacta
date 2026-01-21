"""
SmartCrop Pakistan - Database Models
SQLAlchemy models with PostGIS geospatial support
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    ForeignKey, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from geoalchemy2 import Geometry
import enum

from app.core.database import Base


class Province(str, enum.Enum):
    """Pakistani provinces for agricultural zones."""
    PUNJAB = "punjab"
    SINDH = "sindh"
    KPK = "kpk"
    BALOCHISTAN = "balochistan"


class CropType(str, enum.Enum):
    """Major crops in Pakistan."""
    WHEAT = "wheat"          # گندم
    RICE = "rice"            # چاول
    COTTON = "cotton"        # کپاس
    SUGARCANE = "sugarcane"  # گنا
    MAIZE = "maize"          # مکئی


class CropHealthStatus(str, enum.Enum):
    """Crop health classification categories."""
    HEALTHY = "healthy"
    WATER_STRESSED = "water_stressed"
    NUTRIENT_DEFICIENT = "nutrient_deficient"
    PEST_INFECTED = "pest_infected"
    DISEASE_AFFECTED = "disease_affected"


class Farmer(Base):
    """Farmer/User model."""
    __tablename__ = "farmers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    phone: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    cnic: Mapped[Optional[str]] = mapped_column(String(15), unique=True, nullable=True)
    
    # Location
    village: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tehsil: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    district: Mapped[str] = mapped_column(String(100))
    province: Mapped[Province] = mapped_column(SQLEnum(Province))
    
    # Preferences
    language: Mapped[str] = mapped_column(String(10), default="ur")  # ur, pa, sd
    notification_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    farms: Mapped[List["Farm"]] = relationship("Farm", back_populates="farmer")


class Farm(Base):
    """Farm/Field model with geospatial boundaries."""
    __tablename__ = "farms"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farmer_id: Mapped[int] = mapped_column(Integer, ForeignKey("farmers.id"))
    
    name: Mapped[str] = mapped_column(String(100))
    area_acres: Mapped[float] = mapped_column(Float)
    
    # Geospatial - Farm boundary polygon
    boundary = Column(Geometry("POLYGON", srid=4326))
    center_lat: Mapped[float] = mapped_column(Float)
    center_lon: Mapped[float] = mapped_column(Float)
    
    # Current crop
    current_crop: Mapped[Optional[CropType]] = mapped_column(SQLEnum(CropType), nullable=True)
    planting_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expected_harvest: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Irrigation type
    irrigation_type: Mapped[str] = mapped_column(String(50), default="canal")  # canal, tubewell, rainfed
    
    # Soil information
    soil_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    soil_ph: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Health metrics (latest)
    health_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-100
    ndvi_latest: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ndwi_latest: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_satellite_analysis: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="farms")
    health_records: Mapped[List["CropHealthRecord"]] = relationship("CropHealthRecord", back_populates="farm")
    predictions: Mapped[List["YieldPrediction"]] = relationship("YieldPrediction", back_populates="farm")


class CropHealthRecord(Base):
    """Historical crop health analysis records."""
    __tablename__ = "crop_health_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id"))
    
    # Analysis timestamp
    analysis_date: Mapped[datetime] = mapped_column(DateTime)
    
    # Vegetation indices
    ndvi: Mapped[float] = mapped_column(Float)  # Normalized Difference Vegetation Index
    ndwi: Mapped[float] = mapped_column(Float)  # Normalized Difference Water Index
    savi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Soil-Adjusted Vegetation Index
    
    # Health classification
    health_status: Mapped[CropHealthStatus] = mapped_column(SQLEnum(CropHealthStatus))
    health_score: Mapped[float] = mapped_column(Float)  # 0-100
    confidence: Mapped[float] = mapped_column(Float)  # Model confidence 0-1
    
    # Segmentation data
    affected_area_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    segmentation_mask_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Source
    source: Mapped[str] = mapped_column(String(50), default="sentinel-2")  # sentinel-2, drone
    satellite_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Recommendations
    recommendations: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Relationship
    farm: Mapped["Farm"] = relationship("Farm", back_populates="health_records")


class YieldPrediction(Base):
    """Yield prediction records."""
    __tablename__ = "yield_predictions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id"))
    
    crop_type: Mapped[CropType] = mapped_column(SQLEnum(CropType))
    
    # Prediction
    predicted_yield_tons_per_hectare: Mapped[float] = mapped_column(Float)
    predicted_total_yield_tons: Mapped[float] = mapped_column(Float)
    confidence_interval_low: Mapped[float] = mapped_column(Float)
    confidence_interval_high: Mapped[float] = mapped_column(Float)
    
    # Model info
    model_version: Mapped[str] = mapped_column(String(50))
    prediction_date: Mapped[datetime] = mapped_column(DateTime)
    target_harvest_date: Mapped[datetime] = mapped_column(DateTime)
    
    # Features used
    features_used: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Actual yield (filled after harvest for model improvement)
    actual_yield_tons: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_recorded_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationship
    farm: Mapped["Farm"] = relationship("Farm", back_populates="predictions")


class Alert(Base):
    """Alert/notification records."""
    __tablename__ = "alerts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id"))
    
    alert_type: Mapped[str] = mapped_column(String(50))  # pest, disease, water_stress, weather
    severity: Mapped[str] = mapped_column(String(20))  # low, medium, high, critical
    
    title_en: Mapped[str] = mapped_column(String(200))
    title_ur: Mapped[str] = mapped_column(String(200))
    
    message_en: Mapped[str] = mapped_column(Text)
    message_ur: Mapped[str] = mapped_column(Text)
    
    # Action recommendation
    recommended_action_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommended_action_ur: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ConversationLog(Base):
    """AI Agent conversation history for learning."""
    __tablename__ = "conversation_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farmer_id: Mapped[int] = mapped_column(Integer, ForeignKey("farmers.id"))
    farm_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("farms.id"), nullable=True)
    
    # Conversation
    input_text: Mapped[str] = mapped_column(Text)
    input_language: Mapped[str] = mapped_column(String(10))
    input_type: Mapped[str] = mapped_column(String(20))  # voice, text
    
    response_text: Mapped[str] = mapped_column(Text)
    
    # Context used
    context_used: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Feedback
    feedback_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    feedback_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
