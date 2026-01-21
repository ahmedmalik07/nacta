# SmartCrop Pakistan - ML Model Cards

## Model 1: Crop Health Segmentation (U-Net)

### Model Details

| Property           | Value                                        |
| ------------------ | -------------------------------------------- |
| **Model Name**     | SmartCrop-UNet-Segmentation-v1               |
| **Architecture**   | U-Net with ResNet-34 encoder                 |
| **Framework**      | PyTorch 2.1                                  |
| **Input**          | 4-band Sentinel-2 (B2, B3, B4, B8) - 512×512 |
| **Output**         | 6-class segmentation mask                    |
| **Parameters**     | 24.4M                                        |
| **Inference Time** | 250ms (GPU), 1.8s (CPU)                      |

### Classes

| Class ID | Name (EN)          | Name (UR)    | Color  |
| -------- | ------------------ | ------------ | ------ |
| 0        | Healthy Vegetation | صحت مند پودے | Green  |
| 1        | Moderate Stress    | معتدل دباؤ   | Yellow |
| 2        | Severe Stress      | شدید دباؤ    | Orange |
| 3        | Critical/Dead      | نازک/مردہ    | Red    |
| 4        | Water Bodies       | پانی         | Blue   |
| 5        | Non-Vegetation     | غیر پودے     | Gray   |

### Training Data

- **Source**: Sentinel-2 L2A imagery
- **Region**: Punjab & Sindh, Pakistan
- **Time Period**: 2020-2024 (growing seasons)
- **Samples**: 15,000 labeled patches
- **Annotation**: Manual + semi-automatic with PARC agronomists
- **Split**: 70% train, 15% validation, 15% test

### Performance Metrics

| Metric             | Value |
| ------------------ | ----- |
| Mean IoU           | 0.78  |
| Pixel Accuracy     | 0.89  |
| Class-weighted F1  | 0.82  |
| Healthy Class IoU  | 0.85  |
| Stressed Class IoU | 0.74  |

### Intended Use

- Farm-level crop health monitoring
- Stress zone identification
- Irrigation planning support
- Punjab & Sindh wheat, rice, cotton crops

### Limitations

- Cloud coverage >20% degrades accuracy
- Best for crops at mid-growth stage (NDVI > 0.3)
- Not validated for orchards or mixed cropping

### Ethical Considerations

- Model trained on Pakistan agricultural data only
- Predictions are advisory, not definitive
- Always recommend verification with field visits

---

## Model 2: Crop Disease Classifier (EfficientNet-B4)

### Model Details

| Property           | Value                             |
| ------------------ | --------------------------------- |
| **Model Name**     | SmartCrop-EfficientNet-Disease-v1 |
| **Architecture**   | EfficientNet-B4                   |
| **Framework**      | PyTorch 2.1                       |
| **Input**          | RGB image - 380×380               |
| **Output**         | 5-class probabilities             |
| **Parameters**     | 19M                               |
| **Inference Time** | 45ms (GPU), 320ms (CPU)           |

### Classes

| Class | Disease/Condition | Urdu Name     |
| ----- | ----------------- | ------------- |
| 0     | Healthy           | صحت مند       |
| 1     | Leaf Rust         | پتی کی زنگ    |
| 2     | Yellow Rust       | پیلی زنگ      |
| 3     | Powdery Mildew    | سفید پھپھوندی |
| 4     | Septoria          | سیپٹوریا      |

### Training Data

- **Source**: Field photos from PARC research stations
- **Augmentation**: Rotation, flip, color jitter, cutout
- **Samples**: 25,000 images
- **Balance**: Oversampled minority classes
- **Validation**: Expert agronomist review

### Performance Metrics

| Metric    | Value |
| --------- | ----- |
| Accuracy  | 0.91  |
| Macro F1  | 0.87  |
| Precision | 0.89  |
| Recall    | 0.86  |
| AUC-ROC   | 0.94  |

### Per-Class Performance

| Class          | Precision | Recall | F1   |
| -------------- | --------- | ------ | ---- |
| Healthy        | 0.94      | 0.95   | 0.94 |
| Leaf Rust      | 0.88      | 0.85   | 0.86 |
| Yellow Rust    | 0.85      | 0.82   | 0.83 |
| Powdery Mildew | 0.86      | 0.84   | 0.85 |
| Septoria       | 0.83      | 0.80   | 0.81 |

### Intended Use

- Field-level disease identification from smartphone photos
- Early warning for disease outbreaks
- Treatment recommendation support

### Limitations

- Trained on wheat diseases only (v1)
- Requires clear, well-lit photos
- Single-disease assumption (no multi-label)
- Confidence threshold: 0.7 recommended

### Ethical Considerations

- False negatives could lead to crop loss - recommend professional verification
- Model continuously updated with new disease data

---

## Model 3: Yield Prediction (XGBoost + LSTM Ensemble)

### Model Details

| Property           | Value                               |
| ------------------ | ----------------------------------- |
| **Model Name**     | SmartCrop-YieldPredictor-v1         |
| **Architecture**   | XGBoost + LSTM Ensemble (70/30)     |
| **Framework**      | XGBoost 2.0, PyTorch 2.1            |
| **Input**          | 23 features (tabular + time series) |
| **Output**         | Yield (tons/hectare) + confidence   |
| **Parameters**     | XGBoost: 500 trees, LSTM: 2.1M      |
| **Inference Time** | 15ms                                |

### Input Features

| Category   | Features                             |
| ---------- | ------------------------------------ |
| Vegetation | NDVI (mean, std, trend), NDWI, EVI   |
| Weather    | Temperature, rainfall, humidity, GDD |
| Soil       | Type, pH, organic matter, EC         |
| Farm       | Area, irrigation type, seed variety  |
| Historical | Previous 3 years yield, district avg |

### Training Data

- **Source**: PARC crop cutting experiments + farmer surveys
- **Region**: Punjab & Sindh
- **Crops**: Wheat, rice, cotton
- **Years**: 2015-2024
- **Samples**: 45,000 farm-season records

### Performance Metrics

| Crop   | RMSE (t/ha) | MAE (t/ha) | R²   | MAPE  |
| ------ | ----------- | ---------- | ---- | ----- |
| Wheat  | 0.32        | 0.24       | 0.87 | 8.2%  |
| Rice   | 0.38        | 0.29       | 0.84 | 9.5%  |
| Cotton | 0.28        | 0.21       | 0.82 | 11.3% |

### Prediction Confidence

| Confidence Level | MAPE Range |
| ---------------- | ---------- |
| High (>85%)      | <8%        |
| Medium (70-85%)  | 8-12%      |
| Low (<70%)       | >12%       |

### Intended Use

- Pre-harvest yield estimation
- Market planning for farmers
- Agricultural policy planning
- Crop insurance applications

### Limitations

- Extreme weather events may not be captured
- New seed varieties need calibration
- Best accuracy 4-6 weeks before harvest

---

## Model 4: Urdu Voice Agent (Whisper + Llama)

### Model Details

| Property      | Value                          |
| ------------- | ------------------------------ |
| **STT Model** | Whisper Large-v3               |
| **LLM Model** | Llama 3.1 8B (fine-tuned)      |
| **Framework** | Transformers 4.36              |
| **Languages** | Urdu, Punjabi, Sindhi, English |
| **Latency**   | 2-5 seconds end-to-end         |

### Whisper Performance (Urdu)

| Metric        | Value |
| ------------- | ----- |
| WER (Urdu)    | 12.3% |
| WER (Punjabi) | 15.7% |
| WER (Sindhi)  | 18.2% |

### Llama Fine-tuning

- **Base Model**: Meta Llama 3.1 8B
- **Fine-tuning**: LoRA (r=16, alpha=32)
- **Dataset**: 50,000 Urdu agricultural Q&A pairs
- **Sources**: PARC guidelines, agricultural extension materials

### RAG Knowledge Base

| Source                 | Documents |
| ---------------------- | --------- |
| PARC Publications      | 500+      |
| Crop Management Guides | 120       |
| Pest/Disease Reference | 80        |
| Weather Guidelines     | 40        |

### Safety Measures

- Content filtering for harmful advice
- Confidence thresholds for recommendations
- Escalation to human experts for complex queries

---

## Model Versioning

| Model                   | Current Version | Last Updated | Next Update |
| ----------------------- | --------------- | ------------ | ----------- |
| U-Net Segmentation      | v1.2.0          | 2024-12      | 2025-03     |
| EfficientNet Classifier | v1.1.0          | 2024-11      | 2025-02     |
| Yield Predictor         | v1.3.0          | 2024-12      | 2025-04     |
| Voice Agent             | v1.0.0          | 2024-12      | Continuous  |

## Model Governance

- **Retraining Frequency**: Quarterly (seasonal data updates)
- **Monitoring**: Accuracy drift detection, user feedback analysis
- **Approval**: PARC technical committee review
- **Rollback**: Previous version maintained for 6 months
