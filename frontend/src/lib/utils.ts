import type { ForensicLog } from '../types';

export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const MOCK_LOGS: ForensicLog[] = [
  { id: '1', filename: 'suspect_footage_01.mp4', sha256: 'af17b04a3e9c1f2d8b5e6a7c0d4f9e2b1a3c5d7f8e0b2c4a6d8f0e2b4c6a8d0', timestamp: '2026-07-11T08:45:22Z', verdict: 'manipulated', confidence: 94.2 },
  { id: '2', filename: 'evidence_clip_02.mp4',   sha256: 'b2c8e4f6a0d2b4c6e8f0a2b4d6f8a0c2e4f6b8d0a2c4e6f8b0d2f4a6c8e0b2', timestamp: '2026-07-11T07:32:10Z', verdict: 'authentic',   confidence: 87.6 },
  { id: '3', filename: 'witness_photo_03.png',   sha256: 'c3d9f5b7c1e3d5f7b9e1c3d5f7b9c1e3f5d7b9e1c3f5d7b9e1d3f5b7c9e1d3', timestamp: '2026-07-10T22:15:08Z', verdict: 'manipulated', confidence: 98.1 },
  { id: '4', filename: 'cctv_frame_04.png',      sha256: 'd4e0c6a8d2f4a6c8e0b2d4f6a8c0e2b4d6f8a0c2e4b6d8f0a2c4e6b8d0f2a4', timestamp: '2026-07-10T18:03:45Z', verdict: 'authentic',   confidence: 91.3 },
  { id: '5', filename: 'testimony_05.mp4',       sha256: 'e5f1d7b9e3c5f7d9b1e3c5d7f9b1d3f5b7d9c1e3f5b7d9c1e3d5f7b9c1e3d5', timestamp: '2026-07-10T14:55:30Z', verdict: 'manipulated', confidence: 78.4 },
];

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(2)} MB`;
}

export function truncateHash(hash: string, length = 16): string {
  if (!hash) return '—';
  return `${hash.slice(0, length)}...`;
}

export function formatTimestamp(ts: string): string {
  return new Date(ts).toLocaleString('en-US', { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false });
}

export async function computeSHA256(file: File): Promise<string> {
  const buffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
  return Array.from(new Uint8Array(hashBuffer)).map(b => b.toString(16).padStart(2, '0')).join('');
}

export async function pollStatus(jobId: string, signal?: AbortSignal): Promise<import('../types').JobStatus> {
  return new Promise((resolve, reject) => {
    const interval = setInterval(async () => {
      if (signal?.aborted) { clearInterval(interval); reject(new Error('Aborted')); return; }
      try {
        const res = await fetch(`${API_BASE}/api/v1/status/${jobId}`, { signal });
        const data: import('../types').JobStatus = await res.json();
        if (data.status === 'COMPLETED' || data.status === 'FAILED') {
          clearInterval(interval);
          resolve(data);
        }
      } catch (e) {
        clearInterval(interval);
        reject(e);
      }
    }, 1500);
  });
}
