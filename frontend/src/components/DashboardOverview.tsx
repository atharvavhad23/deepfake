import React from 'react';
import {
  TrendingUp, Shield, AlertTriangle, CheckCircle2, Activity,
  FileText, Clock, BarChart3, Zap
} from 'lucide-react';
import type { ForensicLog } from '../types';

interface DashboardOverviewProps {
  logs: ForensicLog[];
}

export const DashboardOverview: React.FC<DashboardOverviewProps> = ({ logs }) => {
  const total = logs.length;
  const manipulated = logs.filter(l => l.verdict === 'manipulated').length;
  const authentic = logs.filter(l => l.verdict === 'authentic').length;
  const avgConfidence = total > 0 ? logs.reduce((sum, l) => sum + l.confidence, 0) / total : 0;

  const stats = [
    { label: 'Total Cases Analyzed', value: total.toString(), icon: FileText, color: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/20' },
    { label: 'Deepfakes Detected', value: manipulated.toString(), icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' },
    { label: 'Authentic Verified', value: authentic.toString(), icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' },
    { label: 'Avg. Confidence', value: `${avgConfidence.toFixed(1)}%`, icon: TrendingUp, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20' },
  ];

  const modelStats = [
    { label: 'NexaShield Model', value: 'v3.1', icon: Shield },
    { label: 'Model Accuracy', value: '72.82%', icon: BarChart3 },
    { label: 'Training Samples', value: '1,030', icon: Activity },
    { label: 'Inference Engine', value: 'EfficientNet-B4', icon: Zap },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-bold text-zinc-100">Forensic Analysis Dashboard</h2>
          <p className="text-zinc-500 text-sm mt-1">NexaShield Dual-Stream Deepfake Detection System</p>
        </div>
        <div className="flex items-center gap-2 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2">
          <Clock className="w-3.5 h-3.5 text-zinc-500" />
          <span className="text-zinc-400 text-xs font-mono">{new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-4 gap-4">
        {stats.map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} className="relative bg-zinc-900/60 backdrop-blur-md border border-zinc-800/80 rounded-2xl p-5 space-y-3 overflow-hidden shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)] group transition-all duration-300 hover:border-zinc-700">
            {/* Subtle Aura */}
            <div className={`absolute -top-10 -right-10 w-32 h-32 rounded-full blur-3xl opacity-20 ${bg.replace('/10', '')} transition-opacity duration-300 group-hover:opacity-30`} />
            
            <div className="flex items-center justify-between relative z-10">
              <span className="text-zinc-400 text-xs font-semibold uppercase tracking-wider">{label}</span>
              <Icon className={`w-4 h-4 ${color}`} />
            </div>
            <p className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-zinc-100 to-zinc-400 relative z-10">
              {value}
            </p>
          </div>
        ))}
      </div>

      {/* Model Info Bar */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
        <p className="text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-4">Forensic Engine Status</p>
        <div className="grid grid-cols-4 gap-4">
          {modelStats.map(({ label, value, icon: Icon }) => (
            <div key={label} className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-zinc-800 flex items-center justify-center flex-shrink-0">
                <Icon className="w-4 h-4 text-zinc-400" />
              </div>
              <div>
                <p className="text-zinc-600 text-xs">{label}</p>
                <p className="text-zinc-200 text-sm font-semibold font-mono">{value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
