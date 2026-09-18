import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_config.settings')
django.setup()

from forensics_api.models import MediaAnalysisJob

try:
    job = MediaAnalysisJob.objects.get(job_id='1262c39a-efdb-48a1-97f6-ea11cfa13cfa')
    print("JOB STATUS:", job.status)
except Exception as e:
    print(e)
