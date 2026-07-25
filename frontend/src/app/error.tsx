'use client';

import React, { useEffect } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Unhandled Timetable Application Error:', error);
  }, [error]);

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center p-6 text-center">
      <div className="w-16 h-16 rounded-full bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-800 flex items-center justify-center mb-4 text-amber-600 dark:text-amber-400">
        <AlertTriangle className="w-8 h-8" />
      </div>

      <h1 className="text-2xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">
        Application Error
      </h1>
      <p className="text-sm text-slate-500 dark:text-slate-400 mt-2 max-w-md">
        An unexpected error occurred while rendering the timetable view.
      </p>

      {error.message && (
        <pre className="mt-3 p-3 text-left text-xs bg-slate-100 dark:bg-slate-900 text-slate-700 dark:text-slate-300 font-mono rounded-lg max-w-lg overflow-x-auto border border-slate-200 dark:border-slate-800">
          {error.message}
        </pre>
      )}

      <button
        onClick={() => reset()}
        className="mt-6 flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-lg transition-colors cursor-pointer"
      >
        <RefreshCw className="w-4 h-4" />
        <span>Try Again</span>
      </button>
    </div>
  );
}
