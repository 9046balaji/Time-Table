'use client';

import { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import {
  Users,
  Building2,
  Clock,
  BookOpen,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Play,
  RotateCw,
  Send,
  Sparkles,
  ArrowRight,
  Sliders,
  Cpu,
  Coffee,
  Check,
  HeartHandshake,
  Server,
  Layers,
  Calendar,
  Grid,
  Search,
  Filter,
  Eye,
  Info
} from 'lucide-react';
import { getApiBaseUrl } from '@/lib/api';
import { TimetableGrid, SlotEntry } from '@/components/timetable/TimetableGrid';

type AgentVoteInfo = {
  agent: string;
  vote: 'APPROVE' | 'REJECT';
  violations: number;
  has_veto_power?: boolean;
  rationale: string;
  metrics?: Record<string, any>;
};

type DialogueEvent = {
  timestamp: number;
  from_agent: string;
  to_agent: string;
  message_type: string;
  content: string;
  payload?: Record<string, any>;
};

const PERIOD_TIMES: Record<number, string> = {
  1: '08:15 – 09:05',
  2: '09:05 – 09:55',
  3: '10:10 – 11:00',
  4: '11:00 – 11:50',
  5: '11:50 – 12:40',
  6: '13:40 – 14:30',
  7: '14:30 – 15:20',
  8: '15:20 – 16:05',
};

const DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];

export function MultiAgentSynthesisWorkspace({
  versionId = 12,
  onSynthesisComplete,
}: {
  versionId?: number;
  onSynthesisComplete?: (entries: any[]) => void;
}) {
  const [loading, setLoading] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [scope, setScope] = useState<string>('ALL');
  const [availableSections, setAvailableSections] = useState<{
    all_sections: string[];
    by_year: Record<string, string[]>;
  }>({ all_sections: [], by_year: {} });
  const [selectedSections, setSelectedSections] = useState<string[]>([]);
  const [userDirective, setUserDirective] = useState<string>('');
  const [activePreviewSection, setActivePreviewSection] = useState<string>('');

  const [auditData, setAuditData] = useState<{
    status: string;
    unanimous: boolean;
    total_slots: number;
    votes: AgentVoteInfo[];
  } | null>(null);

  const [synthesisResult, setSynthesisResult] = useState<{
    status: string;
    unanimous_consensus: boolean;
    runtime_seconds: number;
    total_slots: number;
    summary: string;
    votes: AgentVoteInfo[];
    dialogue_history: DialogueEvent[];
    entries: any[];
  } | null>(null);

  const [activeVersionId, setActiveVersionId] = useState<number>(versionId);
  const [availableVersions, setAvailableVersions] = useState<any[]>([]);
  const [previewEntries, setPreviewEntries] = useState<any[]>([]);
  const [rounds, setRounds] = useState(3);
  const [publishSuccess, setPublishSuccess] = useState<{ text: string; versionId: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const apiBase = getApiBaseUrl();

  // Load available versions on mount
  useEffect(() => {
    async function loadVersions() {
      try {
        const res = await fetch(`${apiBase}/api/v1/timetable/versions`);
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            setAvailableVersions(data);
          }
        }
      } catch {}
    }
    loadVersions();
  }, [apiBase]);

  // Load available sections when activeVersionId changes
  useEffect(() => {
    async function loadSections() {
      try {
        const res = await fetch(`${apiBase}/api/v1/agent/multi-agent/sections?version_id=${activeVersionId}`);
        if (res.ok) {
          const data = await res.json();
          setAvailableSections(data);
          if (data.all_sections?.length > 0) {
            setActivePreviewSection(data.all_sections[0]);
          }
        }
      } catch {}
    }
    loadSections();
  }, [activeVersionId, apiBase]);

  // Load baseline preview entries when activeVersionId changes
  useEffect(() => {
    async function loadBaseline() {
      try {
        const res = await fetch(`${apiBase}/api/v1/timetable?version_id=${activeVersionId}&section_name=ALL`);
        if (res.ok) {
          const data = await res.json();
          setPreviewEntries(data.entries || []);
        }
      } catch {}
    }
    loadBaseline();
  }, [activeVersionId, apiBase]);

  const runAudit = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/api/v1/agent/multi-agent/audit?version_id=${activeVersionId}`);
      if (!res.ok) throw new Error('Multi-Agent audit failed');
      const data = await res.json();
      setAuditData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Audit error');
    } finally {
      setLoading(false);
    }
  };

  const runSynthesis = async (overrideDirective?: string) => {
    setLoading(true);
    setError(null);
    setPublishSuccess(null);
    const directiveToSend = overrideDirective ?? userDirective;
    try {
      const res = await fetch(`${apiBase}/api/v1/agent/multi-agent/synthesize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          version_id: activeVersionId,
          max_rounds: rounds,
          scope,
          target_sections: scope === 'CUSTOM' ? selectedSections : [],
          user_directive: directiveToSend || undefined,
        }),
      });
      if (!res.ok) throw new Error('Collaborative multi-agent synthesis failed');
      const data = await res.json();
      setSynthesisResult(data);
      if (data.entries && data.entries.length > 0) {
        setPreviewEntries(data.entries);
        if (onSynthesisComplete) {
          onSynthesisComplete(data.entries);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Synthesis error');
    } finally {
      setLoading(false);
    }
  };

  const publishTimetable = async () => {
    if (!previewEntries.length) return;
    setPublishing(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/api/v1/agent/multi-agent/publish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          version_label: `MULTI-AGENT-V${Math.floor(Date.now() / 1000).toString().slice(-4)}`,
          entries: previewEntries,
        }),
      });
      if (!res.ok) throw new Error('Publishing multi-agent timetable failed');
      const data = await res.json();
      setPublishSuccess({
        text: `Successfully published as Master Version #${data.version_id} (${data.version_label || 'V-AUTO'})!`,
        versionId: data.version_id,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Publish error');
    } finally {
      setPublishing(false);
    }
  };

  function str(val: any): string {
    return val ? String(val).trim() : '';
  }

  // Filter and map preview entries for the active section grid
  const mappedEntries = useMemo((): SlotEntry[] => {
    if (!activePreviewSection) return [];
    const validTypes = new Set(['L', 'P', 'T', 'LIBRARY', 'IDP', 'MINORS_HONORS', 'SL_EL', 'OE', 'CRT', 'QALR', 'BREAK', 'LUNCH']);
    return previewEntries
      .filter((e) => {
        const sec = str(e.section || e.sectionName).toUpperCase();
        return sec === activePreviewSection.toUpperCase();
      })
      .map((e, idx) => {
        const subj = str(e.subject || e.subjectCode);
        const rawType = str(e.type || e.subjectType || (subj.includes('(P)') ? 'P' : 'L')).toUpperCase();
        const stype = validTypes.has(rawType) ? rawType : 'L';
        const d = str(e.day).toUpperCase();
        const validDays = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'] as const;
        const safeDay = (validDays.includes(d as any) ? d : 'MON') as SlotEntry['day'];
        return {
          id: String(e.id || `${safeDay}_${e.period}_${idx}`),
          day: safeDay,
          period: Number(e.period || 1),
          subjectCode: subj,
          roomCode: str(e.room || e.roomCode),
          facultyName: str(e.faculty || e.facultyName),
          facultyNames: Array.isArray(e.facultyNames) ? e.facultyNames : (e.faculty ? [e.faculty] : []),
          sectionName: str(e.section || e.sectionName || activePreviewSection),
          subjectType: stype as SlotEntry['subjectType'],
          spanPeriods: Number(e.spanPeriods || e.span_periods || (stype === 'P' || subj.includes('(P)') ? 2 : 1)),
          hasClash: Boolean(e.hasClash),
          clashReason: e.clashReason || '',
        };
      });
  }, [activePreviewSection, previewEntries]);

  // 7 Specialized Agent Definitions
  const agentCards = [
    {
      id: 'SectionCurriculumAgent',
      name: 'Section Curriculum Agent',
      role: 'Academic Quotas, Year Levels & Credits',
      rules: ['2nd Yr: 36h + 1 Lib + 1 IIC', '3rd Yr: 45h, 0 Lib', '4th Yr: 39h, SL/EL', 'Minors/Honors WED/THU P7-8'],
      icon: BookOpen,
      badge: 'Curriculum & Quotas',
    },
    {
      id: 'FacultyWorkloadAgent',
      name: 'Faculty Workload Agent',
      role: 'Fatigue, AICTE Limits & Co-Faculty',
      rules: ['Rank Caps: 12h / 14h / 16h', 'Daily Cap: <= 4h/day', 'Continuous: <= 3 periods', 'Zero Double-Booking'],
      icon: Users,
      badge: 'Faculty Welfare',
    },
    {
      id: 'VenueBlockAgent',
      name: 'Venue & Block Agent',
      role: 'Room Matching, GPU Labs & Locality',
      rules: ['Zero Room Collisions', 'Labs in 604-617 & AFTF', 'GPU Labs for DL/CV/MLOP', 'U-Block vs H-Block Transit'],
      icon: Building2,
      badge: 'Infrastructure',
    },
    {
      id: 'TemporalFlowAgent',
      name: 'Temporal Flow Agent',
      role: 'Pacing, Break Guards & Compactness',
      rules: ['Tea Break (09:55-10:10)', 'Lunch Break (12:40-13:40)', 'Lab Span: 2-3 Periods', 'Late P7-8 Cap <= 40%'],
      icon: Clock,
      badge: 'Temporal Pacing',
    },
    {
      id: 'StudentWelfareAgent',
      name: 'Student Welfare Agent',
      role: 'Cognitive Fatigue & Balanced Study',
      rules: ['Max 7 Classes / Day', 'Exam Spacing', 'Lunch Transition Guard', 'Tutorial Protection'],
      icon: HeartHandshake,
      badge: 'Student Experience',
    },
    {
      id: 'LabTechInfraAgent',
      name: 'Lab Tech & Infra Agent',
      role: 'GPU Machines, Licenses & Turnover',
      rules: ['GPU License Monitoring', 'Sat Afternoon Server Maintenance', 'Machine Turnover Buffer', 'High-Load Machine Guard'],
      icon: Server,
      badge: 'Tech & Maintenance',
    },
    {
      id: 'ValidatorAgent',
      name: 'Master Arbiter & Validator',
      role: 'Unanimous Consensus & Ground-Truth Clashes',
      rules: ['Ground-Truth ConflictChecker', 'Absolute VETO Authority', 'Dispute Resolution Repair', 'Zero Hard Clashes Required'],
      icon: ShieldCheck,
      badge: 'Consensus Gate',
    },
  ];

  const currentVotes = synthesisResult?.votes || auditData?.votes || [];

  return (
    <div className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-5">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 text-xs font-bold border border-indigo-200 dark:border-indigo-800 mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            Autonomous 7-Agent Collaborative Society
          </div>
          <h2 className="text-xl md:text-2xl font-black text-slate-900 dark:text-white">
            Autonomous Multi-Agent Timetable Synthesis & Live Grid Studio
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Interact with the agents, specify target sections or natural language instructions, and watch the timetable generate and negotiate live in real time.
          </p>
        </div>

        {/* Global Action Buttons */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-200">
            <Layers className="w-3.5 h-3.5 text-slate-400" />
            <span>Audit Version:</span>
            <select
              value={activeVersionId}
              onChange={(e) => setActiveVersionId(Number(e.target.value))}
              className="bg-transparent font-bold outline-none cursor-pointer max-w-[140px] truncate"
            >
              {availableVersions.length > 0 ? (
                availableVersions.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.version_label || `Version #${v.id}`}
                  </option>
                ))
              ) : (
                <option value={activeVersionId}>Version #{activeVersionId}</option>
              )}
            </select>
          </div>

          <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-200">
            <Sliders className="w-3.5 h-3.5 text-slate-400" />
            <span>Negotiation Rounds:</span>
            <select
              value={rounds}
              onChange={(e) => setRounds(Number(e.target.value))}
              className="bg-transparent font-bold outline-none cursor-pointer"
            >
              <option value={1}>1 Round</option>
              <option value={3}>3 Rounds</option>
              <option value={5}>5 Rounds</option>
            </select>
          </div>

          <button
            type="button"
            disabled={loading}
            onClick={runAudit}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 font-bold text-xs hover:bg-slate-50 transition-all shadow-sm"
          >
            <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Run 7-Agent Audit
          </button>

          <button
            type="button"
            disabled={loading}
            onClick={() => runSynthesis()}
            className="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs transition-all shadow-md shadow-indigo-600/20"
          >
            <Play className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Launch Multi-Agent Synthesis
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-xs font-semibold text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {publishSuccess && (
        <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 text-xs font-bold text-emerald-700 dark:text-emerald-300 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{publishSuccess.text}</span>
          </div>
          <Link
            href={`/schedule?version_id=${publishSuccess.versionId}`}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 text-white font-bold text-xs hover:bg-emerald-700 shrink-0"
          >
            Open in Schedule Workbench &rarr;
          </Link>
        </div>
      )}

      {/* Interactive Directive Command Center */}
      <div className="rounded-2xl border border-indigo-100 dark:border-indigo-900/50 bg-gradient-to-r from-indigo-50/50 via-white to-purple-50/50 dark:from-indigo-950/20 dark:via-slate-900 dark:to-purple-950/20 p-5 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs font-bold text-indigo-900 dark:text-indigo-200">
            <Sparkles className="w-4 h-4 text-indigo-600" />
            <span>Natural Language Agent Command & Section Selector</span>
          </div>

          {/* Scope Selector Tabs */}
          <div className="flex flex-wrap items-center gap-1.5">
            {[
              { id: 'ALL', label: 'All 44 Sections' },
              { id: 'II_YEAR', label: 'II Year' },
              { id: 'III_YEAR', label: 'III Year' },
              { id: 'IV_YEAR', label: 'IV Year' },
              { id: 'CUSTOM', label: 'Custom Sections' },
            ].map((sc) => (
              <button
                key={sc.id}
                type="button"
                onClick={() => setScope(sc.id)}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                  scope === sc.id
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-100'
                }`}
              >
                {sc.label}
              </button>
            ))}
          </div>
        </div>

        {/* Custom Section Multi-Select if scope === 'CUSTOM' */}
        {scope === 'CUSTOM' && (
          <div className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 space-y-2">
            <div className="flex items-center justify-between text-xs font-bold text-slate-700 dark:text-slate-300">
              <span>Select Individual Target Sections:</span>
              <span className="text-[11px] text-indigo-600 font-mono font-normal">
                {selectedSections.length} of {availableSections.all_sections?.length || 0} selected
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto pt-1">
              {(availableSections.all_sections || []).map((sec) => {
                const isSelected = selectedSections.includes(sec);
                return (
                  <button
                    key={sec}
                    type="button"
                    onClick={() => {
                      setSelectedSections((prev) =>
                        isSelected ? prev.filter((s) => s !== sec) : [...prev, sec]
                      );
                    }}
                    className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all border ${
                      isSelected
                        ? 'bg-indigo-600 text-white border-indigo-700 shadow-xs'
                        : 'bg-slate-50 dark:bg-slate-900 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-indigo-400'
                    }`}
                  >
                    {sec}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Natural Language Directive Bar */}
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={userDirective}
              onChange={(e) => setUserDirective(e.target.value)}
              placeholder="Tell the agents what to do (e.g. 'Create timetable for II Year AIML with morning labs and 0 clashes', 'Give Dr. Kalpana morning slots only')..."
              className="w-full pl-4 pr-10 py-3 rounded-xl border border-indigo-200 dark:border-indigo-800 bg-white dark:bg-slate-900 text-xs text-slate-900 dark:text-white placeholder-slate-400 outline-none focus:ring-2 focus:ring-indigo-500 shadow-inner"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  runSynthesis();
                }
              }}
            />
            <Send className="w-4 h-4 text-indigo-500 absolute right-3.5 top-3.5 pointer-events-none" />
          </div>

          <button
            type="button"
            disabled={loading}
            onClick={() => runSynthesis()}
            className="px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-all shadow-md shadow-indigo-600/20 flex items-center gap-2 shrink-0"
          >
            <Play className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Dispatch Directive
          </button>
        </div>

        {/* Quick Suggestion Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px]">
          <span className="text-slate-400 font-semibold flex items-center gap-1">
            <Info className="w-3 h-3" /> Quick Directives:
          </span>
          {[
            'Generate II Year AIML Timetable with Morning Labs',
            'Schedule III Year with GPU Labs in AFTF-12',
            'Enforce Strict AICTE 14h Faculty Workload Cap',
            'Eliminate Student Free Gaps Across All Days',
            'Protect Saturday Afternoon for GPU Maintenance',
          ].map((chip, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setUserDirective(chip);
                runSynthesis(chip);
              }}
              className="px-2.5 py-1 rounded-lg bg-white/80 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 font-medium hover:border-indigo-400 hover:text-indigo-600 transition-all text-[11px]"
            >
              {chip}
            </button>
          ))}
        </div>
      </div>

      {/* 7 Specialized Agent Society Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-7 gap-3">
        {agentCards.map((ag) => {
          const voteInfo = currentVotes.find((v) => v.agent === ag.id);
          const isApprove = voteInfo?.vote === 'APPROVE';
          const Icon = ag.icon;

          return (
            <div
              key={ag.id}
              className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 p-3.5 flex flex-col justify-between hover:border-indigo-300 dark:hover:border-indigo-700 transition-all group"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="p-1.5 rounded-lg bg-white dark:bg-slate-800 shadow-sm border border-slate-100 dark:border-slate-700 text-indigo-600 dark:text-indigo-400">
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  {voteInfo ? (
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                        isApprove
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800'
                          : 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800'
                      }`}
                    >
                      {isApprove ? <CheckCircle2 className="w-2.5 h-2.5" /> : <XCircle className="w-2.5 h-2.5" />}
                      {voteInfo.vote}
                    </span>
                  ) : (
                    <span className="text-[10px] font-semibold text-slate-400">ACTIVE</span>
                  )}
                </div>

                <h3 className="font-bold text-xs text-slate-900 dark:text-white leading-tight">{ag.name}</h3>
                <span className="inline-block mt-0.5 px-1.5 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 text-[9px] font-semibold">
                  {ag.badge}
                </span>

                <div className="space-y-1 mt-2.5">
                  {ag.rules.map((r, i) => (
                    <div key={i} className="flex items-center gap-1 text-[9px] text-slate-600 dark:text-slate-300">
                      <div className="w-1 h-1 rounded-full bg-slate-400 shrink-0" />
                      <span className="truncate">{r}</span>
                    </div>
                  ))}
                </div>
              </div>

              {voteInfo && (
                <div className="mt-3 pt-2 border-t border-slate-200/60 dark:border-slate-700/60 text-[10px]">
                  <div className="flex justify-between font-bold text-slate-600 dark:text-slate-400 mb-0.5">
                    <span>Violations:</span>
                    <span className={voteInfo.violations > 0 ? 'text-red-600 dark:text-red-400' : 'text-emerald-600'}>
                      {voteInfo.violations}
                    </span>
                  </div>
                  <p className="text-slate-500 text-[9px] truncate" title={voteInfo.rationale}>
                    {voteInfo.rationale}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* LIVE WORKING TIMETABLE GRID SECTION */}
      <div className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-200 dark:border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-600 text-white shadow-sm">
              <Grid className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-black text-slate-900 dark:text-white flex items-center gap-2">
                Live Working Timetable Grid
                <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 font-mono">
                  LIVE WORKING • {mappedEntries.length} SLOTS
                </span>
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Institutional week view (Days as Rows × Periods as Columns) with continuous lab merging and faculty allocation legend.
              </p>
            </div>
          </div>

          {/* Section Picker for Grid View */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-slate-600 dark:text-slate-300">Preview Section:</span>
            <select
              value={activePreviewSection}
              onChange={(e) => setActivePreviewSection(e.target.value)}
              className="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs font-bold text-slate-800 dark:text-white outline-none cursor-pointer"
            >
              {(availableSections.all_sections || []).map((sec) => (
                <option key={sec} value={sec}>
                  {sec}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Embedded Canonical TimetableGrid */}
        <TimetableGrid
          sectionName={activePreviewSection || 'II AIML A'}
          entries={mappedEntries}
          showDownloadBtn={true}
        />
      </div>

      {/* Synthesis Results & Negotiation Dialogue Feed */}
      {synthesisResult && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-2">
          {/* Dialogue Log Feed */}
          <div className="lg:col-span-2 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Send className="w-4 h-4 text-indigo-600" />
                Autonomous 7-Agent Dialogue & Negotiation Trace
              </h3>
              <span className="text-xs font-mono text-slate-400">
                {synthesisResult.dialogue_history.length} dialogue events
              </span>
            </div>

            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/40 p-4 max-h-96 overflow-y-auto space-y-2.5 font-mono text-xs">
              {synthesisResult.dialogue_history.map((d, i) => (
                <div
                  key={i}
                  className="p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 shadow-sm space-y-1"
                >
                  <div className="flex items-center justify-between text-[11px]">
                    <div className="flex items-center gap-1.5 font-bold">
                      <span className="text-indigo-600 dark:text-indigo-400">{d.from_agent}</span>
                      <ArrowRight className="w-3 h-3 text-slate-400" />
                      <span className="text-slate-700 dark:text-slate-300">{d.to_agent}</span>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 font-semibold">
                      {d.message_type}
                    </span>
                  </div>
                  <p className="text-slate-700 dark:text-slate-200 font-sans text-xs leading-relaxed">{d.content}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Synthesis Telemetry & Publish Gate */}
          <div className="space-y-4">
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4 shadow-sm">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                  Consensus Gate Status
                </h4>
                <span
                  className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                    synthesisResult.unanimous_consensus
                      ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300'
                      : 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300'
                  }`}
                >
                  {synthesisResult.status}
                </span>
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800">
                  <span className="text-slate-500">Unanimous Consensus:</span>
                  <span className="font-bold text-slate-900 dark:text-white">
                    {synthesisResult.unanimous_consensus ? 'YES (7/7 Approved)' : 'HELD (Needs Review)'}
                  </span>
                </div>
                <div className="flex justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800">
                  <span className="text-slate-500">Synthesis Runtime:</span>
                  <span className="font-bold text-indigo-600 dark:text-indigo-400 font-mono">
                    {synthesisResult.runtime_seconds}s
                  </span>
                </div>
                <div className="flex justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800">
                  <span className="text-slate-500">Total Timetable Slots:</span>
                  <span className="font-bold text-slate-900 dark:text-white font-mono">
                    {synthesisResult.total_slots}
                  </span>
                </div>
              </div>

              <button
                type="button"
                disabled={publishing}
                onClick={publishTimetable}
                className="w-full py-3 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition-all shadow-md shadow-emerald-600/20 flex items-center justify-center gap-2"
              >
                <Check className={`w-4 h-4 ${publishing ? 'animate-spin' : ''}`} />
                Publish as Official Timetable Version
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
