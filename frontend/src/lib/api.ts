import type { AnalyzeResponse, JobStatusTelemetry } from '../types/forensics';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export function resolveBackendUrl(path: string): string {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }

  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

export async function submitAnalysis(file: File): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || 'Upload failed');
  }

  return (await response.json()) as AnalyzeResponse;
}

export async function fetchJobStatus(jobId: string): Promise<JobStatusTelemetry> {
  const response = await fetch(`${API_BASE_URL}/api/v1/status/${encodeURIComponent(jobId)}`);

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || 'Unable to load job status');
  }

  return (await response.json()) as JobStatusTelemetry;
}
