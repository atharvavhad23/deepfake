import os
import sys
from pathlib import Path
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from torch.optim import Adam

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.dataset import DualStreamDataset
from src.model import NexaShieldModel

def train_model(epochs: int = 15, batch_size: int = 16, lr: float = 1e-4):
    print("==================================================")
    print("NexaShield Dual-Stream Classifier Training Pipeline")
    print("==================================================")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device selected: {device}")
    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        
    # 1. Load Dataset
    data_dir = "data/processed/train"
    print(f"Loading datasets from {data_dir}...")
    dataset = DualStreamDataset(root_dir=data_dir, is_train=True)
    
    if len(dataset) == 0:
        print("Error: Dataset is empty. Please run preprocessing first.")
        return
        
    # Split into train/validation (80/20 split)
    val_size = int(len(dataset) * 0.20)
    train_size = len(dataset) - val_size
    train_set, val_set = random_split(dataset, [train_size, val_size])
    
    # Configure transform states (validation shouldn't use random flips/color jitter)
    val_set.dataset.is_train = False
    
    print(f"Dataset split: {train_size} training samples, {val_size} validation samples")
    
    # Create DataLoaders
    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True, drop_last=True)
    val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=False, drop_last=False)
    
    # 2. Instantiate Model
    print("Initializing NexaShieldModel (EfficientNet-B4 + DCT CNN Stream)...")
    model = NexaShieldModel(pretrained=True).to(device)
    
    # Freeze spatial stream backbone features to speed up CPU training
    print("Freezing Spatial Stream backbone features for accelerated training...")
    for param in model.spatial_stream.backbone.features.parameters():
        param.requires_grad = False
        
    # Loss & Optimizer (optimize only unfrozen parameters)
    criterion = nn.CrossEntropyLoss()
    optimizer = Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=lr)

    
    best_val_acc = 0.0
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    save_path = models_dir / "nexashield_classifier.pth"
    
    if save_path.exists():
        print(f"Found existing checkpoint at {save_path}. Loading weights for fine-tuning...")
        model.load_state_dict(torch.load(save_path))
        # Reduce learning rate for fine-tuning
        for param_group in optimizer.param_groups:
            param_group['lr'] = lr * 0.1
        print(f"Reduced learning rate to {lr * 0.1} for fine-tuning.")
    
    print("\nStarting Training Loop...")
    for epoch in range(1, epochs + 1):
        # --- Training Epoch ---
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        for spatial_x, spectral_x, y in train_loader:
            spatial_x = spatial_x.to(device)
            spectral_x = spectral_x.to(device)
            y = y.to(device)
            
            optimizer.zero_grad()
            
            # Forward pass
            logits = model(spatial_x, spectral_x)
            loss = criterion(logits, y)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * spatial_x.size(0)
            preds = torch.argmax(logits, dim=1)
            train_correct += torch.sum(preds == y).item()
            train_total += y.size(0)
            
        epoch_train_loss = train_loss / train_total
        epoch_train_acc = (train_correct / train_total) * 100
        
        # --- Validation Epoch ---
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for spatial_x, spectral_x, y in val_loader:
                spatial_x = spatial_x.to(device)
                spectral_x = spectral_x.to(device)
                y = y.to(device)
                
                logits = model(spatial_x, spectral_x)
                loss = criterion(logits, y)
                
                val_loss += loss.item() * spatial_x.size(0)
                preds = torch.argmax(logits, dim=1)
                val_correct += torch.sum(preds == y).item()
                val_total += y.size(0)
                
        epoch_val_loss = val_loss / val_total
        epoch_val_acc = (val_correct / val_total) * 100
        
        print(f"Epoch {epoch:02d}/{epochs:02d} | "
              f"Train Loss: {epoch_train_loss:.4f} | Train Acc: {epoch_train_acc:.2f}% | "
              f"Val Loss: {epoch_val_loss:.4f} | Val Acc: {epoch_val_acc:.2f}%")
              
        # Save best model
        if epoch_val_acc > best_val_acc:
            best_val_acc = epoch_val_acc
            torch.save(model.state_dict(), save_path)
            print(f"  --> Saved new best model with Validation Accuracy: {best_val_acc:.2f}%")
            
    print("\nTraining completed successfully!")
    print(f"Best Validation Accuracy: {best_val_acc:.2f}%")
    print(f"Model saved to: {save_path.resolve()}")
    print("==================================================")

if __name__ == "__main__":
    train_model(epochs=3, batch_size=8, lr=1e-4)
