import cv2
import torch
import numpy as np
from typing import Tuple

class GradCAM:
    """
    Grad-CAM class activation mapping generator tailored for the spatial branch 
    of the NexaShield dual-stream network model.
    """
    def __init__(self, model: torch.nn.Module, target_layer: torch.nn.Module):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        # Register hooks
        self.forward_hook = self.target_layer.register_forward_hook(self._save_activation)
        self.backward_hook = self.target_layer.register_full_backward_hook(self._save_gradient)
        
    def _save_activation(self, module, input, output):
        self.activations = output
        
    def _save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0]
        
    def generate_heatmap(
        self, 
        spatial_tensor: torch.Tensor, 
        spectral_tensor: torch.Tensor, 
        class_idx: int = 1
    ) -> np.ndarray:
        """
        Generates the 2D normalized Grad-CAM activation heatmap.
        """
        self.gradients = None
        self.activations = None
        
        # Reset model gradients
        self.model.zero_grad()
        
        # Enable gradient tracking on spatial input tensor
        spatial_tensor = spatial_tensor.clone().detach().requires_grad_(True)
        
        # Run forward pass
        logits = self.model(spatial_tensor, spectral_tensor)
        
        # Select target logit score
        score = logits[0, class_idx]
        
        # Backward pass
        score.backward()
        
        if self.gradients is None or self.activations is None:
            raise RuntimeError("Grad-CAM hooks failed to capture activations or gradients.")
            
        # Get gradient weights via global average pooling
        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True) # [1, C, 1, 1]
        
        # Weighted combination of forward activation maps
        heatmap = torch.sum(weights * self.activations, dim=1) # [1, H, W]
        
        # Apply ReLU to map positive activation regions
        heatmap = torch.relu(heatmap)
        
        # Convert to numpy array on CPU
        heatmap = heatmap.squeeze(0).cpu().detach().numpy()
        
        # Normalize to [0.0, 1.0]
        h_max = heatmap.max()
        if h_max > 0:
            heatmap = heatmap / h_max
        else:
            heatmap = np.zeros_like(heatmap)
            
        return heatmap
        
    def remove_hooks(self):
        """
        Safely removes registered forward and backward hooks.
        """
        self.forward_hook.remove()
        self.backward_hook.remove()

def overlay_heatmap(img_rgb: np.ndarray, heatmap: np.ndarray, alpha: float = 0.6) -> np.ndarray:
    """
    Overlays the 2D Grad-CAM heatmap onto the original RGB face crop using OpenCV.
    
    Args:
        img_rgb: Original RGB face crop, shape [H, W, 3], range [0.0, 1.0].
        heatmap: 2D heatmap matrix, shape [H_feat, W_feat], range [0.0, 1.0].
        alpha: Blend ratio of original image.
        
    Returns:
        Overlayed RGB face crop as a uint8 image [0, 255].
    """
    # Convert RGB float image [0, 1] to uint8 [0, 255]
    img_uint8 = (img_rgb * 255.0).astype(np.uint8)
    
    # Resize heatmap to match original crop dimension
    heatmap_resized = cv2.resize(heatmap, (img_uint8.shape[1], img_uint8.shape[0]), interpolation=cv2.INTER_LINEAR)
    
    # Convert heatmap values to uint8 [0, 255]
    heatmap_uint8 = (heatmap_resized * 255.0).astype(np.uint8)
    
    # Apply JET colormap (produces BGR image)
    heatmap_color_bgr = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    
    # Convert BGR colormap to RGB
    heatmap_color_rgb = cv2.cvtColor(heatmap_color_bgr, cv2.COLOR_BGR2RGB)
    
    # Blend images together
    blended = cv2.addWeighted(img_uint8, alpha, heatmap_color_rgb, 1.0 - alpha, 0)
    return blended
