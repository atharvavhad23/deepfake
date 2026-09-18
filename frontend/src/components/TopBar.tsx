import React from 'react';
import { Bell, Search, Database, Zap, Clock } from 'lucide-react';

export const TopBar: React.FC = () => {
  const now = new Date();

  return (
    <header className="h-14 bg-zinc-950/40 backdrop-blur-xl border-b border-zinc-800/80 flex items-center justify-between px-6 sticky top-0 z-30 shadow-[inset_0_-1px_1px_rgba(255,255,255,0.02)]">
      {/* Left: Search */}
      <div className="flex items-center gap-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-500" />
          <input
            type="text"
            placeholder="Search cases, hashes..."
            className="bg-zinc-900 border border-zinc-700/50 text-zinc-300 text-xs rounded-lg pl-9 pr-4 py-2 w-56 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20 placeholder-zinc-600 font-mono"
          />
        </div>
      </div>

      {/* Center: Metrics */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <Database className="w-3.5 h-3.5 text-emerald-400" />
          <span className="font-mono">1,030 samples trained</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          <span className="font-mono">72.82% model accuracy</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span className="font-mono">{now.toLocaleTimeString('en-US', { hour12: false })}</span>
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-3 py-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-emerald-400 text-xs font-mono font-semibold">SYSTEM ONLINE</span>
        </div>
        <button className="relative w-8 h-8 rounded-lg bg-zinc-800 border border-zinc-700 flex items-center justify-center hover:bg-zinc-700 transition-colors">
          <Bell className="w-4 h-4 text-zinc-400" />
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-cyan-400 rounded-full" />
        </button>
        <div className="w-8 h-8 rounded-lg bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center">
          <span className="text-cyan-400 text-xs font-bold">AA</span>
        </div>
      </div>
    </header>
  );
};
