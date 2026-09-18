# Deepfake Detection System

A starter project for classifying manipulated and authentic images/videos for forensic use.
## Model weights and Git LFS

Large model weight files (e.g. `*.pth`) are tracked using Git LFS to keep the repository lightweight. After cloning the repository, install Git LFS and pull LFS objects:

```powershell
git lfs install
git lfs pull
```

If you push new large weight files, add them to LFS first:

```powershell
git lfs track "*.pth"
git add .gitattributes
git add path/to/weights.pth
git commit -m "Add model weights to LFS"
git push
```

If you need history rewritten to migrate existing large files into LFS, the repository maintainer can run `git lfs migrate import --include="*.pth"` and force-push the cleaned history.
# Deepfake Detection System

A starter project for classifying manipulated and authentic images/videos for forensic use.

## What is included

- Image dataset loader for `real` / `fake` folder structures
- Transfer-learning baseline using a pretrained ResNet-18
- Training script with validation metrics and model checkpoints
- Inference for images and video files
- Frame extraction utility for video-based datasets
- Face preprocessing pipeline with video frame sampling, face detection, cropping, and normalization

## Suggested dataset layout

```text
data/
  train/
    real/
    fake/
  val/
    real/
    fake/
  test/
    real/
    fake/
```

If you start with videos, extract frames into the same folder structure.

## Quick start

1. Create a Python environment and install dependencies:

```bash
pip install -r requirements.txt
```

For the training pipeline specifically, you need PyTorch and torchvision available. If they are not already installed by your environment, add them with:

```bash
pip install torch torchvision
```

Optional, if you want the stronger MediaPipe detector instead of the OpenCV fallback:

```bash
pip install mediapipe
```

If MediaPipe is not available on your machine, the preprocessing code will still run using OpenCV Haar cascades.

2. Train the baseline model:

```bash
python -m src.deepfake_detection.train --data-dir data --epochs 5 --batch-size 16
```

3. Run inference on an image or video:

```bash
python -m src.deepfake_detection.infer --checkpoint models/best_model.pt --input sample.jpg
python -m src.deepfake_detection.infer --checkpoint models/best_model.pt --input sample.mp4
```

3. Run the preprocessing pipeline directly:

```bash
python -m scripts.preprocess_media --input sample.mp4 --target-fps 5
python -m scripts.preprocess_media --input sample.jpg
```

By default this writes `.npy` face crops and a `metadata.json` file into a temporary folder and prints the folder path.

4. Train the classifier on the preprocessed crops:

```bash
python -m src.deepfake_detection.train --metadata-path path/to/metadata_dir --backbone efficientnet_b0 --epochs 10
```

The script saves the best checkpoint as `models/best_deepfake_model.pth` by validation loss.

## FastAPI Backend

Run the API server:

```bash
uvicorn main:app --reload
```

Open the Swagger UI at:

```text
http://127.0.0.1:8000/docs
```

Test flow in Swagger UI or Postman:

1. Call `POST /upload` with a multipart form file field named `file`.
2. Copy the returned job ID, for example `#JOB_7734`.
3. Call `GET /status/{job_id}` or `GET /results/{job_id}` to check progress and fetch the metadata once the job is complete.

Notes:

- The backend uses FastAPI `BackgroundTasks`, which is ideal for a local demo or a single-process proof of concept.
- For production-grade scaling, you would move the queue to Celery + Redis so jobs survive server restarts and can run across multiple workers.

## ML Inference And Reporting

Run the inference module from the repository root, not from `frontend/`, so Python can import the `backend` package correctly:

```powershell
cd "D:\deepfake detection"
.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m backend.app.ml.inference --input path\to\face.jpg --weights backend\app\weights\best_deepfake_model.pth --output-dir backend\app\forensic_outputs --job-id JOB_7734
```

If you are already inside `frontend/`, either go back to the repo root first or run the command with the repo root on the Python path:

```powershell
$env:PYTHONPATH = ".."
& "..\.venv\Scripts\python.exe" -m backend.app.ml.inference --input path\to\face.jpg --weights ..\backend\app\weights\best_deepfake_model.pth --output-dir ..\backend\app\forensic_outputs --job-id JOB_7734
```

## Local Test Guide

1. Put one sample video or image somewhere on your machine, for example `sample.mp4` in the project root.
2. Run the preprocessing command above.
3. Open the printed output directory and check:
  - `face_000000.npy`, `face_000001.npy`, etc.
  - `metadata.json` with bounding boxes, timestamps, and confidence values
4. If you want to inspect a crop quickly in Python, load one file with `numpy.load(path)` and verify it has shape `(224, 224, 3)`.

## Project milestones

- Done: project scaffold, baseline model, training loop, inference tools, preprocessing pipeline
- Next: face-crop quality checks, stronger backbones, better video aggregation, experiment tracking
- Later: dataset curation, evaluation report, presentation slides, police-oriented case-study writeup
