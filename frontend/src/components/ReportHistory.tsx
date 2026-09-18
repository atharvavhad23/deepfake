import React from 'react';
import { Clock, AlertTriangle, CheckCircle2, Hash, ChevronRight } from 'lucide-react';
import type { ForensicLog } from '../types';
import { truncateHash, formatTimestamp } from '../lib/utils';
import { MOCK_LOGS } from '../lib/utils';

interface ReportHistoryProps {
  logs?: ForensicLog[];
}

export const ReportHistory: React.FC<ReportHistoryProps> = ({ logs = MOCK_LOGS }) => {
  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-zinc-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-zinc-500" />
          <h3 className="text-sm font-semibold text-zinc-200">Recent Forensic Logs</h3>
          <span className="bg-zinc-800 text-zinc-500 text-xs px-2 py-0.5 rounded-full font-mono">{logs.length}</span>
        </div>
        <button className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors">
          View all <ChevronRight className="w-3 h-3" />
        </button>
      </div>

      {/* Column Headers */}
      <div className="px-5 py-2 bg-zinc-950/50 border-b border-zinc-800/50 grid grid-cols-12 gap-2 text-xs text-zinc-600 font-semibold uppercase tracking-wide">
        <div className="col-span-1">Status</div>
        <div className="col-span-3">Filename</div>
        <div className="col-span-4">SHA-256 Hash</div>
        <div className="col-span-2">Timestamp</div>
        <div className="col-span-1">Confidence</div>
        <div className="col-span-1">Action</div>
      </div>

      {/* Rows */}
      <div className="divide-y divide-zinc-800/50">
        {logs.map((log, idx) => {
          const isManipulated = log.verdict === 'manipulated';
          return (
            <div
              key={log.id}
              className="px-5 py-3.5 grid grid-cols-12 gap-2 items-center hover:bg-zinc-800/80 transition-all duration-300 animate-fade-in group hover:border-zinc-700"
              style={{ animationDelay: `${idx * 0.06}s` }}
            >
              {/* Status */}
              <div className="col-span-1 flex items-center">
                {isManipulated ? (
                  <div className="w-6 h-6 rounded flex items-center justify-center bg-red-500/10 border border-red-500/20 shadow-[0_0_8px_rgba(239,68,68,0.1)]">
                    <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
                  </div>
                ) : (
                  <div className="w-6 h-6 rounded flex items-center justify-center bg-emerald-500/10 border border-emerald-500/20 shadow-[0_0_8px_rgba(16,185,129,0.1)]">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  </div>
                )}
              </div>

              {/* Filename */}
              <div className="col-span-3">
                <p className="text-zinc-300 text-xs font-medium truncate">{log.filename}</p>
                <p className={`text-[10px] uppercase tracking-widest font-bold mt-0.5 ${isManipulated ? 'text-red-500' : 'text-emerald-500'}`}>
                  {isManipulated ? 'DEEPFAKE' : 'AUTHENTIC'}
                </p>
              </div>

              {/* Hash */}
              <div className="col-span-4">
                <div className="flex items-center gap-1.5">
                  <Hash className="w-3 h-3 text-zinc-600 flex-shrink-0" />
                  <span className="text-zinc-500 text-xs font-mono truncate">{truncateHash(log.sha256, 20)}</span>
                </div>
              </div>

              {/* Timestamp */}
              <div className="col-span-2">
                <p className="text-zinc-500 text-xs font-mono">{formatTimestamp(log.timestamp)}</p>
              </div>

              {/* Confidence */}
              <div className="col-span-1">
                <span className={`text-xs font-mono font-semibold ${isManipulated ? 'text-red-400' : 'text-emerald-400'}`}>
                  {log.confidence.toFixed(1)}%
                </span>
              </div>

              {/* Action */}
              <div className="col-span-1 flex justify-end">
                <button className="opacity-0 group-hover:opacity-100 transition-opacity text-xs text-cyan-400 hover:text-cyan-300 p-1 rounded hover:bg-zinc-700">
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {logs.length === 0 && (
        <div className="py-12 text-center">
          <Clock className="w-8 h-8 text-zinc-700 mx-auto mb-3" />
          <p className="text-zinc-600 text-sm">No forensic logs yet</p>
          <p className="text-zinc-700 text-xs mt-1">Analyzed files will appear here</p>
        </div>
      )}
    </div>
  );
};
