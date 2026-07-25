'use client';

import React, { useEffect } from 'react';
import { useToast, ToastType } from '@/hooks/useToast';
import { CheckCircle2, AlertTriangle, XCircle, Info, X } from 'lucide-react';

const iconMap: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />,
  error: <XCircle className="w-5 h-5 text-red-600 flex-shrink-0" />,
  warning: <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />,
  info: <Info className="w-5 h-5 text-blue-600 flex-shrink-0" />,
};

const borderMap: Record<ToastType, string> = {
  success: 'border-l-4 border-l-emerald-500 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  error: 'border-l-4 border-l-red-500 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  warning: 'border-l-4 border-l-amber-500 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  info: 'border-l-4 border-l-blue-500 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100',
};

export function ToastContainer() {
  const { toasts, subscribe, dismiss } = useToast();

  useEffect(() => {
    const unsubscribe = subscribe();
    return () => unsubscribe();
  }, [subscribe]);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-3 max-w-sm w-full px-4 sm:px-0 pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`pointer-events-auto flex items-start gap-3 p-4 rounded-lg shadow-xl border border-slate-200 dark:border-slate-700 transition-all duration-300 transform translate-y-0 ${borderMap[toast.type]}`}
        >
          {iconMap[toast.type]}
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-semibold leading-snug">{toast.title}</h4>
            {toast.description && (
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-normal">
                {toast.description}
              </p>
            )}
          </div>
          <button
            onClick={() => dismiss(toast.id)}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors p-1 rounded-md"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
