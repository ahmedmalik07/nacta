# SmartCrop Pakistan - API Documentation

## Overview

SmartCrop Pakistan API provides RESTful endpoints for the precision agriculture platform. All endpoints support Urdu responses and are optimized for low-bandwidth conditions.

**Base URL:** `https://api.smartcrop.pk/api/v1`

## Authentication

All protected endpoints require Bearer token authentication:

```
Authorization: Bearer <access_token>
```

### Obtain Token

```http
POST /auth/verify-otp
Content-Type: application/json

{
  "phone": "03001234567",
  "otp": "123456"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 604800
}
```

---

## Farms API

### List All Farms

```http
GET /farms/
Authorization: Bearer <token>
```

**Response:**

```json
{
  "farms": [
    {
      "id": 1,
      "name": "میرا گندم کا کھیت",
      "area_acres": 5.0,
      "center_lat": 31.5204,
      "center_lon": 74.3587,
      "current_crop": "wheat",
      "health_score": 78.5,
      "ndvi_latest": 0.65,
      "last_satellite_analysis": "2026-01-20T10:30:00Z"
    }
  ],
  "total": 1
}
```

### Create Farm

```http
POST /farms/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "نیا کھیت",
  "area_acres": 3.5,
  "boundary_points": [
    {"lat": 31.5200, "lon": 74.3580},
    {"lat": 31.5210, "lon": 74.3580},
    {"lat": 31.5210, "lon": 74.3600},
    {"lat": 31.5200, "lon": 74.3600}
  ],
  "current_crop": "wheat",
  "irrigation_type": "canal"
}
```

### Get Farm Health Summary

```http
GET /farms/{farm_id}/health-summary
Authorization: Bearer <token>
```

**Response:**

```json
{
  "farm_id": 1,
  "farm_name": "میرا گندم کا کھیت",
  "health_score": 78.5,
  "health_status": "Moderate / معتدل",
  "ndvi": 0.65,
  "ndwi": 0.35,
  "last_updated": "2026-01-20T10:30:00Z",
  "alerts_count": 2
}
```

---

## Crop Health API

### Analyze Crop Health

Triggers satellite image analysis for a farm.

```http
POST /health/analyze
Authorization: Bearer <token>
Content-Type: application/json

{
  "farm_id": 1,
  "source": "sentinel-2"
}
```

**Response:**

```json
{
  "farm_id": 1,
  "farm_name": "میرا گندم کا کھیت",
  "analysis_date": "2026-01-21T08:00:00Z",
  "ndvi": 0.72,
  "ndvi_interpretation": "Healthy vegetation / صحت مند پودے",
  "ndwi": 0.45,
  "ndwi_interpretation": "Adequate water / مناسب پانی",
  "savi": 0.68,
  "health_status": "Healthy",
  "health_status_urdu": "صحت مند",
  "health_score": 78.5,
  "confidence": 0.89,
  "healthy_area_percent": 75.0,
  "stressed_area_percent": 20.0,
  "critical_area_percent": 5.0,
  "recommendations": [
    {
      "type": "irrigation",
      "priority": "medium",
      "message_en": "Maintain current irrigation schedule",
      "message_ur": "موجودہ آبپاشی کا شیڈول جاری رکھیں"
    }
  ]
}
```

### Detect Disease from Photo

```http
POST /health/detect-disease?farm_id=1
Authorization: Bearer <token>
Content-Type: multipart/form-data

image: <binary image data>
```

**Response:**

```json
{
  "detected": true,
  "disease_name_en": "Wheat Leaf Rust (Puccinia triticina)",
  "disease_name_ur": "گندم کی پتی کی سرخی (زنگ)",
  "confidence": 0.87,
  "affected_area_percent": 15.0,
  "severity": "moderate",
  "treatment_recommendations": [
    {
      "type": "fungicide",
      "product": "Propiconazole",
      "dosage": "1 liter per acre",
      "message_en": "Apply fungicide within 3 days",
      "message_ur": "3 دن کے اندر فنگیسائڈ لگائیں"
    }
  ]
}
```

---

## Yield Prediction API

### Get Yield Prediction

```http
POST /predictions/predict
Authorization: Bearer <token>
Content-Type: application/json

{
  "farm_id": 1,
  "crop_type": "wheat"
}
```

**Response:**

```json
{
  "farm_id": 1,
  "farm_name": "میرا گندم کا کھیت",
  "crop_type": "wheat",
  "crop_name_urdu": "گندم",
  "predicted_yield_tons_per_hectare": 3.45,
  "predicted_total_yield_tons": 6.9,
  "confidence_interval_low": 2.93,
  "confidence_interval_high": 3.97,
  "confidence_percent": 87.5,
  "district_average_yield": 3.25,
  "pakistan_average_yield": 3.1,
  "yield_percentile": 72,
  "estimated_revenue_pkr": 776250,
  "expected_harvest_date": "2026-04-15",
  "days_to_harvest": 84,
  "key_factors": [
    {
      "factor": "NDVI Index",
      "factor_urdu": "پودوں کی صحت",
      "value": 0.65,
      "impact": "positive",
      "contribution_percent": 35
    }
  ],
  "improvement_suggestions": [
    {
      "suggestion_en": "Optimize irrigation schedule",
      "suggestion_ur": "آبپاشی کا شیڈول بہتر بنائیں",
      "potential_yield_increase": "5-8%"
    }
  ]
}
```

---

## Satellite API

### Get NDVI Time Series

```http
GET /satellite/ndvi-timeseries/{farm_id}?days=90
Authorization: Bearer <token>
```

**Response:**

```json
{
  "farm_id": 1,
  "farm_name": "میرا گندم کا کھیت",
  "period_start": "2025-10-23",
  "period_end": "2026-01-21",
  "measurements": [
    {
      "date": "2025-10-23T00:00:00Z",
      "ndvi_mean": 0.45,
      "ndvi_min": 0.35,
      "ndvi_max": 0.55,
      "cloud_cover": 5.0
    }
  ],
  "trend": "increasing / بڑھ رہا ہے",
  "anomalies": []
}
```

### Get Vegetation Indices

```http
GET /satellite/indices/{farm_id}
Authorization: Bearer <token>
```

**Response:**

```json
{
  "farm_id": 1,
  "calculation_date": "2026-01-21T08:00:00Z",
  "ndvi": 0.65,
  "ndvi_interpretation": "Healthy dense vegetation",
  "ndwi": 0.35,
  "ndwi_interpretation": "Adequate water",
  "savi": 0.58,
  "evi": 0.55,
  "healthy_zone_percent": 65.0,
  "moderate_zone_percent": 25.0,
  "stressed_zone_percent": 10.0,
  "change_from_last_week": 0.03
}
```

---

## AI Agent API

### Text Query

```http
POST /agent/query
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "میری فصل کو کتنا پانی چاہیے؟",
  "language": "ur",
  "farm_id": 1
}
```

**Response:**

```json
{
  "response_text": "آپ کے کھیت میں پانی کی مقدار مناسب ہے (NDWI: 0.35)۔ ہفتے میں 2-3 بار آبپاشی کافی ہے۔",
  "response_audio_url": "/api/v1/agent/tts/resp_123.mp3",
  "language": "ur",
  "confidence": 0.85,
  "farm_context_used": true,
  "sources": ["Pakistan Agriculture Research Council"],
  "suggested_questions": ["کھاد کب لگائیں؟", "فصل کی بیماری کیسے پہچانیں؟"],
  "recommended_actions": [
    {
      "action": "schedule_irrigation",
      "label_ur": "آبپاشی کا شیڈول بنائیں"
    }
  ]
}
```

### Voice Query

```http
POST /agent/voice-query?language=ur&farm_id=1
Authorization: Bearer <token>
Content-Type: multipart/form-data

audio: <binary audio data>
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message in English / اردو میں غلطی کا پیغام"
}
```

### HTTP Status Codes

| Code | Description           |
| ---- | --------------------- |
| 200  | Success               |
| 201  | Created               |
| 400  | Bad Request           |
| 401  | Unauthorized          |
| 403  | Forbidden             |
| 404  | Not Found             |
| 422  | Validation Error      |
| 500  | Internal Server Error |

---

## Rate Limiting

- **Standard:** 100 requests/minute
- **AI Agent:** 20 requests/minute
- **Satellite Analysis:** 10 requests/hour per farm

---

## Webhook Events

Subscribe to real-time alerts:

```http
POST /webhooks/subscribe
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://your-server.com/webhook",
  "events": ["health_alert", "weather_warning", "pest_detection"]
}
```
