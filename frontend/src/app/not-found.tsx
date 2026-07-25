import React from 'react';
import Link from 'next/link';
import { AlertCircle, Home, Calendar } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center p-6 text-center">
      <div className="w-16 h-16 rounded-full bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-800 flex items-center justify-center mb-4 text-red-600 dark:text-red-400">
        <AlertCircle className="w-8 h-8" />
      </div>

      <h1 className="text-3xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">
        404 — Page Not Found
      </h1>
      <p className="text-sm text-slate-500 dark:text-slate-400 mt-2 max-w-md">
        The timetable section, report, or configuration resource you requested does not exist or has been moved.
      </p>

      <div className="flex items-center gap-3 mt-6">
        <Link
          href="/"
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-lg transition-colors"
        >
          <Home className="w-4 h-4" />
          <span>Dashboard</span>
        </Link>

        <Link
          href="/schedule"
          className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-semibold text-xs rounded-lg transition-colors"
        >
          <Calendar className="w-4 h-4" />
          <span>View Timetable</span>
        </Link>
      </div>
    </div>
  );
}
