import os
import hashlib
import tempfile
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from pathlib import Path

from .models import MediaAnalysisJob
from .utils import dispatch_video_job, REPORTS_DIR

@csrf_exempt
@api_view(['POST'])
def analyze_media(request):
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded'}, status=400)
        
    uploaded_file = request.FILES['file']
    
    # Save incoming file to a temporary location
    fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(uploaded_file.name)[1])
    sha256 = hashlib.sha256()
    
    with os.fdopen(fd, 'wb') as dest:
        for chunk in uploaded_file.chunks():
            dest.write(chunk)
            sha256.update(chunk)
            
    file_hash = sha256.hexdigest()
    
    # Create the database record
    job = MediaAnalysisJob.objects.create(
        status=MediaAnalysisJob.StatusChoices.QUEUED,
        file_hash=file_hash,
        progress=0,
        message="Enqueuing video for forensics validation..."
    )
    
    # Dispatch Native Background Thread
    dispatch_video_job(str(job.job_id), temp_path, file_hash, uploaded_file.name)
    
    return JsonResponse({
        'job_id': str(job.job_id)
    }, status=200)

@api_view(['GET'])
def get_status(request, job_id):
    try:
        job = MediaAnalysisJob.objects.get(job_id=job_id)
    except MediaAnalysisJob.DoesNotExist:
        return JsonResponse({'error': 'Job not found'}, status=404)
        
    response_data = {
        'job_id': str(job.job_id),
        'status': job.status,
        'progress': job.progress,
        'sha256': job.file_hash,
        'message': job.message,
    }
    
    if job.error:
        response_data['error'] = job.error
        
    if job.analysis_report:
        response_data['analysis_report'] = job.analysis_report
        
    return JsonResponse(response_data)

@api_view(['GET'])
def serve_report_pdf(request, job_id):
    pdf_path = REPORTS_DIR / f"report_{job_id}.pdf"
    if not pdf_path.exists():
        raise Http404("Forensic report PDF not found.")
    
    response = FileResponse(
        open(pdf_path, 'rb'),
        content_type='application/pdf'
    )
    response['Content-Disposition'] = f'attachment; filename="forensic_report_{job_id}.pdf"'
    return response
