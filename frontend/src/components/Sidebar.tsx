import React from 'react';
import {
  LayoutDashboard,
  FolderOpen,
  FileText,
  Settings,
  Shield,
  Activity,
  Cpu,
  Wifi,
  ChevronRight,
} from 'lucide-react';
import type { NavSection } from '../types';

interface SidebarProps {
  activeSection: NavSection;
  onSectionChange: (s: NavSection) => void;
}

const navItems: { id: NavSection; label: string; icon: React.ElementType; badge?: number }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'cases', label: 'Active Cases', icon: FolderOpen, badge: 3 },
  { id: 'reports', label: 'Forensic Reports', icon: FileText },
  { id: 'settings', label: 'Settings', icon: Settings },
];

const systemStatus = [
  { label: 'ML Engine', icon: Cpu, status: 'online', color: 'text-emerald-400' },
  { label: 'API Gateway', icon: Wifi, status: 'online', color: 'text-emerald-400' },
  { label: 'Chain Monitor', icon: Activity, status: 'active', color: 'text-cyan-400' },
];

export const Sidebar: React.FC<SidebarProps> = ({ activeSection, onSectionChange }) => {
  return (
    <aside className="w-64 flex-shrink-0 bg-zinc-950/40 backdrop-blur-xl border-r border-zinc-800/80 flex flex-col h-screen sticky top-0 shadow-[inset_-1px_0_1px_rgba(255,255,255,0.02)]">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-zinc-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
            <Shield className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h1 className="text-white font-bold text-sm tracking-wide">NEXASHIELD</h1>
            <p className="text-zinc-500 text-xs font-mono">FORENSIC SUITE v3.1</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        <p className="text-zinc-600 text-xs font-semibold uppercase tracking-widest px-3 mb-3">
          Navigation
        </p>
        {navItems.map(({ id, label, icon: Icon, badge }) => {
          const isActive = activeSection === id;
          return (
            <button
              key={id}
              onClick={() => onSectionChange(id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 group ${
                isActive
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-[0_0_12px_rgba(34,211,238,0.1)]'
                  : 'text-zinc-400 border border-transparent hover:border-zinc-700 hover:bg-zinc-800/80 hover:scale-[1.01]'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-zinc-500 group-hover:text-zinc-300'}`} />
                {label}
              </div>
              <div className="flex items-center gap-2">
                {badge && (
                  <span className="bg-cyan-500/20 text-cyan-400 text-xs px-1.5 py-0.5 rounded-full font-mono">
                    {badge}
                  </span>
                )}
                {isActive && <ChevronRight className="w-3 h-3 text-cyan-500" />}
              </div>
            </button>
          );
        })}
      </nav>

      {/* System Status */}
      <div className="px-4 py-4 border-t border-zinc-800 space-y-2">
        <p className="text-zinc-600 text-xs font-semibold uppercase tracking-widest px-1 mb-3">
          System Status
        </p>
        {systemStatus.map(({ label, icon: Icon, status, color }) => (
          <div key={label} className="flex items-center justify-between px-2 py-1">
            <div className="flex items-center gap-2">
              <Icon className={`w-3.5 h-3.5 ${color}`} />
              <span className="text-zinc-400 text-xs">{label}</span>
            </div>
            <span className={`text-xs font-mono ${color} uppercase`}>{status}</span>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="px-5 py-3 border-t border-zinc-800">
        <p className="text-zinc-600 text-xs font-mono">Build 2026.07.11-PROD</p>
        <p className="text-zinc-700 text-xs">© NexaShield Forensics</p>
      </div>
    </aside>
  );
};
