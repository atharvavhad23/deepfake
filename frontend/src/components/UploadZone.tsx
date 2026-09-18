import React, { useCallback, useState, useRef } from 'react';
import {
  UploadCloud, FileVideo2, ImageIcon, ShieldCheck,
  Hash, HardDrive, Lock, RotateCcw, AlertCircle,
} from 'lucide-react';
import type { JobStatus } from '../types';
import { computeSHA256, formatFileSize, API_BASE, pollStatus } from '../lib/utils';

interface UploadZoneProps {
  onJobComplete: (job: JobStatus, filename: string, fileSize: number) => void;
}

type Phase = 'idle' | 'hover' | 'hashing' | 'uploading' | 'analyzing' | 'done' | 'error';

const PHASE_LABEL: Record<Phase, string> = {
  idle: '', hover: '', hashing: 'Computing SHA-256 fingerprint…',
  uploading: 'Transmitting to forensic engine…',
  analyzing: 'Running dual-stream inference…',
  done: 'Analysis complete', error: 'Error occurred',
};

export const UploadZone: React.FC<UploadZoneProps> = ({ onJobComplete }) => {
  const [phase, setPhase]       = useState<Phase>('idle');
  const [progress, setProgress] = useState(0);
  const [message, setMessage]   = useState('');
  const [hash, setHash]         = useState('');
  const [fileInfo, setFileInfo] = useState<{ name: string; size: number } | null>(null);
  const [error, setError]       = useState('');
  const fileRef = useRef<HTMLInputElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const reset = () => {
    abortRef.current?.abort();
    setPhase('idle'); setProgress(0); setHash('');
    setFileInfo(null); setError(''); setMessage('');
  };

  const process = useCallback(async (file: File) => {
    const allowed = ['video/mp4', 'image/png', 'image/jpeg', 'image/jpg'];
    if (!allowed.includes(file.type)) {
      setError('Invalid file. Upload .mp4, .png, or .jpg'); setPhase('error'); return;
    }

    setFileInfo({ name: file.name, size: file.size });
    setError(''); setPhase('hashing'); setProgress(8);

    const sha = await computeSHA256(file);
    setHash(sha); setProgress(20);

    setPhase('uploading'); setProgress(30);
    const fd = new FormData(); fd.append('file', file);

    let jobId: string;
    try {
      const res = await fetch(`${API_BASE}/api/v1/analyze`, { method: 'POST', body: fd });
      if (!res.ok) throw new Error('Upload failed');
      const data = await res.json();
      jobId = data.job_id;
    } catch {
      setError('Backend unreachable — ensure Django server is running.'); setPhase('error'); return;
    }

    setPhase('analyzing'); setProgress(45);
    abortRef.current = new AbortController();

    // Fake progress while polling
    const fakeProgress = setInterval(() => {
      setProgress(p => Math.min(p + 2, 90));
    }, 800);

    try {
      // Poll real backend for status updates too
      const pollInterval = setInterval(async () => {
        try {
          const res = await fetch(`${API_BASE}/api/v1/status/${jobId}`);
          const data: JobStatus = await res.json();
          setProgress(Math.max(45, Math.min(data.progress, 90)));
          setMessage(data.message || '');
        } catch { /* ignore */ }
      }, 1500);

      const finalJob = await pollStatus(jobId, abortRef.current.signal);
      clearInterval(pollInterval);
      clearInterval(fakeProgress);

      if (finalJob.status === 'FAILED') {
        setError(finalJob.error || 'Analysis failed'); setPhase('error'); return;
      }

      setProgress(100); setPhase('done');
      onJobComplete(finalJob, file.name, file.size);
    } catch (e: unknown) {
      clearInterval(fakeProgress);
      if ((e as Error).message !== 'Aborted') {
        setError('Polling failed'); setPhase('error');
      }
    }
  }, [onJobComplete]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (phase !== 'idle' && phase !== 'error') return;
    const file = e.dataTransfer.files[0];
    if (file) process(file);
  }, [phase, process]);

  const onFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) process(file);
    e.target.value = '';
  };

  const isProcessing = ['hashing', 'uploading', 'analyzing'].includes(phase);

  return (
    <div className="space-y-4">
      {/* Drop Target */}
      <div
        onDrop={onDrop}
        onDragOver={e => { e.preventDefault(); if (!isProcessing) setPhase('hover'); }}
        onDragLeave={() => { if (!isProcessing) setPhase('idle'); }}
        onClick={() => !isProcessing && phase !== 'done' && fileRef.current?.click()}
        className={`relative overflow-hidden rounded-2xl border-2 border-dashed transition-all duration-300 cursor-pointer select-none
          ${phase === 'hover'     ? 'border-cyan-400 bg-cyan-950/30 shadow-[0_0_30px_rgba(34,211,238,0.15)]' : ''}
          ${phase === 'idle'      ? 'border-zinc-700 bg-zinc-900 hover:border-zinc-600 hover:bg-zinc-800/50' : ''}
          ${isProcessing          ? 'border-violet-500/50 bg-violet-950/10 cursor-default' : ''}
          ${phase === 'done'      ? 'border-emerald-500/50 bg-emerald-950/10 cursor-default' : ''}
          ${phase === 'error'     ? 'border-red-500/40 bg-red-950/10' : ''}
        `}
      >
        <input ref={fileRef} type="file" accept=".mp4,.png,.jpg,.jpeg" className="hidden" onChange={onFile} />

        {/* Subtle grid bg */}
        <div className="absolute inset-0 opacity-[0.03]"
          style={{ backgroundImage: 'linear-gradient(#fff 1px,transparent 1px),linear-gradient(90deg,#fff 1px,transparent 1px)', backgroundSize: '28px 28px' }} />

        <div className="relative p-8 flex flex-col items-center justify-center min-h-[200px] gap-5">

          {(phase === 'idle' || phase === 'hover') && (
            <>
              <div className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-300
                ${phase === 'hover' ? 'bg-cyan-500/20 scale-110' : 'bg-zinc-800'}`}>
                <UploadCloud className={`w-8 h-8 transition-colors ${phase === 'hover' ? 'text-cyan-400' : 'text-zinc-500'}`} />
              </div>
              <div className="text-center space-y-1.5">
                <p className="text-zinc-100 font-semibold text-sm">Drop Evidence File</p>
                <p className="text-zinc-500 text-xs">or click to browse — .mp4 · .png · .jpg</p>
              </div>
              <div className="flex items-center gap-6 text-zinc-600 text-xs">
                <span className="flex items-center gap-1.5"><FileVideo2 className="w-3.5 h-3.5" />MP4 Video</span>
                <span className="w-px h-3 bg-zinc-700" />
                <span className="flex items-center gap-1.5"><ImageIcon className="w-3.5 h-3.5" />PNG / JPG Image</span>
              </div>
              <div className="flex items-center gap-1.5 text-zinc-700 text-xs">
                <Lock className="w-3 h-3" />SHA-256 chain-of-custody seal computed automatically
              </div>
            </>
          )}

          {isProcessing && (
            <div className="w-full flex flex-col items-center gap-4">
              {/* Spinner rings */}
              <div className="relative w-14 h-14">
                <div className="absolute inset-0 rounded-full border-2 border-violet-500/20 border-t-violet-400 animate-spin" />
                <div className="absolute inset-2 rounded-full border-2 border-cyan-500/20 border-t-cyan-400 animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.4s' }} />
              </div>
              <div className="text-center">
                <p className="text-zinc-200 text-sm font-semibold">{PHASE_LABEL[phase]}</p>
                {message && <p className="text-zinc-500 text-xs mt-1 font-mono">{message}</p>}
              </div>
              {/* Progress bar */}
              <div className="w-full max-w-xs space-y-1">
                <div className="bg-zinc-800 rounded-full h-1.5">
                  <div className="h-1.5 rounded-full bg-gradient-to-r from-violet-500 to-cyan-400 transition-all duration-500" style={{ width: `${progress}%` }} />
                </div>
                <div className="flex justify-between text-zinc-600 text-xs font-mono">
                  <span>{phase.toUpperCase()}</span><span>{progress}%</span>
                </div>
              </div>
            </div>
          )}

          {phase === 'done' && (
            <div className="flex flex-col items-center gap-3">
              <div className="w-14 h-14 rounded-2xl bg-emerald-500/15 flex items-center justify-center">
                <ShieldCheck className="w-7 h-7 text-emerald-400" />
              </div>
              <p className="text-emerald-400 font-semibold text-sm">Analysis Complete</p>
              <button onClick={e => { e.stopPropagation(); reset(); }} className="text-xs text-zinc-500 hover:text-zinc-300 flex items-center gap-1.5 mt-1 underline underline-offset-2">
                <RotateCcw className="w-3 h-3" /> Analyze another file
              </button>
            </div>
          )}

          {phase === 'error' && (
            <div className="flex flex-col items-center gap-3">
              <div className="w-14 h-14 rounded-2xl bg-red-500/10 flex items-center justify-center">
                <AlertCircle className="w-7 h-7 text-red-400" />
              </div>
              <p className="text-red-400 font-semibold text-sm">Analysis Failed</p>
              <p className="text-zinc-500 text-xs max-w-xs text-center">{error}</p>
              <button onClick={e => { e.stopPropagation(); reset(); }} className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1.5 underline underline-offset-2">
                <RotateCcw className="w-3 h-3" /> Try again
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Chain-of-Custody Pre-Analysis Panel */}
      {hash && fileInfo && (
        <div className="card p-4 animate-[slideUp_0.35s_ease-out]">
          <div className="flex items-center gap-2 mb-3">
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
            <span className="label">Pre-Analysis Check — Chain of Custody</span>
          </div>
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div>
              <p className="label mb-1">File Name</p>
              <p className="text-zinc-200 text-xs font-mono truncate">{fileInfo.name}</p>
            </div>
            <div>
              <p className="label mb-1"><HardDrive className="w-3 h-3 inline mr-1" />File Size</p>
              <p className="text-zinc-200 text-xs font-mono">{formatFileSize(fileInfo.size)}</p>
            </div>
          </div>
          <div>
            <div className="flex items-center gap-1.5 mb-1.5">
              <Hash className="w-3 h-3 text-amber-400" />
              <span className="label">SHA-256 Cryptographic Fingerprint</span>
            </div>
            <p className="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-amber-400 text-[11px] font-mono break-all leading-relaxed">
              {hash}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
