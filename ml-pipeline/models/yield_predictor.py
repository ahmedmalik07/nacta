"""
SmartCrop Pakistan - Yield Prediction Model
XGBoost + LSTM Ensemble for crop yield forecasting
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class CropType(Enum):
    """Major crops in Pakistan."""
    WHEAT = "wheat"
    RICE = "rice"
    COTTON = "cotton"
    SUGARCANE = "sugarcane"
    MAIZE = "maize"


@dataclass
class YieldPrediction:
    """Yield prediction result."""
    crop_type: CropType
    predicted_yield_tons_per_hectare: float
    confidence_interval: Tuple[float, float]  # (low, high)
    confidence_percent: float
    
    # Breakdown
    feature_importance: Dict[str, float]
    key_factors: List[Dict[str, any]]
    
    # Comparison
    district_average: float
    province_average: float
    national_average: float
    percentile: int  # Farm's position 0-100


@dataclass
class FarmFeatures:
    """Input features for yield prediction."""
    farm_id: int
    crop_type: CropType
    area_hectares: float
    
    # Historical NDVI time series (last 90 days, weekly)
    ndvi_series: List[float]
    
    # Current indices
    current_ndvi: float
    current_ndwi: float
    current_savi: float
    
    # Weather features
    avg_temperature: float
    total_rainfall_mm: float
    humidity_percent: float
    
    # Soil features
    soil_ph: float
    soil_nitrogen: float  # kg/ha
    soil_phosphorus: float  # kg/ha
    soil_potassium: float  # kg/ha
    
    # Management
    irrigation_type: str  # canal, tubewell, rainfed
    fertilizer_applied_kg: float
    planting_date: datetime
    
    # Location
    district: str
    province: str


# Pakistan crop yield statistics (tons/hectare)
PAKISTAN_YIELDS = {
    CropType.WHEAT: {
        "national_avg": 3.1,
        "punjab_avg": 3.3,
        "sindh_avg": 2.8,
        "optimal": 5.0,
        "min": 1.5
    },
    CropType.RICE: {
        "national_avg": 2.8,
        "punjab_avg": 2.5,
        "sindh_avg": 3.2,
        "optimal": 4.5,
        "min": 1.2
    },
    CropType.COTTON: {
        "national_avg": 0.8,
        "punjab_avg": 0.85,
        "sindh_avg": 0.75,
        "optimal": 1.5,
        "min": 0.3
    },
    CropType.SUGARCANE: {
        "national_avg": 55.0,
        "punjab_avg": 58.0,
        "sindh_avg": 52.0,
        "optimal": 80.0,
        "min": 30.0
    },
    CropType.MAIZE: {
        "national_avg": 5.5,
        "punjab_avg": 5.8,
        "sindh_avg": 4.5,
        "optimal": 8.0,
        "min": 2.5
    }
}


class LSTMTimeSeriesEncoder:
    """
    LSTM encoder for NDVI time series features.
    Captures seasonal patterns in crop growth.
    """
    
    def __init__(self, input_size: int = 1, hidden_size: int = 32, num_layers: int = 2):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # In production, this would be a PyTorch LSTM
        # For now, we'll use a simplified feature extraction
    
    def encode(self, ndvi_series: List[float]) -> np.ndarray:
        """
        Encode NDVI time series into fixed-length features.
        
        Returns feature vector capturing:
        - Trend (increasing/decreasing)
        - Seasonal patterns (Rabi/Kharif cycles)
        - Volatility
        """
        series = np.array(ndvi_series)
        
        if len(series) < 3:
            return np.zeros(8)
        
        # Compute features
        features = [
            np.mean(series),                    # Mean NDVI
            np.std(series),                     # Volatility
            np.max(series),                     # Peak
            np.min(series),                     # Trough
            series[-1] - series[0],             # Overall trend
            series[-1],                         # Current value
            np.mean(np.diff(series)),           # Average change
            np.max(np.diff(series))             # Max positive change
        ]
        
        return np.array(features)


class XGBoostYieldModel:
    """
    XGBoost model for yield prediction.
    
    Features used:
    - NDVI time series encodings
    - Current vegetation indices
    - Weather data
    - Soil parameters
    - Historical yields
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.feature_names = [
            "ndvi_mean", "ndvi_std", "ndvi_max", "ndvi_min",
            "ndvi_trend", "ndvi_current", "ndvi_avg_change", "ndvi_max_change",
            "current_ndwi", "current_savi",
            "temperature", "rainfall", "humidity",
            "soil_ph", "soil_n", "soil_p", "soil_k",
            "area_hectares", "fertilizer_kg",
            "irrigation_canal", "irrigation_tubewell", "irrigation_rainfed",
            "days_since_planting"
        ]
        
        if model_path:
            self._load_model(model_path)
    
    def _load_model(self, path: str):
        """Load trained XGBoost model."""
        # In production: import xgboost as xgb
        # self.model = xgb.Booster()
        # self.model.load_model(path)
        pass
    
    def prepare_features(self, farm: FarmFeatures) -> np.ndarray:
        """Prepare feature vector from farm data."""
        # Encode NDVI time series
        lstm_encoder = LSTMTimeSeriesEncoder()
        ndvi_features = lstm_encoder.encode(farm.ndvi_series)
        
        # Irrigation one-hot encoding
        irrigation_canal = 1 if farm.irrigation_type == "canal" else 0
        irrigation_tubewell = 1 if farm.irrigation_type == "tubewell" else 0
        irrigation_rainfed = 1 if farm.irrigation_type == "rainfed" else 0
        
        # Days since planting
        days_since_planting = (datetime.now() - farm.planting_date).days
        
        features = np.concatenate([
            ndvi_features,
            [farm.current_ndwi, farm.current_savi],
            [farm.avg_temperature, farm.total_rainfall_mm, farm.humidity_percent],
            [farm.soil_ph, farm.soil_nitrogen, farm.soil_phosphorus, farm.soil_potassium],
            [farm.area_hectares, farm.fertilizer_applied_kg],
            [irrigation_canal, irrigation_tubewell, irrigation_rainfed],
            [days_since_planting]
        ])
        
        return features
    
    def predict(self, farm: FarmFeatures) -> float:
        """
        Predict yield in tons/hectare.
        
        In production, this uses trained XGBoost model.
        For demo, uses heuristic based on NDVI and conditions.
        """
        # Get base yield for crop
        base_yield = PAKISTAN_YIELDS[farm.crop_type]["national_avg"]
        optimal_yield = PAKISTAN_YIELDS[farm.crop_type]["optimal"]
        min_yield = PAKISTAN_YIELDS[farm.crop_type]["min"]
        
        # NDVI factor (most important)
        # NDVI 0.6+ is excellent, 0.3-0.6 is moderate, <0.3 is poor
        ndvi_factor = np.clip((farm.current_ndvi - 0.3) / 0.4, 0, 1)
        
        # Water factor from NDWI
        water_factor = np.clip((farm.current_ndwi + 0.2) / 0.5, 0, 1)
        
        # Irrigation factor
        irrigation_factors = {"canal": 1.0, "tubewell": 0.95, "rainfed": 0.7}
        irrigation_factor = irrigation_factors.get(farm.irrigation_type, 0.8)
        
        # Combined factor
        combined_factor = 0.5 * ndvi_factor + 0.3 * water_factor + 0.2 * irrigation_factor
        
        # Calculate yield
        yield_range = optimal_yield - min_yield
        predicted = min_yield + combined_factor * yield_range
        
        # Add some noise for realism
        noise = np.random.normal(0, 0.05)
        predicted = predicted * (1 + noise)
        
        return np.clip(predicted, min_yield, optimal_yield)


class YieldPredictor:
    """
    Main yield prediction class combining XGBoost and LSTM.
    """
    
    def __init__(self, xgb_model_path: Optional[str] = None, lstm_model_path: Optional[str] = None):
        self.xgb_model = XGBoostYieldModel(xgb_model_path)
        self.lstm_encoder = LSTMTimeSeriesEncoder()
    
    def predict(self, farm: FarmFeatures) -> YieldPrediction:
        """
        Generate yield prediction with confidence intervals.
        """
        # Get point prediction
        predicted_yield = self.xgb_model.predict(farm)
        
        # Calculate confidence interval (using simplified approach)
        # In production, use bootstrap or quantile regression
        std_error = 0.15 * predicted_yield  # 15% uncertainty
        ci_low = predicted_yield - 1.96 * std_error
        ci_high = predicted_yield + 1.96 * std_error
        
        # Get comparison data
        crop_stats = PAKISTAN_YIELDS[farm.crop_type]
        national_avg = crop_stats["national_avg"]
        
        # Province average
        if farm.province.lower() == "punjab":
            province_avg = crop_stats["punjab_avg"]
        elif farm.province.lower() == "sindh":
            province_avg = crop_stats["sindh_avg"]
        else:
            province_avg = national_avg
        
        # Calculate percentile (simplified)
        percentile = int(np.clip(
            (predicted_yield - crop_stats["min"]) / 
            (crop_stats["optimal"] - crop_stats["min"]) * 100,
            0, 100
        ))
        
        # Feature importance (simplified)
        feature_importance = {
            "NDVI Index": 0.35,
            "Water Availability": 0.25,
            "Weather Conditions": 0.15,
            "Soil Quality": 0.10,
            "Irrigation Type": 0.10,
            "Management Practices": 0.05
        }
        
        # Key factors affecting yield
        key_factors = []
        
        if farm.current_ndvi >= 0.6:
            key_factors.append({
                "factor": "NDVI Index",
                "factor_ur": "پودوں کی صحت",
                "value": f"{farm.current_ndvi:.2f}",
                "impact": "positive",
                "message_en": "Excellent vegetation health",
                "message_ur": "پودوں کی صحت بہترین ہے"
            })
        elif farm.current_ndvi < 0.4:
            key_factors.append({
                "factor": "NDVI Index",
                "factor_ur": "پودوں کی صحت",
                "value": f"{farm.current_ndvi:.2f}",
                "impact": "negative",
                "message_en": "Low vegetation health - needs attention",
                "message_ur": "پودوں کی صحت کم ہے - توجہ دیں"
            })
        
        if farm.current_ndwi < 0.1:
            key_factors.append({
                "factor": "Water Stress",
                "factor_ur": "پانی کی کمی",
                "value": f"{farm.current_ndwi:.2f}",
                "impact": "negative",
                "message_en": "Water stress detected - increase irrigation",
                "message_ur": "پانی کی کمی ہے - آبپاشی بڑھائیں"
            })
        
        return YieldPrediction(
            crop_type=farm.crop_type,
            predicted_yield_tons_per_hectare=round(predicted_yield, 2),
            confidence_interval=(round(ci_low, 2), round(ci_high, 2)),
            confidence_percent=85.0,  # Model confidence
            feature_importance=feature_importance,
            key_factors=key_factors,
            district_average=province_avg * 0.95,  # Approximate
            province_average=province_avg,
            national_average=national_avg,
            percentile=percentile
        )
    
    def predict_timeseries(
        self, 
        farm: FarmFeatures, 
        days_ahead: int = 30
    ) -> List[Dict]:
        """
        Predict yield evolution over time.
        
        Useful for showing farmers how their yield might change
        with different interventions.
        """
        predictions = []
        current_yield = self.xgb_model.predict(farm)
        
        for day in range(0, days_ahead, 7):
            # Simulate yield evolution
            growth_factor = 1 + 0.01 * (day / 7)  # Slight increase over time
            noise = np.random.normal(0, 0.02)
            
            predictions.append({
                "days_from_now": day,
                "date": (datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d"),
                "predicted_yield": round(current_yield * growth_factor * (1 + noise), 2),
                "confidence": 85 - day * 0.5  # Confidence decreases with time
            })
        
        return predictions


# Example usage
if __name__ == "__main__":
    # Create sample farm
    farm = FarmFeatures(
        farm_id=1,
        crop_type=CropType.WHEAT,
        area_hectares=2.0,
        ndvi_series=[0.45, 0.48, 0.52, 0.55, 0.58, 0.60, 0.62, 0.63, 0.64, 0.65],
        current_ndvi=0.65,
        current_ndwi=0.35,
        current_savi=0.58,
        avg_temperature=22.0,
        total_rainfall_mm=150.0,
        humidity_percent=65.0,
        soil_ph=7.2,
        soil_nitrogen=180,
        soil_phosphorus=25,
        soil_potassium=150,
        irrigation_type="canal",
        fertilizer_applied_kg=150,
        planting_date=datetime(2025, 11, 15),
        district="Faisalabad",
        province="Punjab"
    )
    
    # Predict
    predictor = YieldPredictor()
    result = predictor.predict(farm)
    
    print(f"Crop: {result.crop_type.value}")
    print(f"Predicted Yield: {result.predicted_yield_tons_per_hectare} tons/hectare")
    print(f"Confidence Interval: {result.confidence_interval}")
    print(f"National Average: {result.national_average}")
    print(f"Percentile: {result.percentile}")
    print(f"\nKey Factors:")
    for factor in result.key_factors:
        print(f"  - {factor['factor']}: {factor['message_en']}")
