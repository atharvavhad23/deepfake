import os
import cv2
import torch
import base64
import hashlib
import tempfile
import numpy as np
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Project imports
from src.preprocess import FaceExtractor
from src.model import NexaShieldModel
from src.explainability import GradCAM, overlay_heatmap
from src.reporter import ForensicReportGenerator

# Initialize FastAPI application
app = FastAPI(
    title="NexaShield Deepfake Detection Gateway",
    description="Production-grade API featuring chain-of-custody cryptographic logging and Explainable AI (Grad-CAM).",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load device and NexaShield model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = NexaShieldModel(pretrained=True).to(device)

# Load trained custom classifier weights if available
model_path = Path("models/nexashield_classifier.pth")
if model_path.exists():
    try:
        model.load_state_dict(torch.load(model_path, map_location=device))
        print(f"Loaded custom trained weights from {model_path}")
    except Exception as e:
        print(f"Warning: Failed to load custom weights from {model_path} ({e})")

model.eval()


# Select the target convolution block for Grad-CAM
target_layer = model.spatial_stream.backbone.features[-1]
grad_cam_generator = GradCAM(model, target_layer)

class EvidenceAnalysisResponse(BaseModel):
    file_name: str
    sha256_hash: str
    authenticity_score: float
    classification: str
    tamper_heatmap_base64: str

@app.post("/api/v1/analyze-evidence", response_model=EvidenceAnalysisResponse)
async def analyze_evidence(file: UploadFile = File(...)):
    """
    Ingests video evidence, computes SHA-256, isolates the primary face crop,
    runs dual-stream inference, generates Grad-CAM overlays, and returns results.
    """
    if not file.filename.lower().endswith('.mp4'):
        raise HTTPException(status_code=400, detail="Only MP4 video evidence files are supported.")
        
    try:
        # Read video bytes and calculate SHA-256 immediately (strict chain-of-custody protocol)
        file_bytes = await file.read()
        sha256_hash = hashlib.sha256(file_bytes).hexdigest()
        
        # Save video to a secure temporary file path for frame parsing
        temp_dir = Path(tempfile.gettempdir())
        temp_video_path = temp_dir / f"custody_{sha256_hash}.mp4"
        
        with open(temp_video_path, "wb") as f:
            f.write(file_bytes)
            
        # Ingestion and preprocessing (capture representative face frame)
        cap = cv2.VideoCapture(str(temp_video_path))
        if not cap.isOpened():
            raise ValueError("Unable to read video file.")
            
        extractor = FaceExtractor()
        processed_data = None
        
        # Scan first few frames to find a valid face
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_sample_step = max(1, total_frames // 10)
        
        for frame_idx in range(0, total_frames, frame_sample_step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            success, frame = cap.read()
            if not success:
                break
                
            res = extractor.extract_crop_and_dct(frame, target_size=256)
            if res is not None:
                # Found face, store crop + DCT matrices
                processed_data = res
                break
                
        # If no face is detected in sample frames, fall back to center crop of the middle frame
        if processed_data is None:
            cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
            success, frame = cap.read()
            if success:
                # Force center crop fallback
                processed_data = extractor.extract_crop_and_dct(frame, target_size=256)
                
        cap.release()
        
        # Clean up temporary video file immediately
        if temp_video_path.exists():
            os.remove(temp_video_path)
            
        if processed_data is None:
            raise ValueError("Video contains no valid visual frames for analysis.")
            
        spatial_crop, spectral_dct = processed_data
        
        # Prepare inputs for the model
        spatial_tensor = torch.from_numpy(spatial_crop).permute(2, 0, 1).unsqueeze(0).to(device)
        spectral_tensor = torch.from_numpy(spectral_dct).unsqueeze(0).unsqueeze(0).to(device)
        
        # Dual-Stream Inference
        with torch.no_grad():
            logits = model(spatial_tensor, spectral_tensor)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
            
        prob_real = float(probs[0])
        prob_fake = float(probs[1])
        
        # Generate Grad-CAM activation map
        spatial_tensor_grad = spatial_tensor.clone().detach().requires_grad_(True)
        heatmap = grad_cam_generator.generate_heatmap(spatial_tensor_grad, spectral_tensor, class_idx=1)
        
        # Create overlay visualization crop
        overlay_rgb = overlay_heatmap(spatial_crop, heatmap, alpha=0.6)
        
        # Encode overlay to PNG Base64 string
        overlay_bgr = cv2.cvtColor(overlay_rgb, cv2.COLOR_RGB2BGR)
        success, buffer = cv2.imencode('.png', overlay_bgr)
        if not success:
            raise ValueError("Failed to encode overlay image.")
            
        base64_str = base64.b64encode(buffer).decode('utf-8')
        
        # Determine classification
        classification = "REAL" if prob_real >= prob_fake else "FAKE"
        
        # Save heatmap overlay to a temporary file path to compile PDF report
        temp_heatmap_path = temp_dir / f"heatmap_{sha256_hash}.png"
        cv2.imwrite(str(temp_heatmap_path), overlay_bgr)
        
        # Generate the court-admissible PDF certificate
        reporter = ForensicReportGenerator(output_dir="data/reports")
        file_size_kb = len(file_bytes) / 1024.0
        reporter.generate_report(
            file_name=file.filename,
            file_size_kb=file_size_kb,
            sha256_hash=sha256_hash,
            authenticity_score=prob_real,
            classification=classification,
            heatmap_image_path=str(temp_heatmap_path)
        )
        
        # Clean up temporary heatmap image
        if temp_heatmap_path.exists():
            os.remove(temp_heatmap_path)
            
        return EvidenceAnalysisResponse(
            file_name=file.filename,
            sha256_hash=sha256_hash,
            authenticity_score=prob_real,
            classification=classification,
            tamper_heatmap_base64=base64_str
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Forensic processing failed: {str(e)}")

@app.get("/api/v1/download-report/{sha256_hash}")
async def download_report(sha256_hash: str):
    """
    Downloads the pre-compiled tamper-evident PDF forensic verification report
    for a given video cryptographic signature.
    """
    report_path = Path("data/reports") / f"forensic_report_{sha256_hash[:16]}.pdf"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Forensic verification certificate not found.")
    
    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename=f"NexaShield_Report_{sha256_hash[:16]}.pdf"
    )
