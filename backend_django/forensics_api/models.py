import uuid
from django.db import models

class MediaAnalysisJob(models.Model):
    class StatusChoices(models.TextChoices):
        QUEUED = 'QUEUED', 'Queued'
        EXTRACTING_FRAMES = 'EXTRACTING_FRAMES', 'Extracting Frames'
        ISOLATING_FACES = 'ISOLATING_FACES', 'Isolating Faces'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_hash = models.CharField(max_length=64, null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=StatusChoices.choices,
        default=StatusChoices.QUEUED
    )
    progress = models.IntegerField(default=0)
    message = models.CharField(max_length=255, null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    analysis_report = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"MediaAnalysisJob {self.job_id} - {self.status}"
