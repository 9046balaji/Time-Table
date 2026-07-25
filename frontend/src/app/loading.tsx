import React from 'react';

export default function Loading() {
  return (
    <div className="space-y-6 animate-pulse p-2">
      <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
        <div className="space-y-2">
          <div className="h-6 w-48 bg-slate-200 dark:bg-slate-800 rounded-md" />
          <div className="h-4 w-72 bg-slate-100 dark:bg-slate-800/60 rounded-md" />
        </div>
        <div className="h-9 w-32 bg-slate-200 dark:bg-slate-800 rounded-lg" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-24 bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-800 rounded-xl p-4 space-y-3"
          >
            <div className="h-4 w-24 bg-slate-200 dark:bg-slate-700 rounded" />
            <div className="h-8 w-16 bg-slate-300 dark:bg-slate-600 rounded" />
          </div>
        ))}
      </div>

      <div className="h-96 bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-800 rounded-xl p-4" />
    </div>
  );
}
