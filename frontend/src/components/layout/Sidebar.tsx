'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Calendar, Upload, Settings, Download, Cpu } from 'lucide-react';

const NAV_ITEMS = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/schedule', label: 'Timetable Grid', icon: Calendar },
  { href: '/import', label: 'Import Excel', icon: Upload },
  { href: '/configure', label: 'Data Management', icon: Settings },
  { href: '/export', label: 'Export Options', icon: Download },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-slate-900 text-white min-h-screen p-4 flex flex-col justify-between">
      <div>
        <div className="flex items-center gap-3 px-3 py-4 border-b border-slate-800 mb-6">
          <div className="p-2 bg-blue-600 rounded-lg">
            <Cpu className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-sm leading-tight">VFSTR Scheduler</h1>
            <p className="text-xs text-slate-400">ACSE Dept • AY 2026-27</p>
          </div>
        </div>

        <nav className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="p-3 bg-slate-800/60 rounded-xl border border-slate-700/50">
        <div className="text-xs text-slate-400 mb-1">Baseline Status</div>
        <div className="flex items-center justify-between text-sm font-semibold text-red-400">
          <span>51 Room Clashes</span>
          <span className="px-2 py-0.5 bg-red-500/20 text-red-300 text-[10px] rounded font-bold">V5 Baseline</span>
        </div>
      </div>
    </aside>
  );
}
