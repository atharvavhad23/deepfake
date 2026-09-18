import torch
import torch.nn as nn
from torchvision import models

class SpatialStream(nn.Module):
    """
    Spatial Stream processing 256x256 RGB crops of detected faces
    using an EfficientNet-B4 backbone.
    """
    def __init__(self, pretrained: bool = True):
        super().__init__()
        try:
            weights = models.EfficientNet_B4_Weights.DEFAULT if pretrained else None
            self.backbone = models.efficientnet_b4(weights=weights)
        except Exception as e:
            print(f"Warning: Failed to download pretrained EfficientNet-B4 weights ({e}). Initializing without weights.")
            self.backbone = models.efficientnet_b4(weights=None)
            
        in_features = self.backbone.classifier[1].in_features
        
        # Replace the classifier head to output a 512-dimensional embedding
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=0.4, inplace=True),
            nn.Linear(in_features, 512),
            nn.ReLU(),
            nn.BatchNorm1d(512)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)

class SpectralStream(nn.Module):
    """
    Spectral Stream processing 2D Discrete Cosine Transform (DCT) matrices
    using a custom 4-layer ConvNet to produce a 512-dimensional embedding.
    """
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            # Layer 1: [1, 256, 256] -> [32, 128, 128]
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2),
            
            # Layer 2: [32, 128, 128] -> [64, 64, 64]
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2),
            
            # Layer 3: [64, 64, 64] -> [128, 32, 32]
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2),
            
            # Layer 4: [128, 32, 32] -> [256, 16, 16]
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2),
            
            nn.AdaptiveAvgPool2d(1) # [256, 1, 1]
        )
        
        self.fc = nn.Sequential(
            nn.Linear(256, 512),
            nn.ReLU(),
            nn.BatchNorm1d(512)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = torch.flatten(x, 1) # [Batch, 256]
        x = self.fc(x)          # [Batch, 512]
        return x

class NexaShieldModel(nn.Module):
    """
    Hybrid Dual-Stream Network combining Spatial and Spectral branches
    to detect deepfake manipulation signatures.
    """
    def __init__(self, pretrained: bool = True):
        super().__init__()
        self.spatial_stream = SpatialStream(pretrained=pretrained)
        self.spectral_stream = SpectralStream()
        
        # Fusion head: concatenates spatial (512) and spectral (512) embeddings
        self.fusion_head = nn.Sequential(
            nn.Linear(1024, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(p=0.5),
            nn.Linear(256, 2)  # Output logits for [Real, Fake]
        )
        
    def forward(self, spatial_x: torch.Tensor, spectral_x: torch.Tensor) -> torch.Tensor:
        feat_spatial = self.spatial_stream(spatial_x)   # [Batch, 512]
        feat_spectral = self.spectral_stream(spectral_x) # [Batch, 512]
        
        # Concatenate features
        feat_fused = torch.cat((feat_spatial, feat_spectral), dim=1) # [Batch, 1024]
        
        # Classification logits
        logits = self.fusion_head(feat_fused) # [Batch, 2]
        return logits

def test_model_forward():
    print("Running verification of NexaShieldModel forward pass...")
    # Initialize model
    model = NexaShieldModel(pretrained=False)
    model.eval()
    
    # Generate dummy input tensors matching preprocessing shapes
    # Spatial shape: [Batch_Size, Channels, Height, Width] -> [2, 3, 256, 256]
    dummy_spatial = torch.randn(2, 3, 256, 256)
    # Spectral shape: [Batch_Size, Channels, Height, Width] -> [2, 1, 256, 256]
    dummy_spectral = torch.randn(2, 1, 256, 256)
    
    with torch.no_grad():
        output = model(dummy_spatial, dummy_spectral)
        
    print(f"Input spatial tensor shape: {dummy_spatial.shape}")
    print(f"Input spectral tensor shape: {dummy_spectral.shape}")
    print(f"Output logits shape: {output.shape} (Expected: [2, 2])")
    
    assert output.shape == (2, 2), f"Error: Expected shape [2, 2], got {output.shape}"
    print("Verification successful! Tensor dimensions align perfectly.")

if __name__ == "__main__":
    test_model_forward()
