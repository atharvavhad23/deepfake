import os
import cv2
import json
import numpy as np
import urllib.request
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

def compute_dct_matrix(img_rgb: np.ndarray, target_size: int = 128) -> np.ndarray:
    """
    Computes the log-scaled 2D Discrete Cosine Transform (DCT) matrix of a face crop.
    
    Args:
        img_rgb: RGB face crop, values in [0, 1] float32.
        target_size: Resolution of the output DCT matrix.
        
    Returns:
        A 2D float32 array of shape (target_size, target_size) representing the log-scaled DCT coefficients.
    """
    # Convert RGB float32 crop [0, 1] to grayscale float32
    gray = cv2.cvtColor((img_rgb * 255.0).astype(np.uint8), cv2.COLOR_RGB2GRAY)
    
    # Resize grayscale to target size before DCT
    gray_resized = cv2.resize(gray, (target_size, target_size), interpolation=cv2.INTER_AREA)
    gray_f32 = gray_resized.astype(np.float32) / 255.0
    
    # Compute 2D DCT
    dct = cv2.dct(gray_f32)
    
    # Log scaling to highlight anomalies in frequencies
    dct_log = np.log(1.0 + np.abs(dct))
    
    # Normalize to [0, 1]
    denom = dct_log.max() - dct_log.min()
    if denom > 1e-8:
        dct_norm = (dct_log - dct_log.min()) / denom
    else:
        dct_norm = dct_log
        
    return dct_norm

def get_cascade_path() -> Optional[Path]:
    # 1. Try OpenCV location
    try:
        if hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
            p = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
            if p.exists():
                return p
    except Exception:
        pass
        
    # 2. Check local path
    local_path = Path("models/haarcascade_frontalface_default.xml")
    if local_path.exists():
        return local_path
        
    # 3. Download if missing
    local_path.parent.mkdir(parents=True, exist_ok=True)
    url = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
    print(f"Haar cascade XML not found locally. Downloading from {url}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            with open(local_path, "wb") as f:
                f.write(response.read())
        print(f"Successfully downloaded Haar cascade to {local_path}")
        return local_path
    except Exception as e:
        print(f"Warning: Failed to download Haar cascade ({e}). Face detection will fall back to center crop.")
        return None

class FaceExtractor:
    def __init__(self):
        # Initialize Haar cascade classifier for face detection
        cascade_path = get_cascade_path()
        if cascade_path is not None:
            self.face_cascade = cv2.CascadeClassifier(str(cascade_path))
        else:
            self.face_cascade = None

    def detect_face(self, frame_bgr: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Detects the primary face in a frame. Returns bounding box (x, y, w, h).
        """
        if self.face_cascade is None or self.face_cascade.empty():
            return None
            
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
        if len(faces) == 0:
            return None
        # Select the largest face by area
        largest_face = max(faces, key=lambda box: box[2] * box[3])
        return tuple(largest_face)

    def extract_crop_and_dct(self, frame_bgr: np.ndarray, spatial_size: int = 224, spectral_size: int = 128) -> Optional[Tuple[np.ndarray, np.ndarray, Tuple[int, int, int, int]]]:
        """
        Detects face, extracts crops, and computes spatial and spectral matrices.
        
        Returns:
            Tuple of:
            - spatial_crop: RGB normalized float32 image of shape (spatial_size, spatial_size, 3)
            - spectral_dct: DCT matrix of shape (spectral_size, spectral_size)
            - bbox: Bounding box (x, y, w, h)
        """
        bbox = self.detect_face(frame_bgr)
        if bbox is None:
            # Fallback: Center crop if no face detected
            h, w = frame_bgr.shape[:2]
            side = min(h, w)
            x, y = (w - side) // 2, (h - side) // 2
            bbox = (x, y, side, side)
            
        x, y, w_box, h_box = bbox
        
        # Apply padding / margin to crop (15%)
        margin_x = int(w_box * 0.15)
        margin_y = int(h_box * 0.15)
        h, w = frame_bgr.shape[:2]
        
        x1 = max(0, x - margin_x)
        y1 = max(0, y - margin_y)
        x2 = min(w, x + w_box + margin_x)
        y2 = min(h, y + h_box + margin_y)
        
        face_crop = frame_bgr[y1:y2, x1:x2]
        if face_crop.size == 0:
            return None
            
        # Convert to RGB and scale to [0, 1]
        face_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
        spatial_crop = cv2.resize(face_rgb, (spatial_size, spatial_size), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        
        # Compute DCT
        spectral_dct = compute_dct_matrix(spatial_crop, target_size=spectral_size)
        
        return spatial_crop, spectral_dct, (x1, y1, x2 - x1, y2 - y1)

def process_video(
    video_path: Path, 
    target_fps: float = 2.0, 
    spatial_size: int = 224, 
    spectral_size: int = 128
) -> List[Dict[str, Any]]:
    """
    Extracts frames from a video, processes faces, and computes DCT matrices.
    """
    extractor = FaceExtractor()
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Unable to open video: {video_path}")
        
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_interval = max(int(round(src_fps / target_fps)), 1)
    
    results = []
    frame_idx = 0
    
    while True:
        success, frame = cap.read()
        if not success:
            break
            
        if frame_idx % frame_interval == 0:
            timestamp_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
            processed = extractor.extract_crop_and_dct(frame, spatial_size, spectral_size)
            if processed is not None:
                spatial_crop, spectral_dct, bbox = processed
                results.append({
                    "frame_index": frame_idx,
                    "timestamp_ms": timestamp_ms,
                    "spatial": spatial_crop,
                    "spectral": spectral_dct,
                    "bbox": bbox
                })
        frame_idx += 1
        
    cap.release()
    return results
