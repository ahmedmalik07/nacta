"""
SmartCrop Pakistan - Crop Health Classification Model
EfficientNet-B4 based classifier for crop health status
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np
from PIL import Image
import io


class CropHealthClass(Enum):
    """Crop health classification categories."""
    HEALTHY = 0
    WATER_STRESSED = 1
    NUTRIENT_DEFICIENT = 2
    PEST_INFECTED = 3
    DISEASE_AFFECTED = 4


@dataclass
class ClassificationResult:
    """Result of crop health classification."""
    predicted_class: CropHealthClass
    class_name_en: str
    class_name_ur: str
    confidence: float
    all_probabilities: Dict[str, float]
    
    # Recommendations
    severity: str  # mild, moderate, severe
    recommended_actions: List[Dict[str, str]]


# Class labels in English and Urdu
CLASS_LABELS = {
    CropHealthClass.HEALTHY: {
        "en": "Healthy",
        "ur": "صحت مند"
    },
    CropHealthClass.WATER_STRESSED: {
        "en": "Water Stressed",
        "ur": "پانی کی کمی"
    },
    CropHealthClass.NUTRIENT_DEFICIENT: {
        "en": "Nutrient Deficient",
        "ur": "غذائیت کی کمی"
    },
    CropHealthClass.PEST_INFECTED: {
        "en": "Pest Infected",
        "ur": "کیڑوں کا حملہ"
    },
    CropHealthClass.DISEASE_AFFECTED: {
        "en": "Disease Affected",
        "ur": "بیماری سے متاثر"
    }
}

# Treatment recommendations
RECOMMENDATIONS = {
    CropHealthClass.HEALTHY: [
        {
            "action_en": "Continue current practices",
            "action_ur": "موجودہ طریقے جاری رکھیں",
            "priority": "low"
        }
    ],
    CropHealthClass.WATER_STRESSED: [
        {
            "action_en": "Increase irrigation frequency immediately",
            "action_ur": "فوری طور پر آبپاشی بڑھائیں",
            "priority": "high"
        },
        {
            "action_en": "Apply mulch to retain soil moisture",
            "action_ur": "مٹی کی نمی برقرار رکھنے کے لیے ملچ لگائیں",
            "priority": "medium"
        }
    ],
    CropHealthClass.NUTRIENT_DEFICIENT: [
        {
            "action_en": "Apply nitrogen-rich fertilizer (Urea)",
            "action_ur": "نائٹروجن والی کھاد (یوریا) لگائیں",
            "priority": "high"
        },
        {
            "action_en": "Consider foliar spray for quick nutrient uptake",
            "action_ur": "فوری غذائیت کے لیے پتوں پر سپرے کریں",
            "priority": "medium"
        }
    ],
    CropHealthClass.PEST_INFECTED: [
        {
            "action_en": "Apply appropriate pesticide",
            "action_ur": "مناسب کیڑے مار دوا لگائیں",
            "priority": "high"
        },
        {
            "action_en": "Consider neem oil for organic treatment",
            "action_ur": "قدرتی علاج کے لیے نیم کا تیل استعمال کریں",
            "priority": "medium"
        }
    ],
    CropHealthClass.DISEASE_AFFECTED: [
        {
            "action_en": "Apply fungicide immediately",
            "action_ur": "فوری طور پر فنگیسائڈ لگائیں",
            "priority": "high"
        },
        {
            "action_en": "Remove and destroy affected plants",
            "action_ur": "متاثرہ پودوں کو ہٹا کر تلف کریں",
            "priority": "high"
        },
        {
            "action_en": "Improve air circulation in field",
            "action_ur": "کھیت میں ہوا کی گردش بہتر بنائیں",
            "priority": "medium"
        }
    ]
}


class EfficientNetCropClassifier(nn.Module):
    """
    EfficientNet-B4 based crop health classifier.
    
    Transfer learning from ImageNet, fine-tuned on Pakistan crop images.
    Input: RGB image (380x380)
    Output: 5 class probabilities
    """
    
    def __init__(self, num_classes: int = 5, pretrained: bool = True):
        super().__init__()
        
        # Load EfficientNet-B4 backbone
        # In production, use: from torchvision.models import efficientnet_b4
        # self.backbone = efficientnet_b4(pretrained=pretrained)
        
        # For now, create a simplified model structure
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),
            
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),
            
            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2),
            
            nn.Conv2d(128, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1)
        )
        
        # Classification head
        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, num_classes)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x


class CropHealthClassifier:
    """
    Wrapper class for crop health classification inference.
    """
    
    def __init__(self, model_path: Optional[str] = None, device: str = "cpu"):
        """
        Initialize classifier.
        
        Args:
            model_path: Path to trained model weights
            device: 'cpu' or 'cuda'
        """
        self.device = torch.device(device)
        self.model = EfficientNetCropClassifier()
        
        if model_path:
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        
        self.model.to(self.device)
        self.model.eval()
        
        # Image preprocessing (EfficientNet-B4 input)
        self.transform = transforms.Compose([
            transforms.Resize((380, 380)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
    
    def preprocess(self, image: Image.Image) -> torch.Tensor:
        """Preprocess image for model input."""
        tensor = self.transform(image)
        return tensor.unsqueeze(0)  # Add batch dimension
    
    def predict(self, image: Image.Image) -> ClassificationResult:
        """
        Classify crop health from image.
        
        Args:
            image: PIL Image (RGB)
        
        Returns:
            ClassificationResult with prediction and recommendations
        """
        # Preprocess
        input_tensor = self.preprocess(image).to(self.device)
        
        # Inference
        with torch.no_grad():
            outputs = self.model(input_tensor)
            probabilities = F.softmax(outputs, dim=1)[0]
        
        # Get prediction
        pred_idx = torch.argmax(probabilities).item()
        pred_class = CropHealthClass(pred_idx)
        confidence = probabilities[pred_idx].item()
        
        # All probabilities
        all_probs = {
            CLASS_LABELS[CropHealthClass(i)]["en"]: probabilities[i].item()
            for i in range(len(CropHealthClass))
        }
        
        # Determine severity based on confidence and class
        if pred_class == CropHealthClass.HEALTHY:
            severity = "none"
        elif confidence > 0.8:
            severity = "severe"
        elif confidence > 0.5:
            severity = "moderate"
        else:
            severity = "mild"
        
        return ClassificationResult(
            predicted_class=pred_class,
            class_name_en=CLASS_LABELS[pred_class]["en"],
            class_name_ur=CLASS_LABELS[pred_class]["ur"],
            confidence=confidence,
            all_probabilities=all_probs,
            severity=severity,
            recommended_actions=RECOMMENDATIONS[pred_class]
        )
    
    def predict_from_bytes(self, image_bytes: bytes) -> ClassificationResult:
        """Classify from image bytes."""
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return self.predict(image)
    
    def batch_predict(self, images: List[Image.Image]) -> List[ClassificationResult]:
        """Batch prediction for multiple images."""
        results = []
        
        # Stack tensors for batch processing
        tensors = torch.stack([self.preprocess(img)[0] for img in images])
        tensors = tensors.to(self.device)
        
        with torch.no_grad():
            outputs = self.model(tensors)
            probabilities = F.softmax(outputs, dim=1)
        
        for i, probs in enumerate(probabilities):
            pred_idx = torch.argmax(probs).item()
            pred_class = CropHealthClass(pred_idx)
            confidence = probs[pred_idx].item()
            
            all_probs = {
                CLASS_LABELS[CropHealthClass(j)]["en"]: probs[j].item()
                for j in range(len(CropHealthClass))
            }
            
            severity = "severe" if confidence > 0.8 else "moderate" if confidence > 0.5 else "mild"
            if pred_class == CropHealthClass.HEALTHY:
                severity = "none"
            
            results.append(ClassificationResult(
                predicted_class=pred_class,
                class_name_en=CLASS_LABELS[pred_class]["en"],
                class_name_ur=CLASS_LABELS[pred_class]["ur"],
                confidence=confidence,
                all_probabilities=all_probs,
                severity=severity,
                recommended_actions=RECOMMENDATIONS[pred_class]
            ))
        
        return results


# Disease-specific classifier for wheat (Pakistan's main crop)
class WheatDiseaseClassifier:
    """
    Specialized classifier for wheat diseases common in Pakistan.
    
    Classes:
    - Healthy wheat
    - Wheat rust (سرخی) - Most common in Punjab
    - Powdery mildew (سفید دھول)
    - Loose smut (کانگیاری)
    - Karnal bunt (کرنال بنٹ)
    """
    
    WHEAT_DISEASES = {
        0: {"en": "Healthy", "ur": "صحت مند"},
        1: {"en": "Wheat Rust (Puccinia)", "ur": "گندم کی سرخی"},
        2: {"en": "Powdery Mildew", "ur": "سفید دھول"},
        3: {"en": "Loose Smut", "ur": "کانگیاری"},
        4: {"en": "Karnal Bunt", "ur": "کرنال بنٹ"}
    }
    
    def __init__(self, model_path: Optional[str] = None, device: str = "cpu"):
        self.device = torch.device(device)
        # Similar model architecture, trained on wheat-specific data
        self.model = EfficientNetCropClassifier(num_classes=5)
        
        if model_path:
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        
        self.model.to(self.device)
        self.model.eval()
        
        self.transform = transforms.Compose([
            transforms.Resize((380, 380)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
    
    def predict(self, image: Image.Image) -> Dict:
        """Predict wheat disease."""
        input_tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(input_tensor)
            probs = F.softmax(outputs, dim=1)[0]
        
        pred_idx = torch.argmax(probs).item()
        
        return {
            "disease_id": pred_idx,
            "disease_name_en": self.WHEAT_DISEASES[pred_idx]["en"],
            "disease_name_ur": self.WHEAT_DISEASES[pred_idx]["ur"],
            "confidence": probs[pred_idx].item(),
            "all_probabilities": {
                self.WHEAT_DISEASES[i]["en"]: probs[i].item()
                for i in range(5)
            }
        }


# Example usage
if __name__ == "__main__":
    # Create sample image
    sample_image = Image.new("RGB", (400, 400), color=(100, 150, 100))
    
    # Initialize classifier
    classifier = CropHealthClassifier()
    
    # Predict
    result = classifier.predict(sample_image)
    
    print(f"Predicted Class: {result.class_name_en} / {result.class_name_ur}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Severity: {result.severity}")
    print(f"Recommendations:")
    for rec in result.recommended_actions:
        print(f"  - {rec['action_en']} ({rec['priority']})")
