import json
from pathlib import Path
from typing import Tuple, List

import numpy as np
import torch
from torch.utils.data import Dataset
from torchvision import transforms


class DeepfakeDataset(Dataset):
    """
    A robust Dataset loader for deepfake classification that loads preprocessed .npy face crops.
    """
    def __init__(self, metadata_path: str, is_train: bool = True):
        super().__init__()
        self.metadata_path = Path(metadata_path)
        if self.metadata_path.is_dir():
            self.metadata_path = self.metadata_path / "metadata.json"
            
        with open(self.metadata_path, 'r') as f:
            data = json.load(f)
            
        self.samples = []
        for item in data:
            # Safely extract labels, handling strings like 'Real', 'Fake' or integers
            label_val = item.get('label', item.get('class_name'))
            if isinstance(label_val, str):
                label_str = label_val.lower()
                label = 1 if 'fake' in label_str else 0
            else:
                label = int(label_val)

            npy_path = item.get('output_path') or item.get('npy_path')
            
            # Resolve the path relative to the metadata.json
            full_path = Path(npy_path)
            if not full_path.is_absolute():
                full_path = self.metadata_path.parent / full_path

            if full_path.exists():
                self.samples.append({
                    'path': str(full_path),
                    'label': label
                })

        # Anti-Overfitting Data Pipeline
        # We apply strong regularizations specifically designed to prevent the neural network 
        # from "cheating" by memorizing studio lighting, compression artifacts, or specific
        # orientations of the training data.
        if is_train:
            self.transform = transforms.Compose([
                # Randomly flipping the image horizontally forces the model to learn 
                # structural authenticity rather than asymmetric dataset biases.
                transforms.RandomHorizontalFlip(p=0.5),
                
                # Minor rotations prevent the network from memorizing exact pixel layouts
                # around the eyes and mouth.
                transforms.RandomRotation(degrees=10),
                
                # ColorJitter adds pixel noise to the brightness, contrast, and saturation. 
                # This breaks exact color memorization and prevents the model from relying
                # on lighting or simple RGB statistical differences between fake/real datasets.
                transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.1, hue=0.05)
            ])
        else:
            self.transform = None

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        sample = self.samples[idx]
        face_array = np.load(sample['path'], allow_pickle=False)

        # Convert the raw array into a standard FloatTensor [0-1 range typically assumed depending on preprocessing]
        # The preprocessing pipeline extracts face_array and we assume it's valid Float32 (H, W, C)
        if face_array.dtype != np.float32:
            face_array = face_array.astype(np.float32)
            
        # If the array was saved without dividing by 255
        if face_array.max() > 1.5:
            face_array = face_array / 255.0

        # Permute HWC to CHW for PyTorch
        image_tensor = torch.from_numpy(face_array).permute(2, 0, 1)

        if self.transform is not None:
            image_tensor = self.transform(image_tensor)

        # Target label as float32 for BCEWithLogitsLoss
        label_tensor = torch.tensor([sample['label']], dtype=torch.float32)

        return image_tensor, label_tensor
