import torch
import torch.nn as nn
from torchvision import models

class SpatialStream(nn.Module):
    """
    Spatial Stream processing RGB crops of detected faces using an EfficientNet backbone.
    """
    def __init__(self, pretrained: bool = True):
        super().__init__()
        try:
            weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
            self.backbone = models.efficientnet_b0(weights=weights)
        except Exception as e:
            print(f"Warning: Failed to download pretrained weights ({e}). Initializing without pretrained weights.")
            self.backbone = models.efficientnet_b0(weights=None)
            
        self.features = self.backbone.features
        self.pool = nn.AdaptiveAvgPool2d(1)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = self.pool(x)
        x = torch.flatten(x, 1)  # Output size: 1280
        return x

class SpectralStream(nn.Module):
    """
    Spectral Stream processing Discrete Cosine Transform (DCT) matrices using a custom CNN.
    """
    def __init__(self):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),  # Shape: (32, 64, 64)
            
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),  # Shape: (64, 32, 32)
            
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2),  # Shape: (128, 16, 16)
            
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1)  # Shape: (256, 1, 1)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv(x)
        x = torch.flatten(x, 1)  # Output size: 256
        return x

class DualStreamNetwork(nn.Module):
    """
    Dual-Stream network combining Spatial and Spectral features for deepfake detection.
    Outputs: [Real Logit, Fake Logit]
    """
    def __init__(self, pretrained: bool = True):
        super().__init__()
        self.spatial_stream = SpatialStream(pretrained=pretrained)
        self.spectral_stream = SpectralStream()
        
        self.classifier = nn.Sequential(
            nn.Linear(1280 + 256, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 2)  # [Real, Fake] logits
        )
        
    def forward(self, spatial_x: torch.Tensor, spectral_x: torch.Tensor) -> torch.Tensor:
        feat_spatial = self.spatial_stream(spatial_x)
        feat_spectral = self.spectral_stream(spectral_x)
        
        # Fusion by concatenation
        feat_fused = torch.cat((feat_spatial, feat_spectral), dim=1)
        
        logits = self.classifier(feat_fused)
        return logits
