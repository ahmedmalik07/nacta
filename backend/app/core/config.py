"""
SmartCrop Pakistan - Configuration Settings
"""

from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Application
    APP_NAME: str = "SmartCrop Pakistan"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8081",
        "https://smartcrop.pk",
        "https://app.smartcrop.pk"
    ]
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/smartcrop"
    DATABASE_ECHO: bool = False
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 3600  # 1 hour
    
    # Satellite API (Sentinel Hub)
    SENTINEL_HUB_CLIENT_ID: str = ""
    SENTINEL_HUB_CLIENT_SECRET: str = ""
    SENTINEL_HUB_INSTANCE_ID: str = ""
    
    # Pakistan Met Department API
    PAKISTAN_MET_API_KEY: str = ""
    PAKISTAN_MET_API_URL: str = "https://api.pmd.gov.pk/v1"
    
    # ML Models
    ML_MODELS_PATH: str = "./ml_models"
    SEGMENTATION_MODEL: str = "unet_crop_segmentation_v1.onnx"
    CLASSIFICATION_MODEL: str = "efficientnet_crop_health_v1.onnx"
    YIELD_MODEL: str = "xgboost_lstm_yield_v1.pkl"
    
    # LLM Configuration (Llama)
    LLM_MODEL_PATH: str = "./ml_models/llama-3.1-8b-urdu-finetuned"
    LLM_MAX_TOKENS: int = 512
    LLM_TEMPERATURE: float = 0.7
    
    # Whisper (Voice Recognition)
    WHISPER_MODEL: str = "large-v3"
    WHISPER_LANGUAGE: str = "ur"  # Urdu default
    
    # Storage (MinIO/S3)
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_SATELLITE: str = "satellite-imagery"
    S3_BUCKET_DRONE: str = "drone-imagery"
    S3_BUCKET_MODELS: str = "ml-models"
    
    # SMS Gateway (Jazz/Telenor)
    SMS_GATEWAY_URL: str = "https://api.jazzcash.pk/sms/v1"
    SMS_API_KEY: str = ""
    
    # Monitoring
    ENABLE_METRICS: bool = True
    PROMETHEUS_PORT: int = 9090
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
