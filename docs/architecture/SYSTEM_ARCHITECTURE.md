# SmartCrop Pakistan - System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │  Mobile App     │  │  USSD Gateway   │  │  Voice Hotline (IVR)   │  │
│  │  (React Native) │  │  (SMS Fallback) │  │  0800-SMARTCROP        │  │
│  │  Android/iOS    │  │  Feature phones │  │  Urdu/Punjabi/Sindhi   │  │
│  └────────┬────────┘  └────────┬────────┘  └───────────┬─────────────┘  │
│           │                    │                       │                │
└───────────┼────────────────────┼───────────────────────┼────────────────┘
            │                    │                       │
            └────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │      API GATEWAY        │
                    │      (FastAPI)          │
                    │  ┌──────────────────┐   │
                    │  │ • Authentication │   │
                    │  │ • Rate Limiting  │   │
                    │  │ • Load Balancing │   │
                    │  │ • Request Routing│   │
                    │  └──────────────────┘   │
                    └────────────┬────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ Farm Service  │      │ Health Service  │      │  AI Agent       │
│ • CRUD ops    │      │ • Analysis      │      │  Service        │
│ • Boundaries  │      │ • Disease detect│      │ • Whisper STT   │
│ • Geospatial  │      │ • Recommendations│     │ • Llama LLM     │
└───────┬───────┘      └────────┬────────┘      │ • RAG Pipeline  │
        │                       │               └────────┬────────┘
        │                       │                        │
        └───────────────────────┼────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   ML INFERENCE LAYER  │
                    │   (TorchServe/ONNX)   │
                    ├───────────────────────┤
                    │ • U-Net Segmentation  │
                    │ • EfficientNet Class. │
                    │ • XGBoost+LSTM Yield  │
                    │ • Llama 3.1 Agent     │
                    └───────────┬───────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│  PostgreSQL   │      │    Redis      │      │    MinIO      │
│  + PostGIS    │      │    Cache      │      │  Object Store │
│  ──────────── │      │  ──────────── │      │  ──────────── │
│  • Farms      │      │  • Sessions   │      │  • Satellite  │
│  • Health     │      │  • Weather    │      │    Images     │
│  • Predictions│      │  • API cache  │      │  • Drone data │
│  • Geospatial │      │  • Rate limits│      │  • ML models  │
└───────────────┘      └───────────────┘      └───────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  EXTERNAL DATA LAYER  │
                    ├───────────────────────┤
                    │ • Sentinel Hub API    │
                    │ • Pakistan Met Dept   │
                    │ • NASA POWER Weather  │
                    │ • Drone Upload Portal │
                    └───────────────────────┘
```

## Component Details

### 1. Client Layer

#### Mobile Application (React Native)

- **Platform:** Android (primary), iOS (secondary)
- **Features:**
  - Farm registration with GPS boundary drawing
  - Real-time health dashboard
  - Voice input in Urdu/Punjabi/Sindhi
  - Offline-first with sync capability
  - Push notifications for alerts
- **Tech Stack:** React Native 0.73, Zustand, React Navigation

#### USSD Gateway

- **Purpose:** Reach farmers without smartphones
- **Protocol:** USSD over GSM
- **Integration:** Jazz/Telenor Pakistan USSD APIs
- **Features:** Menu-driven health queries, alert subscription

#### Voice Hotline (IVR)

- **Number:** 0800-SMARTCROP (toll-free)
- **Languages:** Urdu, Punjabi, Sindhi
- **Tech:** Twilio/Vonage with custom IVR flow
- **Features:** Voice queries, audio advisories

### 2. API Gateway

#### FastAPI Application

- **Framework:** FastAPI 0.109+
- **Features:**
  - OAuth2 JWT authentication
  - Request rate limiting
  - Request/response validation
  - Auto-generated OpenAPI docs
  - CORS for mobile apps

#### Authentication Flow

```
1. Farmer registers with phone number
2. OTP sent via SMS (Jazz/Telenor gateway)
3. OTP verified → JWT issued (7-day expiry)
4. JWT included in all subsequent requests
```

### 3. Microservices

#### Farm Service

- CRUD operations for farm management
- Geospatial boundary storage (PostGIS)
- Farm-to-farmer relationships

#### Health Analysis Service

- Coordinates satellite image fetching
- Triggers ML inference pipeline
- Stores analysis results
- Generates recommendations

#### AI Agent Service

- Whisper integration for speech-to-text
- Llama 3.1 8B fine-tuned on Urdu agricultural corpus
- RAG pipeline with PARC guidelines
- Context-aware responses using farm data

### 4. ML Inference Layer

#### Model Serving

- **Framework:** TorchServe for PyTorch models, ONNX Runtime for edge
- **Hardware:** NVIDIA T4 GPUs (inference optimized)
- **Scaling:** Kubernetes HPA based on request queue

#### Models Deployed

| Model             | Architecture     | Input             | Output        | Latency |
| ----------------- | ---------------- | ----------------- | ------------- | ------- |
| Crop Segmentation | U-Net/DeepLabV3+ | Sentinel-2 4-band | 6-class mask  | 2.5s    |
| Health Classifier | EfficientNet-B4  | RGB 380×380       | 5-class probs | 0.3s    |
| Yield Predictor   | XGBoost + LSTM   | 23 features       | tons/hectare  | 0.1s    |
| Voice Agent       | Whisper + Llama  | Audio/Text        | Text response | 2-5s    |

### 5. Data Layer

#### PostgreSQL + PostGIS

- **Version:** PostgreSQL 15, PostGIS 3.4
- **Purpose:** Primary relational storage
- **Highlights:**
  - Spatial indexing for boundary queries
  - Partitioning by province for scale
  - Read replicas for analytics

#### Redis

- **Version:** Redis 7
- **Purpose:** Caching and rate limiting
- **Cached Data:**
  - Weather forecasts (1-hour TTL)
  - Recent analysis results (24-hour TTL)
  - Session tokens

#### MinIO (S3-compatible)

- **Purpose:** Object storage
- **Buckets:**
  - `satellite-imagery`: Raw Sentinel-2 data
  - `drone-imagery`: High-res drone uploads
  - `ml-models`: Model artifacts

### 6. External Integrations

#### Sentinel Hub

- **Purpose:** Sentinel-2 satellite imagery
- **Revisit:** Every 5 days
- **Resolution:** 10m multispectral
- **API:** Catalog + Processing

#### Pakistan Meteorological Department

- **Purpose:** Weather data and forecasts
- **Data:** Temperature, rainfall, humidity
- **Updates:** 6-hourly

#### NASA POWER

- **Purpose:** Historical weather for yield models
- **Data:** 40 years of climate data
- **Resolution:** 0.5° × 0.5°

---

## Data Flow: Farm Health Analysis

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Mobile  │────▶│   API    │────▶│ Celery   │────▶│ Sentinel │
│   App    │     │ Gateway  │     │  Task    │     │   Hub    │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                        │                │
                                        │      ┌─────────▼─────────┐
                                        │      │ Download Satellite │
                                        │      │ Imagery (4 bands) │
                                        │      └─────────┬─────────┘
                                        │                │
                                  ┌─────▼─────┐          │
                                  │  MinIO    │◀─────────┘
                                  │  Storage  │
                                  └─────┬─────┘
                                        │
                              ┌─────────▼─────────┐
                              │  ML Pipeline      │
                              │  ┌─────────────┐  │
                              │  │ NDVI/NDWI   │  │
                              │  │ Computation │  │
                              │  └──────┬──────┘  │
                              │         │         │
                              │  ┌──────▼──────┐  │
                              │  │ U-Net       │  │
                              │  │ Segmentation│  │
                              │  └──────┬──────┘  │
                              │         │         │
                              │  ┌──────▼──────┐  │
                              │  │ EfficientNet│  │
                              │  │ Classifier  │  │
                              │  └──────┬──────┘  │
                              └─────────┼─────────┘
                                        │
                              ┌─────────▼─────────┐
                              │  PostgreSQL       │
                              │  Store Results    │
                              └─────────┬─────────┘
                                        │
                              ┌─────────▼─────────┐
                              │  Push Notification│
                              │  to Mobile App    │
                              └───────────────────┘
```

---

## Deployment Architecture

### Infrastructure (Pakistan Cloud)

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
│                    (NAYATEL Datacenter)                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ API Pods    │  │ ML Pods     │  │ Worker Pods │          │
│  │ (3 replicas)│  │ (GPU nodes) │  │ (Celery)    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                 Ingress Controller                   │    │
│  │                 (NGINX + Cert Manager)               │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
         ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
         │PostgreSQL│    │  Redis  │    │  MinIO  │
         │ HA Cluster│   │ Sentinel│    │ Cluster │
         └──────────┘    └─────────┘    └─────────┘
```

### Scaling Strategy

| Component      | Min                    | Max | Trigger         |
| -------------- | ---------------------- | --- | --------------- |
| API Pods       | 3                      | 20  | CPU > 70%       |
| ML Pods        | 2                      | 8   | GPU Queue > 100 |
| Celery Workers | 5                      | 50  | Queue length    |
| PostgreSQL     | 1 primary + 2 replicas | -   | Manual          |

---

## Security Architecture

### Authentication & Authorization

- **Protocol:** OAuth 2.0 with JWT
- **Token Lifetime:** 7 days (refresh supported)
- **Scopes:** `farms:read`, `farms:write`, `health:analyze`, `agent:query`

### Data Protection

- **In Transit:** TLS 1.3
- **At Rest:** AES-256 encryption
- **PII:** Phone numbers hashed, location data anonymized for analytics

### Compliance

- Pakistan Personal Data Protection Bill 2023
- Farmer consent for data collection (Urdu/Punjabi forms)

---

## Monitoring & Observability

```
┌───────────────────────────────────────────────────────────┐
│                     Prometheus                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│  │ API Metrics │  │ ML Metrics  │  │ Infrastructure  │    │
│  │ • Latency   │  │ • Inference │  │ • CPU/Memory    │    │
│  │ • Errors    │  │ • Accuracy  │  │ • Disk/Network  │    │
│  └─────────────┘  └─────────────┘  └─────────────────┘    │
└───────────────────────────┬───────────────────────────────┘
                            │
                    ┌───────▼───────┐
                    │    Grafana    │
                    │  Dashboards   │
                    └───────────────┘
```

### Key Metrics

- API response time (P50, P95, P99)
- ML inference latency
- Satellite image processing time
- Voice recognition accuracy
- Error rates by endpoint
