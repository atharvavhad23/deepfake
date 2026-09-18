import { useEffect, useMemo, useReducer } from 'react';
import type { AnalyzeResponse, AnalysisReportPayload, JobStatusTelemetry, TimelineFrame } from '../types/forensics';
import { API_BASE_URL, fetchJobStatus, resolveBackendUrl, submitAnalysis } from '../lib/api';

type DashboardPhase = 'idle' | 'uploading' | 'polling' | 'ready' | 'failed';

interface DashboardState {
  phase: DashboardPhase;
  selectedFile: File | null;
  jobId: string | null;
  telemetry: JobStatusTelemetry | null;
  activeFrameIndex: number;
  error: string | null;
}

type DashboardAction =
  | { type: 'select_file'; file: File | null }
  | { type: 'upload_start' }
  | { type: 'upload_success'; response: AnalyzeResponse }
  | { type: 'poll_success'; telemetry: JobStatusTelemetry }
  | { type: 'poll_failed'; error: string }
  | { type: 'set_active_frame'; index: number }
  | { type: 'clear_error' };

const initialState: DashboardState = {
  phase: 'idle',
  selectedFile: null,
  jobId: null,
  telemetry: null,
  activeFrameIndex: 0,
  error: null,
};

function reducer(state: DashboardState, action: DashboardAction): DashboardState {
  switch (action.type) {
    case 'select_file':
      return {
        ...state,
        selectedFile: action.file,
        error: null,
        phase: 'idle',
        telemetry: null,
        jobId: null,
        activeFrameIndex: 0,
      };
    case 'upload_start':
      return {
        ...state,
        phase: 'uploading',
        error: null,
      };
    case 'upload_success':
      return {
        ...state,
        phase: 'polling',
        jobId: action.response.job_id,
        error: null,
      };
    case 'poll_success': {
      const report = action.telemetry.analysis_report;
      const frameCount = report?.timeline_frames.length ?? 0;
      return {
        ...state,
        telemetry: action.telemetry,
        phase: action.telemetry.status === 'COMPLETED' ? 'ready' : action.telemetry.status === 'FAILED' ? 'failed' : 'polling',
        activeFrameIndex:
          frameCount === 0
            ? 0
            : state.activeFrameIndex >= frameCount
              ? 0
              : state.activeFrameIndex,
        error: action.telemetry.error ?? null,
      };
    }
    case 'poll_failed':
      return {
        ...state,
        phase: 'failed',
        error: action.error,
      };
    case 'set_active_frame':
      return {
        ...state,
        activeFrameIndex: action.index,
      };
    case 'clear_error':
      return {
        ...state,
        error: null,
      };
    default:
      return state;
  }
}

function statusTone(score: number): string {
  return score > 0.85 ? 'bg-red-600 text-white shadow-lg shadow-red-950/40' : 'bg-slate-600 text-slate-100';
}

function formatStatus(status: JobStatusTelemetry['status']): string {
  switch (status) {
    case 'QUEUED':
      return 'Queued';
    case 'EXTRACTING_FRAMES':
      return 'Extracting Frames';
    case 'ISOLATING_FACES':
      return 'Isolating Faces';
    case 'COMPLETED':
      return 'Completed';
    case 'FAILED':
      return 'Failed';
  }
}

function resolveFrames(job: JobStatusTelemetry | null): TimelineFrame[] {
  const frames = job?.analysis_report?.timeline_frames ?? [];
  return [...frames].sort((left, right) => left.frame_index - right.frame_index);
}

function resolveActiveFrame(frames: TimelineFrame[], activeFrameIndex: number): TimelineFrame | null {
  if (!frames.length) {
    return null;
  }

  return frames.find((frame) => frame.frame_index === activeFrameIndex) ?? frames[0] ?? null;
}

function resolveFrameUrl(url: string): string {
  return resolveBackendUrl(url);
}

export default function ForensicDashboard() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const frames = useMemo(() => resolveFrames(state.telemetry), [state.telemetry]);
  const activeFrame = useMemo(() => resolveActiveFrame(frames, state.activeFrameIndex), [frames, state.activeFrameIndex]);

  useEffect(() => {
    if (state.phase !== 'polling' || !state.jobId) {
      return;
    }

    let cancelled = false;

    const intervalId = window.setInterval(async () => {
      try {
        const telemetry = await fetchJobStatus(state.jobId as string);
        if (cancelled) {
          return;
        }

        dispatch({ type: 'poll_success', telemetry });

        if (telemetry.status === 'COMPLETED' || telemetry.status === 'FAILED') {
          window.clearInterval(intervalId);
        }
      } catch (pollError) {
        if (cancelled) {
          return;
        }

        dispatch({ type: 'poll_failed', error: pollError instanceof Error ? pollError.message : 'Polling failed' });
        window.clearInterval(intervalId);
      }
    }, 1500);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [state.phase, state.jobId]);

  useEffect(() => {
    if (!frames.length) {
      return;
    }

    const activeFrameExists = frames.some((frame) => frame.frame_index === state.activeFrameIndex);
    if (!activeFrameExists) {
      dispatch({ type: 'set_active_frame', index: frames[0].frame_index });
    }
  }, [frames, state.activeFrameIndex]);

  async function handleSubmit() {
    if (!state.selectedFile) {
      dispatch({ type: 'poll_failed', error: 'Please choose an MP4 or JPG file first.' });
      return;
    }

    dispatch({ type: 'upload_start' });

    try {
      const response = await submitAnalysis(state.selectedFile);
      dispatch({ type: 'upload_success', response });
    } catch (submitError) {
      dispatch({ type: 'poll_failed', error: submitError instanceof Error ? submitError.message : 'Upload failed' });
    }
  }

  const report: AnalysisReportPayload | null = state.telemetry?.analysis_report ?? null;
  const pdfExportUrl = state.jobId ? `${API_BASE_URL}/api/v1/reports/${encodeURIComponent(state.jobId)}/pdf` : null;

  return (
    <div className="min-h-screen bg-forensics-grid text-slate-100">
      <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[280px_1fr]">
        <aside className="border-r border-cyan-400/10 bg-surface/95 px-6 py-8 backdrop-blur-xl">
          <div className="mb-10 flex items-center gap-3">
            <div className="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-500 font-black text-slate-950 shadow-glow">
              DD
            </div>
            <div>
              <p className="text-lg font-bold tracking-wide">Deepfake Detective</p>
              <p className="text-sm text-slate-400">Digital Forensics Workspace</p>
            </div>
          </div>

          <nav className="space-y-2 text-sm font-medium">
            {['Upload', 'Active Jobs', 'Archived Reports', 'Settings'].map((item, index) => (
              <div
                key={item}
                className={`rounded-2xl border px-4 py-3 transition ${
                  index === 0
                    ? 'border-cyan-400/30 bg-cyan-400/10 text-cyan-100'
                    : 'border-white/5 bg-white/5 text-slate-400 hover:border-cyan-400/20 hover:bg-cyan-400/10 hover:text-slate-100'
                }`}
              >
                {item}
              </div>
            ))}
          </nav>

          <div className="mt-10 rounded-3xl border border-white/10 bg-panel p-5 shadow-glow">
            <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Telemetry</p>
            <p className="mt-3 text-sm font-semibold text-slate-100">Reducer-driven job state machine</p>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              Explicit phases keep upload, polling, completion, and failure states isolated so the UI remains stable while the backend updates asynchronously.
            </p>
          </div>
        </aside>

        <main className="px-5 py-6 lg:px-8">
          <header className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-cyan-300/80">Forensic Analytics Dashboard</p>
              <h1 className="mt-3 max-w-3xl text-3xl font-black leading-tight text-white lg:text-5xl">
                Scrub suspicious frames, review heatmaps, and export the audit trail.
              </h1>
            </div>
            <div className="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-2 text-sm font-medium text-cyan-100">
              Backend status: {state.telemetry ? formatStatus(state.telemetry.status) : 'Ready'}
            </div>
          </header>

          <section className="grid gap-5 xl:grid-cols-[1.4fr_0.9fr]">
            <div className="rounded-[28px] border border-white/10 bg-panel/90 p-6 shadow-glow">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-white">Analyze New Media (Video/Image)</h2>
                  <p className="mt-2 text-sm leading-6 text-slate-400">
                    Upload a media file to start secure ingestion, frame extraction, face cropping, and explainable AI analysis.
                  </p>
                </div>
                <div className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs uppercase tracking-[0.25em] text-slate-300">
                  Job ID: {state.jobId ?? 'Not started'}
                </div>
              </div>

              <label className="mt-6 flex min-h-[260px] cursor-pointer flex-col items-center justify-center rounded-[24px] border border-dashed border-cyan-400/30 bg-slate-950/70 p-8 text-center transition hover:border-cyan-300 hover:bg-slate-950/90">
                <input
                  type="file"
                  accept="video/mp4,video/x-msvideo,image/jpeg,image/jpg,image/png"
                  className="hidden"
                  onChange={(event) => dispatch({ type: 'select_file', file: event.target.files?.[0] ?? null })}
                />
                <div className="grid h-16 w-16 place-items-center rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-500 text-2xl font-black text-slate-950">
                  ↑
                </div>
                <p className="mt-5 text-lg font-semibold text-white">Drag and drop evidence here</p>
                <p className="mt-2 text-sm text-slate-400">or click to browse a local JPG, PNG, AVI, or MP4</p>
                <p className="mt-4 text-xs uppercase tracking-[0.25em] text-slate-500">
                  Selected: {state.selectedFile?.name ?? 'No file chosen'}
                </p>
              </label>

              {state.error ? <p className="mt-4 rounded-2xl border border-red-400/20 bg-red-500/10 px-4 py-3 text-sm text-red-200">{state.error}</p> : null}

              <div className="mt-5 flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={state.phase === 'uploading'}
                  className="rounded-full bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {state.phase === 'uploading' ? 'Uploading...' : 'Start Analysis'}
                </button>

                <a
                  href={pdfExportUrl ?? '#'}
                  target="_blank"
                  rel="noreferrer"
                  aria-disabled={!pdfExportUrl}
                  className={`rounded-full border px-5 py-3 text-sm font-semibold transition ${
                    pdfExportUrl
                      ? 'border-white/10 bg-white/5 text-slate-100 hover:border-cyan-300 hover:bg-cyan-400/10'
                      : 'pointer-events-none border-white/5 bg-white/5 text-slate-500'
                  }`}
                >
                  Export PDF Audit Log
                </a>

                <div className="text-sm text-slate-400">
                  {state.telemetry?.message ?? 'Awaiting upload.'}
                </div>
              </div>
            </div>

            <div className="rounded-[28px] border border-white/10 bg-panel/90 p-6 shadow-glow">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold text-white">Timeline Scrubber</h2>
                  <p className="mt-2 text-sm text-slate-400">Flagged slices light up crimson when manipulation probability exceeds the threshold.</p>
                </div>
                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs uppercase tracking-[0.22em] text-slate-300">
                  {formatStatus(state.telemetry?.status ?? 'QUEUED')}
                </span>
              </div>

              <div className="mt-6 rounded-3xl border border-white/10 bg-slate-950/70 p-4">
                <svg viewBox="0 0 1000 120" className="h-28 w-full">
                  <rect x="0" y="48" width="1000" height="20" rx="10" fill="rgba(255,255,255,0.08)" />
                  {frames.map((frame, index) => {
                    const x = frames.length <= 1 ? 40 : 40 + (920 * index) / Math.max(frames.length - 1, 1);
                    const width = frames.length <= 1 ? 920 : Math.max(22, 920 / frames.length - 8);
                    const isSelected = activeFrame?.frame_index === frame.frame_index;
                    const isFlagged = frame.confidence_score > 0.85;

                    return (
                      <g
                        key={`${frame.frame_index}-${index}`}
                        role="button"
                        tabIndex={0}
                        onClick={() => dispatch({ type: 'set_active_frame', index: frame.frame_index })}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter' || event.key === ' ') {
                            dispatch({ type: 'set_active_frame', index: frame.frame_index });
                          }
                        }}
                        className="cursor-pointer"
                      >
                        <rect
                          x={x}
                          y={40}
                          width={width}
                          height={36}
                          rx={12}
                          fill={isSelected ? 'rgba(56, 189, 248, 0.28)' : isFlagged ? '#dc2626' : '#475569'}
                          stroke={isSelected ? '#67e8f9' : 'transparent'}
                          strokeWidth={2}
                        />
                        <text x={x + 12} y={62} fill="white" fontSize="12" fontWeight={700}>
                          F{frame.frame_index}
                        </text>
                        <text x={x + 12} y={80} fill="rgba(255,255,255,0.8)" fontSize="10">
                          {(frame.confidence_score * 100).toFixed(0)}%
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>

              <div className="mt-6 h-3 overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 transition-all duration-500"
                  style={{ width: `${state.telemetry?.progress ?? 0}%` }}
                />
              </div>

              <div className="mt-6 grid grid-cols-3 gap-3 text-center text-sm">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
                  <p className="text-slate-400">Progress</p>
                  <p className="mt-1 font-semibold text-white">{state.telemetry?.progress ?? 0}%</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
                  <p className="text-slate-400">Frames</p>
                  <p className="mt-1 font-semibold text-white">{report?.total_frames ?? 0}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
                  <p className="text-slate-400">Hash</p>
                  <p className="mt-1 truncate font-semibold text-white">{state.telemetry?.sha256?.slice(0, 12) ?? '—'}</p>
                </div>
              </div>
            </div>
          </section>

          <section className="mt-5 rounded-[28px] border border-white/10 bg-panel/90 p-6 shadow-glow">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-white">Inspection Gallery</h2>
                <p className="mt-2 text-sm text-slate-400">
                  Click a flagged segment to sync the exact face crop, Grad-CAM overlay, and anomaly notes at that timestamp.
                </p>
              </div>
              <div className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-4 py-2 text-sm text-emerald-100">
                {state.telemetry?.status === 'COMPLETED' ? 'Ready for review' : 'Waiting for completion'}
              </div>
            </div>

            {activeFrame ? (
              <div className="mt-6 grid gap-5 xl:grid-cols-[1fr_0.8fr]">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="rounded-3xl border border-white/10 bg-slate-950/70 p-3">
                    <p className="mb-3 text-sm font-semibold text-slate-300">Face Crop</p>
                    <div className="overflow-hidden rounded-2xl border border-white/10 bg-black">
                      <img
                        src={resolveFrameUrl(activeFrame.face_crop_url)}
                        alt={`Face crop frame ${activeFrame.frame_index}`}
                        className="h-80 w-full object-contain"
                      />
                    </div>
                  </div>

                  <div className="rounded-3xl border border-white/10 bg-slate-950/70 p-3">
                    <p className="mb-3 text-sm font-semibold text-slate-300">Grad-CAM Overlay</p>
                    <div className="overflow-hidden rounded-2xl border border-white/10 bg-black">
                      <img
                        src={resolveFrameUrl(activeFrame.grad_cam_url)}
                        alt={`Grad-CAM overlay frame ${activeFrame.frame_index}`}
                        className="h-80 w-full object-contain"
                      />
                    </div>
                  </div>
                </div>

                <aside className="rounded-3xl border border-white/10 bg-slate-950/70 p-5">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-xs uppercase tracking-[0.26em] text-slate-400">Current slice</p>
                      <h3 className="mt-2 text-2xl font-black text-white">Frame #{activeFrame.frame_index}</h3>
                    </div>
                    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusTone(activeFrame.confidence_score)}`}>
                      {(activeFrame.confidence_score * 100).toFixed(1)}% fake probability
                    </span>
                  </div>

                  <div className="mt-5 space-y-3">
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
                      <span className="block text-slate-500">Timestamp</span>
                      {activeFrame.timestamp_seconds.toFixed(3)} seconds
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                      <span className="mb-2 block text-sm text-slate-500">Detected anomalies</span>
                      <div className="flex flex-wrap gap-2">
                        {activeFrame.anomalies.length ? (
                          activeFrame.anomalies.map((item) => (
                            <span
                              key={item}
                              className="rounded-full border border-white/10 bg-slate-800 px-3 py-1 text-xs text-slate-100"
                            >
                              {item}
                            </span>
                          ))
                        ) : (
                          <span className="text-sm text-slate-400">No anomalies recorded for this slice.</span>
                        )}
                      </div>
                    </div>
                  </div>
                </aside>
              </div>
            ) : (
              <div className="mt-6 rounded-3xl border border-dashed border-white/10 bg-slate-950/50 p-10 text-center text-slate-400">
                Once the backend finishes, the timeline scrubber will unlock the frame-level evidence view.
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}