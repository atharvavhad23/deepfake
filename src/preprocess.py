import os
import cv2
import numpy as np
import urllib.request
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

def compute_dct_matrix(img_rgb: np.ndarray, target_size: int = 256) -> np.ndarray:
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
    try:
        if hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
            p = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
            if p.exists():
                return p
    except Exception:
        pass
        
    local_path = Path("models/haarcascade_frontalface_default.xml")
    if local_path.exists():
        return local_path
        
    local_path.parent.mkdir(parents=True, exist_ok=True)
    url = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
    print(f"Haar cascade XML not found. Downloading from {url}...")
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
        cascade_path = get_cascade_path()
        if cascade_path is not None:
            self.face_cascade = cv2.CascadeClassifier(str(cascade_path))
        else:
            self.face_cascade = None

    def detect_face(self, frame_bgr: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        if self.face_cascade is None or self.face_cascade.empty():
            return None
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
        if len(faces) == 0:
            return None
        # Select the largest face by area
        largest_face = max(faces, key=lambda box: box[2] * box[3])
        return tuple(largest_face)

    def extract_crop_and_dct(self, frame_bgr: np.ndarray, target_size: int = 256) -> Optional[Tuple[np.ndarray, np.ndarray]]:
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
        spatial_crop = cv2.resize(face_rgb, (target_size, target_size), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        
        # Compute DCT matrix
        spectral_dct = compute_dct_matrix(spatial_crop, target_size=target_size)
        
        return spatial_crop, spectral_dct

def process_video_file(video_path: Path, output_spatial_dir: Path, output_spectral_dir: Path, num_frames: int = 5):
    """
    Extracts frames from a video file, detects faces, resizes them,
    calculates frequency signatures, and saves them to the output directories.
    """
    output_spatial_dir.mkdir(parents=True, exist_ok=True)
    output_spectral_dir.mkdir(parents=True, exist_ok=True)
    
    extractor = FaceExtractor()
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"Error: Unable to open video {video_path}")
        return
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        total_frames = 100 # fallback estimate
        
    # Process N evenly spaced frames across the video
    frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
    
    video_stem = video_path.stem
    
    for i, idx in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        success, frame = cap.read()
        if not success:
            # try sequential read if random seek failed
            continue
            
        processed = extractor.extract_crop_and_dct(frame, target_size=256)
        if processed is not None:
            spatial_crop, spectral_dct = processed
            
            spatial_name = f"{video_stem}_frame_{idx}_spatial.npy"
            spectral_name = f"{video_stem}_frame_{idx}_spectral.npy"
            
            np.save(output_spatial_dir / spatial_name, spatial_crop)
            np.save(output_spectral_dir / spectral_name, spectral_dct)
            
    cap.release()

def process_image_file(image_path: Path, output_spatial_dir: Path, output_spectral_dir: Path):
    """
    Detects face, resizes, calculates frequency signatures, and saves them.
    """
    output_spatial_dir.mkdir(parents=True, exist_ok=True)
    output_spectral_dir.mkdir(parents=True, exist_ok=True)
    
    extractor = FaceExtractor()
    frame = cv2.imread(str(image_path))
    if frame is None:
        return
        
    processed = extractor.extract_crop_and_dct(frame, target_size=256)
    if processed is not None:
        spatial_crop, spectral_dct = processed
        img_stem = image_path.stem
        
        spatial_name = f"{img_stem}_spatial.npy"
        spectral_name = f"{img_stem}_spectral.npy"
        
        np.save(output_spatial_dir / spatial_name, spatial_crop)
        np.save(output_spectral_dir / spectral_name, spectral_dct)

def main():
    print("Initializing Forensic Preprocessing Pipeline...")
    
    # Paths mapping
    data_dir = Path("data")
    processed_dir = data_dir / "processed" / "train"
    
    # Real Sequences
    real_video_dir = data_dir / "original_sequences" / "youtube" / "c23" / "videos"
    real_spatial_out = processed_dir / "real" / "spatial"
    real_spectral_out = processed_dir / "real" / "spectral"
    
    if real_video_dir.exists():
        real_videos = list(real_video_dir.glob("*.mp4"))
        print(f"Found {len(real_videos)} real videos.")
        for vid in real_videos[:3]: # process first 3 videos for immediate testing
            print(f"Processing real video: {vid.name}")
            process_video_file(vid, real_spatial_out, real_spectral_out, num_frames=5)
    else:
        print("Real videos directory not found.")
        
    # Fake Sequences (scan all manipulated directories)
    manip_dir = data_dir / "manipulated_sequences"
    fake_spatial_out = processed_dir / "fake" / "spatial"
    fake_spectral_out = processed_dir / "fake" / "spectral"
    
    if manip_dir.exists():
        fake_videos = list(manip_dir.glob("**/*.mp4"))
        print(f"Found {len(fake_videos)} fake videos across manipulated sequences.")
        for vid in fake_videos[:3]: # process first 3 videos for immediate testing
            print(f"Processing fake video: {vid.name}")
            process_video_file(vid, fake_spatial_out, fake_spectral_out, num_frames=5)
    else:
        print("Manipulated sequences directory not found.")
        
    # Process GenAI Still Images
    genai_real_dir = data_dir / "raw" / "real"
    genai_fake_dir = data_dir / "raw" / "fake"
    
    if genai_real_dir.exists():
        genai_reals = list(genai_real_dir.glob("*.jpg"))
        print(f"Found {len(genai_reals)} GenAI real images.")
        for img_path in genai_reals:
            process_image_file(img_path, real_spatial_out, real_spectral_out)
            
    if genai_fake_dir.exists():
        genai_fakes = list(genai_fake_dir.glob("*.jpg"))
        print(f"Found {len(genai_fakes)} GenAI fake images.")
        for img_path in genai_fakes:
            process_image_file(img_path, fake_spatial_out, fake_spectral_out)
            
    print("Preprocessing completed!")

if __name__ == "__main__":
    main()
