import os
import sys
import time
import requests
from pathlib import Path

def main():
    print("Starting NexaShield Django API v1 Validation...")
    
    # 1. Find a downloaded video
    video_dir = Path("data/original_sequences/youtube/c23/videos")
    if not video_dir.exists():
        print(f"Error: Video directory {video_dir} does not exist.")
        sys.exit(1)
        
    videos = list(video_dir.glob("*.mp4"))
    if not videos:
        print(f"Error: No videos found in {video_dir}.")
        sys.exit(1)
        
    test_video = videos[0]
    print(f"Using test video: {test_video}")
    
    # 2. Start Django server check
    django_url = "http://127.0.0.1:8000"
    
    # 3. Submit analysis request
    print("\n--- 1. Ingesting Media via POST /api/v1/analyze ---")
    with open(test_video, "rb") as f:
        response = requests.post(
            f"{django_url}/api/v1/analyze",
            files={"file": (test_video.name, f, "video/mp4")}
        )
        
    print(f"Ingestion HTTP Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
        sys.exit(1)
        
    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"Created Django Forensic Job ID: {job_id}")
    
    # 4. Poll status endpoint
    print("\n--- 2. Polling status via GET /api/v1/status/{jobId} ---")
    max_retries = 40
    completed = False
    
    for retry in range(max_retries):
        status_resp = requests.get(f"{django_url}/api/v1/status/{job_id}")
        if status_resp.status_code != 200:
            print(f"Error: status code {status_resp.status_code}, response: {status_resp.text}")
            sys.exit(1)
            
        status_data = status_resp.json()
        status = status_data["status"]
        progress = status_data["progress"]
        message = status_data.get("message", "")
        
        print(f"  [Poll #{retry+1}] Status: {status} | Progress: {progress}% | Message: {message}")
        
        if status == "COMPLETED":
            completed = True
            break
        elif status == "FAILED":
            print(f"Error: Job failed with detail: {status_data.get('error')}")
            sys.exit(1)
            
        time.sleep(1.5)
        
    if not completed:
        print("Error: Forensic job did not complete within timeout.")
        sys.exit(1)
        
    print("\n--- 3. Verifying Completed Job Artifacts ---")
    
    # Fetch job status one last time to inspect final fields
    final_resp = requests.get(f"{django_url}/api/v1/status/{job_id}")
    final_data = final_resp.json()
    
    if "analysis_report" not in final_data:
        print("Error: analysis_report not in final status response.")
        sys.exit(1)
        
    report = final_data["analysis_report"]
    print(f"  Total frames analyzed: {report['total_frames']}")
    print(f"  Timeline frames found: {len(report['timeline_frames'])}")
    
    if len(report['timeline_frames']) == 0:
        print("Error: timeline_frames is empty.")
        sys.exit(1)
        
    # Verify the first frame URLs and that they return HTTP 200
    first_frame = report['timeline_frames'][0]
    face_url = first_frame['face_crop_url']
    grad_url = first_frame['grad_cam_url']
    
    print(f"  Checking face crop URL: {face_url}")
    face_resp = requests.get(f"{django_url}{face_url}")
    print(f"  Face Crop HTTP Status: {face_resp.status_code}")
    assert face_resp.status_code == 200
    
    print(f"  Checking Grad-CAM URL: {grad_url}")
    grad_resp = requests.get(f"{django_url}{grad_url}")
    print(f"  Grad-CAM HTTP Status: {grad_resp.status_code}")
    assert grad_resp.status_code == 200
    
    # 5. Fetch PDF Report stream
    print("\n--- 4. Exporting PDF Report via GET /api/v1/reports/{jobId}/pdf ---")
    pdf_resp = requests.get(f"{django_url}/api/v1/reports/{job_id}/pdf")
    print(f"  PDF HTTP Status: {pdf_resp.status_code}")
    assert pdf_resp.status_code == 200
    assert len(pdf_resp.content) > 0, "PDF content is empty."
    
    print("\nDjango API v1 validation completed successfully and is 100% stable!")

if __name__ == "__main__":
    main()
