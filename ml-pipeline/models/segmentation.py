"""
SmartCrop Pakistan - U-Net Crop Segmentation Model
Semantic segmentation for crop health zone mapping
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class SegmentationResult:
    """Result of crop segmentation."""
    mask: np.ndarray  # H x W with class indices
    class_areas: Dict[str, float]  # Percentage of each class
    health_zones: Dict[str, Dict[str, float]]  # Zone statistics
    confidence_map: np.ndarray  # Per-pixel confidence


# Segmentation classes
SEGMENTATION_CLASSES = {
    0: {"name": "background", "color": [0, 0, 0], "name_ur": "پس منظر"},
    1: {"name": "healthy_crop", "color": [0, 128, 0], "name_ur": "صحت مند فصل"},
    2: {"name": "stressed_crop", "color": [255, 255, 0], "name_ur": "دباؤ میں فصل"},
    3: {"name": "diseased_crop", "color": [255, 0, 0], "name_ur": "بیمار فصل"},
    4: {"name": "bare_soil", "color": [139, 69, 19], "name_ur": "خالی زمین"},
    5: {"name": "water", "color": [0, 0, 255], "name_ur": "پانی"}
}


class DoubleConv(nn.Module):
    """Double convolution block for U-Net."""
    
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
    
    def forward(self, x):
        return self.double_conv(x)


class Down(nn.Module):
    """Downsampling block: MaxPool + DoubleConv."""
    
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.maxpool_conv = nn.Sequential(
            nn.MaxPool2d(2),
            DoubleConv(in_channels, out_channels)
        )
    
    def forward(self, x):
        return self.maxpool_conv(x)


class Up(nn.Module):
    """Upsampling block: Upsample + DoubleConv with skip connection."""
    
    def __init__(self, in_channels: int, out_channels: int, bilinear: bool = True):
        super().__init__()
        
        if bilinear:
            self.up = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
            self.conv = DoubleConv(in_channels, out_channels)
        else:
            self.up = nn.ConvTranspose2d(in_channels, in_channels // 2, kernel_size=2, stride=2)
            self.conv = DoubleConv(in_channels, out_channels)
    
    def forward(self, x1, x2):
        x1 = self.up(x1)
        
        # Handle size mismatch
        diffY = x2.size()[2] - x1.size()[2]
        diffX = x2.size()[3] - x1.size()[3]
        x1 = F.pad(x1, [diffX // 2, diffX - diffX // 2,
                        diffY // 2, diffY - diffY // 2])
        
        x = torch.cat([x2, x1], dim=1)
        return self.conv(x)


class UNetCropSegmentation(nn.Module):
    """
    U-Net model for crop health zone segmentation.
    
    Input: Multi-spectral image (RGB + NIR = 4 channels or just RGB = 3 channels)
    Output: Segmentation mask with 6 classes
    
    Architecture based on DeepLabV3+ concepts with U-Net backbone.
    Optimized for Sentinel-2 10m resolution imagery.
    """
    
    def __init__(self, n_channels: int = 4, n_classes: int = 6, bilinear: bool = True):
        super().__init__()
        self.n_channels = n_channels
        self.n_classes = n_classes
        self.bilinear = bilinear
        
        # Encoder
        self.inc = DoubleConv(n_channels, 64)
        self.down1 = Down(64, 128)
        self.down2 = Down(128, 256)
        self.down3 = Down(256, 512)
        factor = 2 if bilinear else 1
        self.down4 = Down(512, 1024 // factor)
        
        # Decoder
        self.up1 = Up(1024, 512 // factor, bilinear)
        self.up2 = Up(512, 256 // factor, bilinear)
        self.up3 = Up(256, 128 // factor, bilinear)
        self.up4 = Up(128, 64, bilinear)
        
        # Output
        self.outc = nn.Conv2d(64, n_classes, kernel_size=1)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Encoder path
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        x5 = self.down4(x4)
        
        # Decoder path with skip connections
        x = self.up1(x5, x4)
        x = self.up2(x, x3)
        x = self.up3(x, x2)
        x = self.up4(x, x1)
        
        logits = self.outc(x)
        return logits


class CropSegmenter:
    """
    Wrapper class for crop segmentation inference.
    """
    
    def __init__(self, model_path: Optional[str] = None, device: str = "cpu"):
        """
        Initialize segmenter.
        
        Args:
            model_path: Path to trained model weights
            device: 'cpu' or 'cuda'
        """
        self.device = torch.device(device)
        self.model = UNetCropSegmentation(n_channels=4, n_classes=6)
        
        if model_path:
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        
        self.model.to(self.device)
        self.model.eval()
    
    def preprocess(
        self, 
        rgb: np.ndarray, 
        nir: Optional[np.ndarray] = None
    ) -> torch.Tensor:
        """
        Preprocess imagery for model input.
        
        Args:
            rgb: RGB image (H, W, 3) normalized 0-1
            nir: NIR band (H, W) normalized 0-1, optional
        
        Returns:
            Tensor (1, C, H, W)
        """
        if nir is not None:
            # Stack RGB + NIR
            image = np.concatenate([rgb, nir[:, :, np.newaxis]], axis=2)
        else:
            # Use RGB only, pad with zeros for NIR
            image = np.concatenate([rgb, np.zeros_like(rgb[:, :, :1])], axis=2)
        
        # Transpose to (C, H, W) and add batch dimension
        tensor = torch.from_numpy(image.transpose(2, 0, 1)).float()
        tensor = tensor.unsqueeze(0)
        
        return tensor
    
    def segment(
        self, 
        rgb: np.ndarray, 
        nir: Optional[np.ndarray] = None
    ) -> SegmentationResult:
        """
        Perform segmentation on satellite imagery.
        
        Args:
            rgb: RGB image (H, W, 3) normalized 0-1
            nir: NIR band (H, W) normalized 0-1
        
        Returns:
            SegmentationResult with mask and statistics
        """
        # Preprocess
        input_tensor = self.preprocess(rgb, nir).to(self.device)
        
        # Inference
        with torch.no_grad():
            logits = self.model(input_tensor)
            probs = F.softmax(logits, dim=1)
            mask = torch.argmax(probs, dim=1)
            confidence = torch.max(probs, dim=1)[0]
        
        # Convert to numpy
        mask_np = mask[0].cpu().numpy()
        confidence_np = confidence[0].cpu().numpy()
        
        # Calculate class areas
        total_pixels = mask_np.size
        class_areas = {}
        for class_idx, class_info in SEGMENTATION_CLASSES.items():
            pixels = np.sum(mask_np == class_idx)
            class_areas[class_info["name"]] = pixels / total_pixels * 100
        
        # Calculate health zones
        healthy_pixels = np.sum(mask_np == 1)
        stressed_pixels = np.sum(mask_np == 2)
        diseased_pixels = np.sum(mask_np == 3)
        crop_pixels = healthy_pixels + stressed_pixels + diseased_pixels
        
        if crop_pixels > 0:
            health_zones = {
                "healthy": {
                    "percent": healthy_pixels / crop_pixels * 100,
                    "area_pixels": int(healthy_pixels),
                    "confidence": float(np.mean(confidence_np[mask_np == 1])) if healthy_pixels > 0 else 0
                },
                "stressed": {
                    "percent": stressed_pixels / crop_pixels * 100,
                    "area_pixels": int(stressed_pixels),
                    "confidence": float(np.mean(confidence_np[mask_np == 2])) if stressed_pixels > 0 else 0
                },
                "diseased": {
                    "percent": diseased_pixels / crop_pixels * 100,
                    "area_pixels": int(diseased_pixels),
                    "confidence": float(np.mean(confidence_np[mask_np == 3])) if diseased_pixels > 0 else 0
                }
            }
        else:
            health_zones = {
                "healthy": {"percent": 0, "area_pixels": 0, "confidence": 0},
                "stressed": {"percent": 0, "area_pixels": 0, "confidence": 0},
                "diseased": {"percent": 0, "area_pixels": 0, "confidence": 0}
            }
        
        return SegmentationResult(
            mask=mask_np,
            class_areas=class_areas,
            health_zones=health_zones,
            confidence_map=confidence_np
        )
    
    def colorize_mask(self, mask: np.ndarray) -> np.ndarray:
        """
        Convert segmentation mask to RGB visualization.
        
        Args:
            mask: Class indices (H, W)
        
        Returns:
            RGB image (H, W, 3)
        """
        h, w = mask.shape
        rgb = np.zeros((h, w, 3), dtype=np.uint8)
        
        for class_idx, class_info in SEGMENTATION_CLASSES.items():
            rgb[mask == class_idx] = class_info["color"]
        
        return rgb
    
    def generate_report(self, result: SegmentationResult) -> Dict:
        """
        Generate bilingual report from segmentation result.
        """
        health_zones = result.health_zones
        
        # Determine overall status
        if health_zones["healthy"]["percent"] > 70:
            status_en = "Healthy"
            status_ur = "صحت مند"
            severity = "low"
        elif health_zones["healthy"]["percent"] > 40:
            status_en = "Moderate Stress"
            status_ur = "معتدل دباؤ"
            severity = "medium"
        else:
            status_en = "Severe Stress"
            status_ur = "شدید دباؤ"
            severity = "high"
        
        recommendations = []
        
        if health_zones["stressed"]["percent"] > 20:
            recommendations.append({
                "type": "water",
                "message_en": f"{health_zones['stressed']['percent']:.1f}% of crop shows water stress. Increase irrigation.",
                "message_ur": f"فصل کا {health_zones['stressed']['percent']:.1f}% حصہ پانی کی کمی میں ہے۔ آبپاشی بڑھائیں۔",
                "priority": "high"
            })
        
        if health_zones["diseased"]["percent"] > 5:
            recommendations.append({
                "type": "disease",
                "message_en": f"{health_zones['diseased']['percent']:.1f}% of crop shows disease symptoms. Apply treatment.",
                "message_ur": f"فصل کا {health_zones['diseased']['percent']:.1f}% حصہ بیمار ہے۔ علاج کریں۔",
                "priority": "high"
            })
        
        return {
            "overall_status": {"en": status_en, "ur": status_ur},
            "severity": severity,
            "health_zones": health_zones,
            "class_areas": result.class_areas,
            "recommendations": recommendations
        }


# ONNX Export utility
def export_to_onnx(model: nn.Module, output_path: str, input_size: Tuple[int, int] = (512, 512)):
    """Export model to ONNX for edge deployment."""
    model.eval()
    dummy_input = torch.randn(1, 4, input_size[0], input_size[1])
    
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=11,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={
            'input': {0: 'batch_size', 2: 'height', 3: 'width'},
            'output': {0: 'batch_size', 2: 'height', 3: 'width'}
        }
    )
    print(f"Model exported to {output_path}")


# Example usage
if __name__ == "__main__":
    # Create sample image
    h, w = 256, 256
    rgb = np.random.rand(h, w, 3).astype(np.float32)
    nir = np.random.rand(h, w).astype(np.float32)
    
    # Initialize segmenter
    segmenter = CropSegmenter()
    
    # Segment
    result = segmenter.segment(rgb, nir)
    
    print(f"Mask shape: {result.mask.shape}")
    print(f"Class areas: {result.class_areas}")
    print(f"Health zones: {result.health_zones}")
    
    # Generate report
    report = segmenter.generate_report(result)
    print(f"\nOverall Status: {report['overall_status']['en']} / {report['overall_status']['ur']}")
    print(f"Severity: {report['severity']}")
