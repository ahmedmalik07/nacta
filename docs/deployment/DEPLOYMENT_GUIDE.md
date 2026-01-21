# SmartCrop Pakistan - Deployment Guide

## Prerequisites

- Docker & Docker Compose
- Kubernetes cluster (for production)
- PostgreSQL 15+ with PostGIS
- Redis 7+
- NVIDIA GPU (for ML inference)
- Python 3.11+
- Node.js 18+

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/smartcrop-pk/smartcrop-pakistan.git
cd smartcrop-pakistan
```

### 2. Environment Configuration

Create `.env` file in project root:

```env
# Application
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-super-secret-key-change-in-production

# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/smartcrop

# Redis
REDIS_URL=redis://localhost:6379/0

# Sentinel Hub (Satellite Data)
SENTINEL_HUB_CLIENT_ID=your-client-id
SENTINEL_HUB_CLIENT_SECRET=your-client-secret
SENTINEL_HUB_INSTANCE_ID=your-instance-id

# Pakistan Met Department
PAKISTAN_MET_API_KEY=your-api-key

# ML Models
ML_MODELS_PATH=./ml_models

# Storage
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
```

### 3. Start Services with Docker Compose

```bash
docker-compose up -d
```

This starts:

- PostgreSQL with PostGIS
- Redis
- MinIO (S3-compatible storage)

### 4. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API available at: http://localhost:8000

### 5. Mobile App Setup

```bash
cd mobile-app

# Install dependencies
npm install

# Start Metro bundler
npm start

# Run on Android emulator
npm run android
```

---

## Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL with PostGIS
  postgres:
    image: postgis/postgis:15-3.4
    container_name: smartcrop-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: smartcrop
    ports:
      - '5432:5432'
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ['CMD-SHELL', 'pg_isready -U postgres']
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:7-alpine
    container_name: smartcrop-redis
    ports:
      - '6379:6379'
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  # MinIO (S3-compatible storage)
  minio:
    image: minio/minio:latest
    container_name: smartcrop-minio
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - '9000:9000'
      - '9001:9001'
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

  # Backend API
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: smartcrop-api
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/smartcrop
      - REDIS_URL=redis://redis:6379/0
      - S3_ENDPOINT=http://minio:9000
    ports:
      - '8000:8000'
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./ml_models:/app/ml_models

  # Celery Worker
  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: smartcrop-celery
    command: celery -A app.worker worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/smartcrop
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - api
      - redis
    volumes:
      - ./ml_models:/app/ml_models

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

---

## Production Deployment (Kubernetes)

### 1. Cluster Setup

```bash
# Create namespace
kubectl create namespace smartcrop

# Create secrets
kubectl create secret generic smartcrop-secrets \
  --from-literal=database-url='postgresql+asyncpg://user:pass@postgres:5432/smartcrop' \
  --from-literal=redis-url='redis://redis:6379/0' \
  --from-literal=secret-key='production-secret-key' \
  -n smartcrop
```

### 2. Deploy PostgreSQL (with PostGIS)

```yaml
# k8s/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: smartcrop
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgis/postgis:15-3.4
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_USER
              value: smartcrop
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: smartcrop-secrets
                  key: postgres-password
            - name: POSTGRES_DB
              value: smartcrop
          volumeMounts:
            - name: postgres-storage
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              memory: '1Gi'
              cpu: '500m'
            limits:
              memory: '4Gi'
              cpu: '2'
  volumeClaimTemplates:
    - metadata:
        name: postgres-storage
      spec:
        accessModes: ['ReadWriteOnce']
        resources:
          requests:
            storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: smartcrop
spec:
  ports:
    - port: 5432
  selector:
    app: postgres
```

### 3. Deploy API

```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: smartcrop-api
  namespace: smartcrop
spec:
  replicas: 3
  selector:
    matchLabels:
      app: smartcrop-api
  template:
    metadata:
      labels:
        app: smartcrop-api
    spec:
      containers:
        - name: api
          image: smartcrop/api:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: smartcrop-secrets
                  key: database-url
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: smartcrop-secrets
                  key: redis-url
          resources:
            requests:
              memory: '512Mi'
              cpu: '250m'
            limits:
              memory: '2Gi'
              cpu: '1'
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: smartcrop-api
  namespace: smartcrop
spec:
  ports:
    - port: 80
      targetPort: 8000
  selector:
    app: smartcrop-api
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: smartcrop-api-hpa
  namespace: smartcrop
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: smartcrop-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

### 4. Deploy ML Inference (GPU)

```yaml
# k8s/ml-inference.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: smartcrop-ml
  namespace: smartcrop
spec:
  replicas: 2
  selector:
    matchLabels:
      app: smartcrop-ml
  template:
    metadata:
      labels:
        app: smartcrop-ml
    spec:
      containers:
        - name: torchserve
          image: smartcrop/ml-inference:latest
          ports:
            - containerPort: 8080 # Inference
            - containerPort: 8081 # Management
          resources:
            limits:
              nvidia.com/gpu: 1
            requests:
              memory: '8Gi'
              cpu: '2'
          volumeMounts:
            - name: model-store
              mountPath: /home/model-server/model-store
      nodeSelector:
        nvidia.com/gpu: 'true'
      volumes:
        - name: model-store
          persistentVolumeClaim:
            claimName: model-store-pvc
```

### 5. Ingress Configuration

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: smartcrop-ingress
  namespace: smartcrop
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: '100'
    nginx.ingress.kubernetes.io/rate-limit-window: '1m'
spec:
  tls:
    - hosts:
        - api.smartcrop.pk
      secretName: smartcrop-tls
  rules:
    - host: api.smartcrop.pk
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: smartcrop-api
                port:
                  number: 80
```

### 6. Apply All Configurations

```bash
kubectl apply -f k8s/
```

---

## ML Model Deployment

### 1. Export Models to ONNX

```python
# export_models.py
import torch
from ml_pipeline.models.segmentation import UNetCropSegmentation
from ml_pipeline.models.crop_classifier import EfficientNetCropClassifier

# Export U-Net
unet = UNetCropSegmentation()
unet.load_state_dict(torch.load("unet_trained.pth"))
dummy_input = torch.randn(1, 4, 512, 512)
torch.onnx.export(unet, dummy_input, "models/unet_segmentation.onnx",
                  opset_version=11, dynamic_axes={'input': {0: 'batch'}})

# Export EfficientNet
effnet = EfficientNetCropClassifier()
effnet.load_state_dict(torch.load("efficientnet_trained.pth"))
dummy_input = torch.randn(1, 3, 380, 380)
torch.onnx.export(effnet, dummy_input, "models/efficientnet_classifier.onnx",
                  opset_version=11)
```

### 2. TorchServe Configuration

```properties
# config.properties
inference_address=http://0.0.0.0:8080
management_address=http://0.0.0.0:8081
number_of_netty_threads=32
job_queue_size=1000
model_store=/home/model-server/model-store
load_models=all
```

### 3. Create Model Archive

```bash
torch-model-archiver --model-name crop_segmentation \
  --version 1.0 \
  --model-file models/unet_segmentation.onnx \
  --handler custom_handlers/segmentation_handler.py \
  --export-path model-store
```

---

## Monitoring Setup

### 1. Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'smartcrop-api'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: smartcrop-api
        action: keep
      - source_labels: [__meta_kubernetes_pod_container_port_number]
        regex: '8000'
        action: keep
```

### 2. Grafana Dashboard

Import pre-built dashboards:

- API Performance: `dashboards/api-performance.json`
- ML Inference: `dashboards/ml-inference.json`
- Infrastructure: `dashboards/infrastructure.json`

---

## Backup & Disaster Recovery

### Database Backup

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
pg_dump -h postgres -U smartcrop smartcrop | gzip > backup_$DATE.sql.gz
aws s3 cp backup_$DATE.sql.gz s3://smartcrop-backups/postgres/
```

### Model Versioning

All models stored in MinIO with versioning enabled:

```
s3://ml-models/
├── segmentation/
│   ├── v1.0.0/
│   ├── v1.1.0/
│   └── latest -> v1.1.0
├── classification/
└── yield_prediction/
```

---

## Health Checks

```bash
# Check all services
curl https://api.smartcrop.pk/health

# Expected response
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "redis": "connected",
    "ml_models": "loaded",
    "satellite_api": "connected"
  }
}
```
