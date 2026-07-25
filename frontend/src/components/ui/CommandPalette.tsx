'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Search, LayoutDashboard, Calendar, Settings, Upload, Download, Sparkles, User, Building, BookOpen, X } from 'lucide-react';
import { toast } from '@/hooks/useToast';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

interface CommandItem {
  id: string;
  category: 'Navigation' | 'Quick Actions' | 'Entities';
  title: string;
  description: string;
  icon: React.ReactNode;
  action: () => void;
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const router = useRouter();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (isOpen) {
          onClose();
        } else {
          // Open triggered from parent or direct listener
        }
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const navigateTo = (path: string, label: string) => {
    router.push(path);
    toast.info(`Navigated to ${label}`);
    onClose();
  };

  const items: CommandItem[] = [
    {
      id: 'nav-dashboard',
      category: 'Navigation',
      title: 'Dashboard Overview',
      description: 'View university timetable status, clash summaries, and metrics',
      icon: <LayoutDashboard className="w-4 h-4 text-blue-600 dark:text-blue-400" />,
      action: () => navigateTo('/', 'Dashboard'),
    },
    {
      id: 'nav-schedule',
      category: 'Navigation',
      title: 'Timetable Schedule & Solver',
      description: 'View section grids, clash reports, and run CP-SAT solver',
      icon: <Calendar className="w-4 h-4 text-purple-600 dark:text-purple-400" />,
      action: () => navigateTo('/schedule', 'Schedule View'),
    },
    {
      id: 'nav-configure',
      category: 'Navigation',
      title: 'Data Configuration',
      description: 'Manage 44 Sections, ~80 Faculty, 35 Rooms, and Assignments',
      icon: <Settings className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />,
      action: () => navigateTo('/configure', 'Configure'),
    },
    {
      id: 'nav-import',
      category: 'Navigation',
      title: 'Import Excel Baseline',
      description: 'Upload VFSTR V5 Excel timetable for baseline clash audit',
      icon: <Upload className="w-4 h-4 text-amber-600 dark:text-amber-400" />,
      action: () => navigateTo('/import', 'Import'),
    },
    {
      id: 'nav-export',
      category: 'Navigation',
      title: 'Export Timetable Reports',
      description: 'Download PDF schedules, Excel workbooks, and JSON specs',
      icon: <Download className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />,
      action: () => navigateTo('/export', 'Export'),
    },
    {
      id: 'entity-section',
      category: 'Entities',
      title: 'Section II AIML-A Timetable',
      description: 'Jump to II Year AIML Section A timetable grid',
      icon: <BookOpen className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />,
      action: () => navigateTo('/schedule?section=II_AIML_A', 'II AIML-A Schedule'),
    },
    {
      id: 'entity-room',
      category: 'Entities',
      title: 'Room 604 Computer Lab',
      description: 'View room capacity, schedule allocation, and clashes',
      icon: <Building className="w-4 h-4 text-rose-600 dark:text-rose-400" />,
      action: () => navigateTo('/configure?tab=rooms', 'Rooms Config'),
    },
    {
      id: 'entity-faculty',
      category: 'Entities',
      title: 'Faculty Workload Matrix',
      description: 'Inspect teaching hours for Professors and Assistant Professors',
      icon: <User className="w-4 h-4 text-violet-600 dark:text-violet-400" />,
      action: () => navigateTo('/configure?tab=faculty', 'Faculty Workload'),
    },
    {
      id: 'action-solver',
      category: 'Quick Actions',
      title: 'Trigger CP-SAT Solver',
      description: 'Run OR-Tools constraint solver to resolve 51 baseline clashes',
      icon: <Sparkles className="w-4 h-4 text-amber-500" />,
      action: () => {
        navigateTo('/schedule', 'Solver Workspace');
        toast.info('Click "Run Solver Engine" to initiate generation.');
      },
    },
  ];

  const filteredItems = items.filter(
    (item) =>
      item.title.toLowerCase().includes(query.toLowerCase()) ||
      item.description.toLowerCase().includes(query.toLowerCase()) ||
      item.category.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-slate-900/60 backdrop-blur-sm transition-opacity">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xl max-w-xl w-full overflow-hidden flex flex-col max-h-[80vh] animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center px-4 py-3 border-b border-slate-200 dark:border-slate-800 gap-3">
          <Search className="w-5 h-5 text-slate-400 dark:text-slate-500 flex-shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search sections, faculty, rooms... (Esc to cancel)"
            className="w-full bg-transparent text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none"
            autoFocus
          />
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-md"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {filteredItems.length === 0 ? (
            <div className="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
              No matching commands or entities found for &quot;{query}&quot;
            </div>
          ) : (
            filteredItems.map((item) => (
              <button
                key={item.id}
                onClick={item.action}
                className="w-full flex items-start gap-3 p-3 rounded-lg text-left hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors group cursor-pointer"
              >
                <div className="p-2 rounded-md bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/60 group-hover:border-slate-300 dark:group-hover:border-slate-600 transition-colors">
                  {item.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h5 className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                      {item.title}
                    </h5>
                    <span className="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
                      {item.category}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5">
                    {item.description}
                  </p>
                </div>
              </button>
            ))
          )}
        </div>

        <div className="px-4 py-2 bg-slate-50 dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
          <span>
            Use <kbd className="px-1.5 py-0.5 font-mono bg-slate-200 dark:bg-slate-800 rounded">Ctrl+K</kbd> to toggle anywhere
          </span>
          <span>VFSTR Timetable Engine</span>
        </div>
      </div>
    </div>
  );
}
