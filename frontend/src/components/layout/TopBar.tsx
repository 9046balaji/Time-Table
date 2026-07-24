'use client';

import React from 'react';
import { Bell, Sparkles, UserCheck } from 'lucide-react';

export function TopBar() {
  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <h2 className="text-lg font-bold text-slate-900">Department of ACSE Timetable Management</h2>
        <span className="px-2.5 py-1 bg-blue-50 text-blue-700 text-xs font-semibold rounded-full border border-blue-200">
          Semester I • 44 Sections
        </span>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200">
          <Sparkles className="w-3.5 h-3.5 text-purple-600" />
          <span>CP-SAT + GA Engine Ready</span>
        </div>

        <button className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors">
          <Bell className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 border-l border-slate-200 pl-4">
          <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-xs">
            AC
          </div>
          <div className="text-xs">
            <div className="font-semibold text-slate-900">Coordinator</div>
            <div className="text-slate-500">ACSE Dept</div>
          </div>
        </div>
      </div>
    </header>
  );
}
