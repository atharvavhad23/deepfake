export type JobStatus = 'QUEUED' | 'EXTRACTING_FRAMES' | 'ISOLATING_FACES' | 'COMPLETED' | 'FAILED';

export interface TimelineFrame {
  frame_index: number;
  timestamp_seconds: number;
  face_crop_url: string;
  grad_cam_url: string;
  confidence_score: number;
  anomalies: string[];
}

export interface AnalysisReportPayload {
  job_id: string;
  file_name: string;
  sha256: string;
  generated_at: string;
  total_frames: number;
  timeline_frames: TimelineFrame[];
}

export interface JobStatusTelemetry {
  job_id: string;
  sha256?: string | null;
  status: JobStatus;
  progress: number;
  created_at: string;
  updated_at: string;
  source_filename?: string | null;
  input_path?: string | null;
  output_dir?: string | null;
  message?: string | null;
  error?: string | null;
  analysis_report?: AnalysisReportPayload | null;
}

export interface AnalyzeResponse {
  job_id: string;
  sha256: string;
  status: JobStatus;
  detail: string;
}