'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import {
  Search,
  LayoutDashboard,
  Calendar,
  Settings,
  Upload,
  Download,
  Sparkles,
  User,
  Building,
  BookOpen,
  X,
  Bot,
  Activity,
  Layers,
  ArrowRight,
  ShieldCheck,
  Zap
} from 'lucide-react';
import { timetableApi } from '@/lib/api';
import { toast } from '@/hooks/useToast';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

interface CommandItem {
  id: string;
  category: 'Navigation' | 'Sections' | 'Faculty' | 'Venues & Labs' | 'Curriculum' | 'AI Actions';
  title: string;
  description: string;
  icon: React.ReactNode;
  action: () => void;
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const router = useRouter();

  // Dynamic Live DB entities
  const [sections, setSections] = useState<any[]>([]);
  const [faculty, setFaculty] = useState<any[]>([]);
  const [rooms, setRooms] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Fetch live PostgreSQL entities on open
  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      Promise.all([
        timetableApi.getSections().catch(() => ({ data: [] })),
        timetableApi.getFaculty().catch(() => ({ data: [] })),
        timetableApi.getRooms().catch(() => ({ data: [] })),
        timetableApi.getSubjects().catch(() => ({ data: [] })),
      ]).then(([secRes, facRes, roomRes, subRes]) => {
        setSections(Array.isArray(secRes.data) ? secRes.data : ((secRes.data as any)?.items || []));
        setFaculty(Array.isArray(facRes.data) ? facRes.data : ((facRes.data as any)?.items || []));
        setRooms(Array.isArray(roomRes.data) ? roomRes.data : ((roomRes.data as any)?.items || []));
        setSubjects(Array.isArray(subRes.data) ? subRes.data : ((subRes.data as any)?.items || []));
      }).finally(() => setLoading(false));
    }
  }, [isOpen]);

  const navigateTo = (path: string, label: string) => {
    router.push(path);
    toast.info(`Navigated to ${label}`);
    onClose();
  };

  // Static Navigation & AI Actions
  const staticItems: CommandItem[] = [
    {
      id: 'nav-dashboard',
      category: 'Navigation',
      title: 'Dashboard Overview',
      description: 'View university timetable operations, live metrics, and dataset benchmarks',
      icon: <LayoutDashboard className="w-4 h-4 text-blue-600 dark:text-blue-400" />,
      action: () => navigateTo('/', 'Dashboard'),
    },
    {
      id: 'nav-ai-scheduler',
      category: 'Navigation',
      title: 'Autonomous AI Timetable Generator',
      description: 'Run OR-Tools CP-SAT math solver to auto-generate 0-clash master schedules',
      icon: <Sparkles className="w-4 h-4 text-purple-600 dark:text-purple-400" />,
      action: () => navigateTo('/ai-scheduler', 'AI Auto-Scheduler'),
    },
    {
      id: 'nav-schedule',
      category: 'Navigation',
      title: 'Timetable Grid Workbench',
      description: 'Interactive section grids, side-by-side comparison, and faculty view',
      icon: <Calendar className="w-4 h-4 text-blue-600 dark:text-blue-400" />,
      action: () => navigateTo('/schedule', 'Schedule Workbench'),
    },
    {
      id: 'nav-configure',
      category: 'Navigation',
      title: 'Master Data Profiler Hub',
      description: 'Manage Faculty Dossiers, Venue Specifications, and Curriculum Subjects',
      icon: <Settings className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />,
      action: () => navigateTo('/configure', 'Data Management'),
    },
    {
      id: 'nav-testing',
      category: 'Navigation',
      title: 'Multi-Branch Tested Cohorts Hub',
      description: 'Audit 10-section multi-branch cohorts (AIML, Core, DS, CS) with 0 clashes',
      icon: <Activity className="w-4 h-4 text-teal-600 dark:text-teal-400" />,
      action: () => navigateTo('/testing', 'Tested Cohorts Hub'),
    },
    {
      id: 'nav-import',
      category: 'Navigation',
      title: 'Excel Import Wizard',
      description: 'Upload new Excel revisions or audit V5 baseline dataset',
      icon: <Upload className="w-4 h-4 text-amber-600 dark:text-amber-400" />,
      action: () => navigateTo('/import', 'Import Wizard'),
    },
    {
      id: 'nav-export',
      category: 'Navigation',
      title: 'Multi-Format Export Hub',
      description: 'Generate section PDFs, faculty iCal (.ics) feeds, and Excel workbooks',
      icon: <Download className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />,
      action: () => navigateTo('/export', 'Export Hub'),
    },
    {
      id: 'action-solver',
      category: 'AI Actions',
      title: 'Execute CP-SAT AI Solver Engine',
      description: 'Run OR-Tools parallel portfolio engine to generate 100% clash-free timetable',
      icon: <Zap className="w-4 h-4 text-amber-500" />,
      action: () => navigateTo('/schedule?action=solve', 'AI Solver'),
    },
  ];

  // Dynamic Section items
  const sectionItems: CommandItem[] = useMemo(() => {
    const defaultSecs = [
      { name: "II AIML-A", year: "II Year", branch: "AIML" },
      { name: "II AIML-B", year: "II Year", branch: "AIML" },
      { name: "III AIML-A", year: "III Year", branch: "AIML" },
      { name: "IV AIML-A", year: "IV Year", branch: "AIML" },
      { name: "II CS-A", year: "II Year", branch: "CS" },
      { name: "II DS-A", year: "II Year", branch: "DS" },
    ];
    const source = sections.length > 0 ? sections : defaultSecs;
    return source.slice(0, 15).map((s: any, idx: number) => {
      const sName = typeof s === 'string' ? s : (s.name || s.section_name || `Section ${idx+1}`);
      return {
        id: `sec-${idx}`,
        category: 'Sections',
        title: `Section ${sName} Timetable Grid`,
        description: `Jump directly to ${sName} weekly schedule matrix`,
        icon: <BookOpen className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />,
        action: () => navigateTo(`/schedule?section=${encodeURIComponent(sName)}`, `${sName} Schedule`),
      };
    });
  }, [sections]);

  // Dynamic Faculty items
  const facultyItems: CommandItem[] = useMemo(() => {
    return faculty.slice(0, 15).map((f: any) => ({
      id: `fac-${f.id}`,
      category: 'Faculty',
      title: `Faculty: ${f.name}`,
      description: `${f.designation || 'Instructor'} • ${f.employee_id || `VF-${f.id}`} • ${f.phone || 'ACSE Dept'}`,
      icon: <User className="w-4 h-4 text-violet-600 dark:text-violet-400" />,
      action: () => navigateTo(`/configure?tab=faculty&search=${encodeURIComponent(f.name)}`, `Faculty ${f.name}`),
    }));
  }, [faculty]);

  // Dynamic Room items
  const roomItems: CommandItem[] = useMemo(() => {
    return rooms.slice(0, 15).map((r: any) => ({
      id: `room-${r.id}`,
      category: 'Venues & Labs',
      title: `Venue: Room ${r.code}`,
      description: `${r.type || r.room_type || 'Classroom'} • Capacity ${r.capacity || 60} Seats • Floor ${r.floor || 6}`,
      icon: <Building className="w-4 h-4 text-rose-600 dark:text-rose-400" />,
      action: () => navigateTo(`/configure?tab=rooms&search=${encodeURIComponent(r.code)}`, `Venue ${r.code}`),
    }));
  }, [rooms]);

  // Dynamic Subject items
  const subjectItems: CommandItem[] = useMemo(() => {
    return subjects.slice(0, 15).map((sub: any) => ({
      id: `sub-${sub.id}`,
      category: 'Curriculum',
      title: `Course: ${sub.code}`,
      description: `${sub.full_name || 'Subject Course'} • L:${sub.lecture_hours || 3} T:${sub.tutorial_hours || 0} P:${sub.lab_hours || 0}`,
      icon: <BookOpen className="w-4 h-4 text-amber-600 dark:text-amber-400" />,
      action: () => navigateTo(`/configure?tab=subjects&search=${encodeURIComponent(sub.code)}`, `Subject ${sub.code}`),
    }));
  }, [subjects]);

  // Combine all searchable command items
  const allItems = useMemo(() => {
    return [...staticItems, ...sectionItems, ...facultyItems, ...roomItems, ...subjectItems];
  }, [sectionItems, facultyItems, roomItems, subjectItems]);

  const filteredItems = useMemo(() => {
    if (!query.trim()) return allItems.slice(0, 12);
    const q = query.toLowerCase();
    return allItems.filter(
      (item) =>
        item.title.toLowerCase().includes(q) ||
        item.description.toLowerCase().includes(q) ||
        item.category.toLowerCase().includes(q)
    );
  }, [allItems, query]);

  // Keyboard Navigation Listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
      if (isOpen && filteredItems.length > 0) {
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          setSelectedIndex((prev) => (prev + 1) % filteredItems.length);
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          setSelectedIndex((prev) => (prev - 1 + filteredItems.length) % filteredItems.length);
        } else if (e.key === 'Enter') {
          e.preventDefault();
          if (filteredItems[selectedIndex]) {
            filteredItems[selectedIndex].action();
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, filteredItems, selectedIndex]);

  // Reset selected index on query change
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 px-4 bg-slate-950/70 backdrop-blur-md transition-opacity">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl max-w-2xl w-full overflow-hidden flex flex-col max-h-[85vh] animate-in fade-in zoom-in-95 duration-150">

        {/* Input Header */}
        <div className="flex items-center px-5 py-4 border-b border-slate-200 dark:border-slate-800 gap-3">
          <Search className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search sections (II AIML-A), faculty, rooms (604), courses (22CS406)..."
            className="w-full bg-transparent text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none font-medium"
            autoFocus
          />
          {query && (
            <button onClick={() => setQuery('')} className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-white font-bold text-xs">
              ✕
            </button>
          )}
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-white rounded-md text-xs font-bold"
          >
            Esc
          </button>
        </div>

        {/* Results Body */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {filteredItems.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-500 dark:text-slate-400">
              No matching commands or entities found for &quot;{query}&quot;
            </div>
          ) : (
            filteredItems.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <button
                  key={item.id}
                  onClick={item.action}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`w-full flex items-center justify-between p-3 rounded-2xl text-left transition-all cursor-pointer border ${
                    isSelected
                      ? 'bg-blue-50 dark:bg-blue-950/70 border-blue-300 dark:border-blue-700 shadow-sm'
                      : 'bg-white dark:bg-slate-900 border-transparent hover:bg-slate-50 dark:hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={`p-2 rounded-xl border ${isSelected ? 'bg-white dark:bg-slate-900 border-blue-200 dark:border-blue-700' : 'bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700'}`}>
                      {item.icon}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <h5 className="text-xs font-extrabold text-slate-900 dark:text-slate-100 truncate">
                          {item.title}
                        </h5>
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate mt-0.5 font-medium">
                        {item.description}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 ml-3">
                    <span className="text-[10px] uppercase font-black tracking-wider text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-md border border-slate-200 dark:border-slate-700">
                      {item.category}
                    </span>
                    {isSelected && <ArrowRight className="w-4 h-4 text-blue-600 dark:text-blue-400" />}
                  </div>
                </button>
              );
            })
          )}
        </div>

        {/* Footer info bar */}
        <div className="px-5 py-3 bg-slate-50 dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <div className="flex items-center gap-3">
            <span>Press <kbd className="px-1.5 py-0.5 font-mono text-[10px] bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded font-bold">↑</kbd> <kbd className="px-1.5 py-0.5 font-mono text-[10px] bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded font-bold">↓</kbd> to navigate</span>
            <span><kbd className="px-1.5 py-0.5 font-mono text-[10px] bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded font-bold">Enter</kbd> to select</span>
          </div>
          <span className="font-bold text-blue-600 dark:text-blue-400">VFSTR ACSE Engine</span>
        </div>
      </div>
    </div>
  );
}
