import threading
import logging
from typing import Optional, Callable
from .train import run_training_engine

logger = logging.getLogger(__name__)


def start_training_job(
    metadata_path: str,
    epochs: int = 10,
    batch_size: int = 32,
    on_complete: Optional[Callable[[str], None]] = None,
    on_error: Optional[Callable[[Exception], None]] = None
):
    """
    Background Thread Invocation Hook for Deepfake Detection Training.
    
    This function wraps the rigorous PyTorch training engine in a native Python thread.
    By using Python's built-in threading, we achieve asynchronous execution without 
    blocking the active Django web threads. 
    
    This design choice elegantly satisfies our requirement to keep infrastructure 
    simple (avoiding Celery/Redis/Docker overhead) while maintaining high performance.
    
    Args:
        metadata_path: Path to the metadata.json for the deepfake dataset.
        epochs: Number of training epochs.
        batch_size: Batch size for DataLoader.
        on_complete: Optional callback function to run when training succeeds, passing the best model path.
        on_error: Optional callback function to run if training fails.
    """
    
    def _train_worker():
        try:
            logger.info(f"Starting background training thread for metadata: {metadata_path}")
            best_model_path = run_training_engine(
                metadata_path=metadata_path,
                epochs=epochs,
                batch_size=batch_size
            )
            logger.info(f"Background training thread completed. Best model: {best_model_path}")
            if on_complete:
                on_complete(str(best_model_path))
        except Exception as e:
            logger.error(f"Background training thread failed with error: {e}", exc_info=True)
            if on_error:
                on_error(e)

    # Instantiate and start the native Python thread.
    # We set daemon=True so the thread won't block the Django server from shutting down if needed.
    train_thread = threading.Thread(target=_train_worker, daemon=True)
    train_thread.start()
    
    logger.info("Training job successfully dispatched to background thread.")
    
    # Return immediately, allowing the Django view to respond to the frontend HTTP request
    # while the thread crunches the PyTorch tensors asynchronously.
    return train_thread
