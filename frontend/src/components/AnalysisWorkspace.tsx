import React, { useState } from 'react';
import {
  ScanLine, Thermometer, Maximize2, X, ImageOff,
  AlertTriangle, CheckCircle2, ChevronLeft, ChevronRight,
} from 'lucide-react';
import type { JobStatus, TimelineFrame } from '../types';
import { API_BASE } from '../lib/utils';

interface Props {
  job: JobStatus | null;
  isAnalyzing: boolean;
}

const ImagePanel: React.FC<{
  url: string; label: string; labelColor: string; icon: React.ElementType;
  onExpand: () => void;
}> = ({ url, label, labelColor, icon: Icon, onExpand }) => {
  const [err, setErr] = useState(false);
  const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`;

  return (
    <div className="relative bg-zinc-950 rounded-xl overflow-hidden border border-zinc-800 group">
      {/* Label chip */}
      <div className={`absolute top-3 left-3 z-10 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-sm border ${labelColor}`}>
        <Icon className="w-3 h-3" />
        <span className="text-[10px] font-bold uppercase tracking-widest">{label}</span>
      </div>
      {/* Expand button */}
      <button
        onClick={onExpand}
        className="absolute top-3 right-3 z-10 p-1.5 rounded-lg bg-black/50 backdrop-blur-sm border border-white/10 opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <Maximize2 className="w-3.5 h-3.5 text-white/70" />
      </button>
      {/* Image */}
      <div className="aspect-square bg-zinc-950 flex items-center justify-center">
        {err ? (
          <div className="flex flex-col items-center gap-2 text-zinc-700">
            <ImageOff className="w-8 h-8" />
            <span className="text-xs">Image unavailable</span>
          </div>
        ) : (
          <img
            src={fullUrl}
            alt={label}
            onError={() => setErr(true)}
            className="w-full h-full object-cover"
          />
        )}
      </div>
    </div>
  );
};

const LightboxModal: React.FC<{ url: string; label: string; onClose: () => void }> = ({ url, label, onClose }) => {
  const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`;
  return (
    <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-sm flex items-center justify-center p-4" onClick={onClose}>
      <div className="relative max-w-3xl w-full" onClick={e => e.stopPropagation()}>
        <button onClick={onClose} className="absolute -top-10 right-0 text-zinc-400 hover:text-white flex items-center gap-2 text-sm">
          <X className="w-4 h-4" /> Close
        </button>
        <p className="text-zinc-400 text-xs font-mono mb-2 uppercase tracking-widest">{label}</p>
        <img src={fullUrl} alt={label} className="w-full rounded-2xl border border-zinc-700 shadow-2xl" />
      </div>
    </div>
  );
};

export const AnalysisWorkspace: React.FC<Props> = ({ job, isAnalyzing }) => {
  const [lightbox, setLightbox]         = useState<{ url: string; label: string } | null>(null);
  const [frameIdx, setFrameIdx]         = useState(0);

  /* ── Empty / Analyzing states ── */
  if (!job && !isAnalyzing) {
    return (
      <div className="card p-8 flex flex-col items-center justify-center min-h-[260px] gap-4">
        <div className="w-14 h-14 rounded-2xl bg-zinc-800 flex items-center justify-center">
          <ScanLine className="w-7 h-7 text-zinc-600" />
        </div>
        <div className="text-center">
          <p className="text-zinc-500 text-sm font-medium">Forensic Workspace</p>
          <p className="text-zinc-700 text-xs mt-1">Upload evidence to populate the comparison view</p>
        </div>
        {/* Placeholder grid */}
        <div className="grid grid-cols-2 gap-3 w-full max-w-md">
          {[0, 1].map(i => (
            <div key={i} className="aspect-square rounded-xl bg-zinc-800/50 animate-pulse" style={{ animationDelay: `${i * 0.2}s` }} />
          ))}
        </div>
      </div>
    );
  }

  if (isAnalyzing) {
    return (
      <div className="card p-8 flex flex-col items-center justify-center min-h-[260px] gap-5">
        <div className="relative w-16 h-16">
          <div className="absolute inset-0 rounded-full border-2 border-cyan-500/20 border-t-cyan-400 animate-spin" />
          <div className="absolute inset-2.5 rounded-full border-2 border-violet-500/20 border-t-violet-400 animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.3s' }} />
        </div>
        <div className="text-center">
          <p className="text-zinc-200 text-sm font-semibold">Running Forensic Analysis</p>
          <p className="text-zinc-600 text-xs font-mono mt-1">{job?.message || 'Dual-stream inference in progress…'}</p>
        </div>
        <div className="flex flex-wrap justify-center gap-2">
          {['Face Detection', 'EfficientNet-B4', 'DCT Spectral', 'Grad-CAM'].map(t => (
            <span key={t} className="text-[10px] bg-zinc-800 border border-zinc-700 text-zinc-500 px-2.5 py-1 rounded-full animate-pulse">
              {t}
            </span>
          ))}
        </div>
      </div>
    );
  }

  if (!job?.analysis_report) return null;

  const frames = job.analysis_report.timeline_frames;
  if (frames.length === 0) return null;

  const frame: TimelineFrame = frames[Math.min(frameIdx, frames.length - 1)];
  const isDeepfake = frame.confidence_score > 0.5;
  const confidencePct = (frame.confidence_score * 100).toFixed(1);

  return (
    <>
      {lightbox && <LightboxModal url={lightbox.url} label={lightbox.label} onClose={() => setLightbox(null)} />}

      <div className="space-y-4">
        {/* Frame Verdict Banner */}
        <div className={`flex items-center justify-between px-4 py-3 rounded-xl border ${isDeepfake ? 'bg-red-950/20 border-red-500/25' : 'bg-emerald-950/20 border-emerald-500/25'}`}>
          <div className="flex items-center gap-2.5">
            {isDeepfake
              ? <AlertTriangle className="w-5 h-5 text-red-400" />
              : <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            }
            <div>
              <p className={`text-sm font-bold ${isDeepfake ? 'text-red-400' : 'text-emerald-400'}`}>
                {isDeepfake ? 'MANIPULATED / DEEPFAKE DETECTED' : 'AUTHENTIC / PRISTINE'}
              </p>
              <p className="text-zinc-500 text-xs font-mono">
                Frame {frame.frame_index} · {frame.timestamp_seconds.toFixed(2)}s · {confidencePct}% confidence
              </p>
            </div>
          </div>
          {/* Frame navigator */}
          {frames.length > 1 && (
            <div className="flex items-center gap-2">
              <button onClick={() => setFrameIdx(i => Math.max(0, i - 1))} disabled={frameIdx === 0}
                className="p-1.5 rounded-lg bg-zinc-800 border border-zinc-700 disabled:opacity-30 hover:bg-zinc-700 transition-colors">
                <ChevronLeft className="w-4 h-4 text-zinc-400" />
              </button>
              <span className="text-zinc-500 text-xs font-mono">{frameIdx + 1}/{frames.length}</span>
              <button onClick={() => setFrameIdx(i => Math.min(frames.length - 1, i + 1))} disabled={frameIdx === frames.length - 1}
                className="p-1.5 rounded-lg bg-zinc-800 border border-zinc-700 disabled:opacity-30 hover:bg-zinc-700 transition-colors">
                <ChevronRight className="w-4 h-4 text-zinc-400" />
              </button>
            </div>
          )}
        </div>

        {/* Side-by-Side Image Comparison */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <p className="label">Original Face Crop</p>
            <ImagePanel
              url={frame.face_crop_url}
              label="ORIGINAL"
              labelColor="border-zinc-600 text-zinc-300"
              icon={ScanLine}
              onExpand={() => setLightbox({ url: frame.face_crop_url, label: 'Original Face Crop' })}
            />
          </div>
          <div className="space-y-2">
            <p className="label">Grad-CAM Localization Map</p>
            <ImagePanel
              url={frame.grad_cam_url}
              label="GRAD-CAM"
              labelColor="border-red-500/40 text-red-400"
              icon={Thermometer}
              onExpand={() => setLightbox({ url: frame.grad_cam_url, label: 'Grad-CAM Heatmap' })}
            />
          </div>
        </div>

        {/* Anomaly List */}
        {frame.anomalies.length > 0 && (
          <div className="bg-red-950/15 border border-red-500/20 rounded-xl px-4 py-3">
            <p className="label text-red-500 mb-2">Detected Anomalies</p>
            <div className="flex flex-wrap gap-2">
              {frame.anomalies.map(a => (
                <span key={a} className="text-xs bg-red-950/40 border border-red-500/20 text-red-300 px-2.5 py-1 rounded-full font-mono">{a}</span>
              ))}
            </div>
          </div>
        )}

        {/* All frames strip */}
        {frames.length > 1 && (
          <div>
            <p className="label mb-2">Frame Timeline ({frames.length} analyzed)</p>
            <div className="flex gap-2 overflow-x-auto pb-2">
              {frames.map((f, i) => (
                <button key={i} onClick={() => setFrameIdx(i)}
                  className={`flex-shrink-0 relative rounded-lg overflow-hidden border-2 transition-all ${i === frameIdx ? 'border-cyan-400' : f.confidence_score > 0.5 ? 'border-red-500/40' : 'border-emerald-500/30'}`}>
                  <img
                    src={f.face_crop_url.startsWith('http') ? f.face_crop_url : `${API_BASE}${f.face_crop_url}`}
                    alt={`Frame ${f.frame_index}`}
                    className="w-14 h-14 object-cover"
                    onError={e => (e.currentTarget.style.display = 'none')}
                  />
                  <div className={`absolute inset-0 flex items-end justify-center pb-0.5 ${f.confidence_score > 0.5 ? 'bg-red-900/30' : 'bg-emerald-900/20'}`}>
                    <span className="text-[8px] font-mono font-bold text-white/80">{(f.confidence_score * 100).toFixed(0)}%</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
};
