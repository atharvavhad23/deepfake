from django.urls import path
from . import views

urlpatterns = [
    path('analyze', views.analyze_media, name='analyze_media'),
    path('status/<uuid:job_id>', views.get_status, name='get_status'),
    path('reports/<uuid:job_id>/pdf', views.serve_report_pdf, name='serve_report_pdf'),
]
