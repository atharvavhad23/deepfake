import logging
import math
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from .dataset import DeepfakeDataset
from .model import build_forensics_model

logger = logging.getLogger(__name__)


def calculate_accuracy(logits: torch.Tensor, labels: torch.Tensor) -> float:
    # Sigmoid to get probability, threshold at 0.5
    predictions = (torch.sigmoid(logits) >= 0.5).float()
    correct = (predictions == labels).sum().item()
    return correct / max(labels.numel(), 1)


def run_training_engine(
    metadata_path: str,
    epochs: int = 10,
    batch_size: int = 32,
    learning_rate: float = 1e-4,
    device_str: str = "cuda" if torch.cuda.is_available() else "cpu",
    output_weights_dir: str = "weights"
):
    """
    Rigorous Training Engine for Deepfake Detection
    """
    device = torch.device(device_str)
    
    # Initialize Dataset and DataLoader
    train_dataset = DeepfakeDataset(metadata_path, is_train=True)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    
    # We ideally need a validation set for tracking exactly when to checkpoint. 
    # For this simplified prototype pipeline, we'll evaluate on the training set to demonstrate the guard,
    # or you can split the dataset here. (Using train loader for simplicity as placeholder for validation).
    val_loader = DataLoader(DeepfakeDataset(metadata_path, is_train=False), batch_size=batch_size, shuffle=False)

    # Initialize Model, Loss, and Optimizer
    model = build_forensics_model().to(device)
    
    # BCEWithLogitsLoss is numerically more stable than Sigmoid + BCELoss
    criterion = nn.BCEWithLogitsLoss()
    
    # Only optimize parameters that have requires_grad=True (our unfreezed layers)
    optimizer = torch.optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()), 
        lr=learning_rate
    )
    
    weights_path = Path(__file__).parent / output_weights_dir
    weights_path.mkdir(parents=True, exist_ok=True)
    best_model_path = weights_path / "best_model.pth"
    
    best_val_accuracy = -1.0
    
    print(f"Starting training loop ({epochs} epochs) on {device}...")
    
    for epoch in range(1, epochs + 1):
        # ---------------------
        # TRAINING PHASE
        # ---------------------
        model.train()
        train_loss_total = 0.0
        train_acc_total = 0.0
        
        # tqdm for console tracking
        progress = tqdm(train_loader, desc=f"Epoch {epoch}/{epochs} [Train]")
        
        for images, labels in progress:
            images = images.to(device)
            labels = labels.to(device)
            
            # Explicit 5-step PyTorch training layout
            
            # 1. Forward Pass: Compute model output (logits) for the batch
            logits = model(images)
            
            # 2. Loss Calculation: Calculate the discrepancy between logits and true labels
            loss = criterion(logits, labels)
            
            # 3. Zero Grad: Clear out previous iteration's gradients before backward pass
            optimizer.zero_grad()
            
            # 4. Backward Pass: Compute gradients using backpropagation
            loss.backward()
            
            # 5. Optimizer Step: Update the model weights based on computed gradients
            optimizer.step()
            
            # Track dynamic metrics
            train_loss_total += loss.item()
            train_acc_total += calculate_accuracy(logits.detach(), labels.detach())
            
            progress.set_postfix({"loss": f"{loss.item():.4f}"})
            
        avg_train_loss = train_loss_total / len(train_loader)
        avg_train_acc = train_acc_total / len(train_loader)
        
        # ---------------------
        # VALIDATION PHASE
        # ---------------------
        model.eval()
        val_loss_total = 0.0
        val_acc_total = 0.0
        
        with torch.no_grad():
            for images, labels in tqdm(val_loader, desc=f"Epoch {epoch}/{epochs} [Val]"):
                images = images.to(device)
                labels = labels.to(device)
                logits = model(images)
                loss = criterion(logits, labels)
                
                val_loss_total += loss.item()
                val_acc_total += calculate_accuracy(logits, labels)
                
        avg_val_loss = val_loss_total / len(val_loader)
        avg_val_acc = val_acc_total / len(val_loader)
        
        print(f"Epoch {epoch} Results:")
        print(f"  Train Loss: {avg_train_loss:.4f} | Train Acc: {avg_train_acc:.4f}")
        print(f"  Val Loss:   {avg_val_loss:.4f} | Val Acc:   {avg_val_acc:.4f}")
        
        # Automated Checkpoint Guard
        # Saves the absolute best iteration weights
        if avg_val_acc > best_val_accuracy:
            best_val_accuracy = avg_val_acc
            print(f"  --> New best validation accuracy! Saving to {best_model_path}")
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'val_accuracy': best_val_accuracy,
                'val_loss': avg_val_loss,
            }, best_model_path)
            
    print("Training complete!")
    return best_model_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata-path", type=str, required=True, help="Path to metadata.json")
    parser.add_argument("--epochs", type=int, default=10)
    args = parser.parse_args()
    
    run_training_engine(metadata_path=args.metadata_path, epochs=args.epochs)
