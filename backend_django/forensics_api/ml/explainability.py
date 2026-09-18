import cv2
import torch
import numpy as np

class GradCAM:
    """
    Grad-CAM tracking utility to output visual target anomaly heatmaps for the Spatial Stream.
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
        Generates the 2D Grad-CAM heatmap for a target class.
        
        Args:
            spatial_tensor: Spatial input, shape (1, 3, 224, 224)
            spectral_tensor: Spectral input, shape (1, 1, 128, 128)
            class_idx: Index of class to compute gradients for (default: 1 for 'Fake')
            
        Returns:
            A normalized 2D numpy array heatmap, shape equal to target layer feature maps.
        """
        self.gradients = None
        self.activations = None
        
        self.model.zero_grad()
        
        # Ensure gradients are tracked
        spatial_tensor = spatial_tensor.clone().detach().requires_grad_(True)
        
        # Forward pass
        logits = self.model(spatial_tensor, spectral_tensor)
        
        # Target class logit
        score = logits[0, class_idx]
        
        # Backward pass
        score.backward()
        
        if self.gradients is None or self.activations is None:
            raise RuntimeError("Failed to hook activations or gradients. Check the target layer configuration.")
            
        # Global average pool gradients
        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)  # (1, C, 1, 1)
        
        # Weighted combination of activations
        heatmap = torch.sum(weights * self.activations, dim=1)  # (1, H, W)
        
        # ReLU activation map
        heatmap = torch.relu(heatmap)
        
        # Move to CPU and convert to numpy
        heatmap = heatmap.squeeze(0).cpu().detach().numpy()
        
        # Normalize heatmap to [0, 1]
        h_max = heatmap.max()
        if h_max > 0:
            heatmap = heatmap / h_max
        else:
            heatmap = np.zeros_like(heatmap)
            
        return heatmap
        
    def remove_hooks(self):
        self.forward_hook.remove()
        self.backward_hook.remove()

def overlay_heatmap(img_rgb: np.ndarray, heatmap: np.ndarray, alpha: float = 0.6) -> np.ndarray:
    """
    Overlays the Grad-CAM heatmap on the input RGB face image.
    
    Args:
        img_rgb: RGB face crop, values in [0, 1] float32.
        heatmap: 2D Grad-CAM heatmap, values in [0, 1] float32.
        alpha: Blend ratio of the input image.
        
    Returns:
        Blended RGB image as a uint8 numpy array.
    """
    # Convert image to uint8 [0, 255]
    img_uint8 = (img_rgb * 255.0).astype(np.uint8)
    
    # Resize heatmap to match image size
    heatmap_resized = cv2.resize(heatmap, (img_uint8.shape[1], img_uint8.shape[0]), interpolation=cv2.INTER_LINEAR)
    
    # Apply JET colormap (returns BGR)
    heatmap_color_bgr = cv2.applyColorMap((heatmap_resized * 255.0).astype(np.uint8), cv2.COLORMAP_JET)
    
    # Convert BGR to RGB
    heatmap_color_rgb = cv2.cvtColor(heatmap_color_bgr, cv2.COLOR_BGR2RGB)
    
    # Blend original and heatmap
    overlayed = cv2.addWeighted(img_uint8, alpha, heatmap_color_rgb, 1.0 - alpha, 0)
    return overlayed
