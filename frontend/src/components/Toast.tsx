import React, { useEffect, useState } from 'react';
import { CheckCircle2, AlertTriangle, Download, X } from 'lucide-react';

interface Toast {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
  subtitle?: string;
}

let globalToastFn: ((toast: Omit<Toast, 'id'>) => void) | null = null;

export function showToast(toast: Omit<Toast, 'id'>) {
  globalToastFn?.(toast);
}

export const ToastContainer: React.FC = () => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    globalToastFn = (t) => {
      const id = Date.now().toString();
      setToasts((prev) => [...prev, { ...t, id }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((toast) => toast.id !== id));
      }, 4000);
    };
    return () => { globalToastFn = null; };
  }, []);

  const remove = (id: string) => setToasts((prev) => prev.filter((t) => t.id !== id));

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`flex items-start gap-3 px-4 py-3 rounded-xl border shadow-2xl animate-slide-up min-w-[280px] max-w-sm ${
            toast.type === 'success' ? 'bg-emerald-950 border-emerald-500/40' :
            toast.type === 'error' ? 'bg-red-950 border-red-500/40' :
            'bg-zinc-900 border-zinc-700'
          }`}
        >
          <div className="flex-shrink-0 mt-0.5">
            {toast.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
            {toast.type === 'error' && <AlertTriangle className="w-4 h-4 text-red-400" />}
            {toast.type === 'info' && <Download className="w-4 h-4 text-cyan-400" />}
          </div>
          <div className="flex-1 min-w-0">
            <p className={`text-sm font-semibold ${toast.type === 'success' ? 'text-emerald-300' : toast.type === 'error' ? 'text-red-300' : 'text-zinc-200'}`}>
              {toast.message}
            </p>
            {toast.subtitle && <p className="text-xs text-zinc-500 mt-0.5">{toast.subtitle}</p>}
          </div>
          <button onClick={() => remove(toast.id)} className="flex-shrink-0 text-zinc-600 hover:text-zinc-400 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
};
