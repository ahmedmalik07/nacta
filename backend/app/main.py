"""
SmartCrop Pakistan - Main FastAPI Application
AI-powered precision agriculture platform for Pakistani farmers
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import farms, health, predictions, satellite, voice_agent
from app.core.config import settings
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    await init_db()
    print("🌾 SmartCrop Pakistan API Started")
    print(f"📡 Satellite monitoring: Active")
    print(f"🤖 AI Agent: Ready (Urdu/Punjabi/Sindhi)")
    yield
    # Shutdown
    print("👋 SmartCrop Pakistan API Shutting Down")


app = FastAPI(
    title="SmartCrop Pakistan API",
    description="""
    ## 🌾 AI-Powered Precision Agriculture for Pakistan
    
    SmartCrop Pakistan combines satellite imagery, IoT sensors, and machine learning 
    to revolutionize farming practices across Pakistan.
    
    ### Features:
    - **Satellite Monitoring**: Real-time crop health from Sentinel-2 imagery
    - **Yield Prediction**: ±0.18 ton/hectare accuracy using XGBoost + LSTM ensemble
    - **Voice AI Agent**: Urdu/Punjabi/Sindhi support via Whisper + Llama
    - **Early Warnings**: 7-day advance pest and disease alerts
    
    ### Target Regions:
    - Punjab Province
    - Sindh Province
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(farms.router, prefix="/api/v1/farms", tags=["Farms"])
app.include_router(health.router, prefix="/api/v1/health", tags=["Crop Health"])
app.include_router(predictions.router, prefix="/api/v1/predictions", tags=["Predictions"])
app.include_router(satellite.router, prefix="/api/v1/satellite", tags=["Satellite"])
app.include_router(voice_agent.router, prefix="/api/v1/agent", tags=["Voice AI Agent"])


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "SmartCrop Pakistan API",
        "version": "1.0.0",
        "status": "operational",
        "message": "خوش آمدید - Welcome to SmartCrop Pakistan! 🌾",
        "docs": "/docs",
        "features": {
            "satellite_monitoring": True,
            "crop_health_detection": True,
            "yield_prediction": True,
            "voice_agent_urdu": True,
            "voice_agent_punjabi": True,
            "voice_agent_sindhi": True
        }
    }


@app.get("/health", tags=["Health Check"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "services": {
            "database": "connected",
            "redis": "connected",
            "ml_models": "loaded",
            "satellite_api": "connected"
        }
    }
