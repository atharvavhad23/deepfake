import os
from pathlib import Path
from typing import Tuple, List, Dict, Any
import numpy as np
import torch
from torch.utils.data import Dataset
from torchvision import transforms

class DualStreamDataset(Dataset):
    """
    Custom Dataset class to concurrently load spatial (RGB face crops) and
    spectral (log-DCT matrices) processed npy arrays for deepfake detection.
    """
    def __init__(self, root_dir: str, is_train: bool = True):
        super().__init__()
        self.root_dir = Path(root_dir)
        self.is_train = is_train
        self.samples: List[Dict[str, Any]] = []
        
        # Define directories
        real_spatial_dir = self.root_dir / "real" / "spatial"
        fake_spatial_dir = self.root_dir / "fake" / "spatial"
        
        # Load real samples (label = 0)
        if real_spatial_dir.exists():
            for f in real_spatial_dir.glob("*_spatial.npy"):
                spectral_path = f.parent.parent / "spectral" / f.name.replace("_spatial.npy", "_spectral.npy")
                if spectral_path.exists():
                    self.samples.append({
                        "spatial": f,
                        "spectral": spectral_path,
                        "label": 0
                    })
                    
        # Load fake samples (label = 1)
        if fake_spatial_dir.exists():
            for f in fake_spatial_dir.glob("*_spatial.npy"):
                spectral_path = f.parent.parent / "spectral" / f.name.replace("_spatial.npy", "_spectral.npy")
                if spectral_path.exists():
                    self.samples.append({
                        "spatial": f,
                        "spectral": spectral_path,
                        "label": 1
                    })
                    
        print(f"Loaded {len(self.samples)} samples from {root_dir} (is_train={is_train})")
        
        # Augmentations for the spatial branch
        if self.is_train:
            self.spatial_transform = transforms.Compose([
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.ColorJitter(brightness=0.15, contrast=0.15)
            ])
        else:
            self.spatial_transform = None

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        sample = self.samples[idx]
        
        # 1. Load spatial face crop (expected shape: [256, 256, 3], float32 in [0, 1])
        spatial_arr = np.load(sample["spatial"], allow_pickle=False)
        if spatial_arr.dtype != np.float32:
            spatial_arr = spatial_arr.astype(np.float32)
            
        spatial_tensor = torch.from_numpy(spatial_arr).permute(2, 0, 1) # [3, 256, 256]
        
        # Apply transforms to spatial branch
        if self.spatial_transform is not None:
            spatial_tensor = self.spatial_transform(spatial_tensor)
            
        # 2. Load spectral DCT matrix (expected shape: [256, 256], float32 in [0, 1])
        spectral_arr = np.load(sample["spectral"], allow_pickle=False)
        if spectral_arr.dtype != np.float32:
            spectral_arr = spectral_arr.astype(np.float32)
            
        spectral_tensor = torch.from_numpy(spectral_arr).unsqueeze(0) # [1, 256, 256]
        
        # Label
        label_tensor = torch.tensor(sample["label"], dtype=torch.long)
        
        return spatial_tensor, spectral_tensor, label_tensor
