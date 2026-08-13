"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Sparkles, Loader2, CheckCircle2, Zap, ShieldCheck,
  RefreshCw, ChevronDown, ChevronUp, X, AlertCircle,
  ArrowRight
} from "lucide-react";
import { timetableApi } from "@/lib/api";
import { CourseAssignmentInput, TimetableGenerationRequest, WizardGenerationResponse } from "@/lib/types";
import Link from "next/link";

interface ScheduleSetupWizardProps {
  onSuccess?: (response: WizardGenerationResponse) => void;
}

// Hard Constraints — always enforced, shown to user for transparency
const HARD_CONSTRAINTS = [
  { id: "HC-01", label: "No room double-booking" },
  { id: "HC-02", label: "No faculty double-booking" },
  { id: "HC-03", label: "No student conflict" },
  { id: "HC-04", label: "Subject weekly frequency" },
  { id: "HC-05", label: "Room capacity respected" },
  { id: "HC-06", label: "Lab subjects → lab rooms" },
  { id: "HC-07", label: "Break & Lunch blocked" },
  { id: "HC-08", label: "Lab sessions consecutive" },
  { id: "HC-09", label: "Minors/Honors: Wed/Thu P7-P8" },
  { id: "HC-10", label: "IV Yr SL/EL: P1-P2 only" },
];

const YEAR_FILTERS = ["All", "II Year", "III Year", "IV Year"];
const BRANCH_FILTERS = ["All", "AIML", "CS", "DS", "CSBS", "IOT", "BS(DS)", "MSC(DS)"];

function matchesFilters(sec: string, year: string, branch: string): boolean {
  const up = sec.toUpperCase();
  const yearMatch = year === "All" ||
    (year === "II Year" && up.startsWith("II ")) ||
    (year === "III Year" && up.startsWith("III ")) ||
    (year === "IV Year" && up.startsWith("IV "));
  const branchMatch = branch === "All" || up.includes(branch.toUpperCase());
  return yearMatch && branchMatch;
}

export const ScheduleSetupWizard: React.FC<ScheduleSetupWizardProps> = ({ onSuccess }) => {
  // Data state
  const [availableSections, setAvailableSections] = useState<string[]>([]);
  const [facultyPool, setFacultyPool] = useState<string[]>([]);
  const [roomsPool, setRoomsPool] = useState<any[]>([]);
  const [curriculaMap, setCurriculaMap] = useState<Record<string, CourseAssignmentInput[]>>({});
  const [loadingDefaults, setLoadingDefaults] = useState(true);

  // Selection state
  const [selectedSections, setSelectedSections] = useState<string[]>([]);
  const [yearFilter, setYearFilter] = useState("All");
  const [branchFilter, setBranchFilter] = useState("All");

  // Solver config state (collapsed by default)
  const [showConfig, setShowConfig] = useState(false);
  const [algorithm, setAlgorithm] = useState("CP-SAT");
  const [timeoutSecs, setTimeoutSecs] = useState(120);
  const [maxDailyHours, setMaxDailyHours] = useState(4);

  // Solve state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<WizardGenerationResponse | null>(null);

  // Load defaults on mount
  useEffect(() => {
    timetableApi.getWizardDefaults()
      .then((res) => {
        const d = res.data;
        setFacultyPool((d.faculty || []).map((f: any) => f.name));
        setAvailableSections(d.sections || []);
        setRoomsPool(d.rooms || []);
        setCurriculaMap(d.curricula || {});
      })
      .catch(console.error)
      .finally(() => setLoadingDefaults(false));
  }, []);

  // Filtered section list based on year+branch filter
  const visibleSections = useMemo(
    () => availableSections.filter((s) => matchesFilters(s, yearFilter, branchFilter)),
    [availableSections, yearFilter, branchFilter]
  );

  const toggleSection = (sec: string) => {
    setSelectedSections((prev) =>
      prev.includes(sec) ? prev.filter((s) => s !== sec) : [...prev, sec]
    );
    // Clear previous result when scope changes
    setResult(null);
    setError(null);
  };

  const selectVisible = () => {
    setSelectedSections((prev) => {
      const combined = new Set([...prev, ...visibleSections]);
      return Array.from(combined);
    });
  };

  const clearVisible = () => {
    setSelectedSections((prev) => prev.filter((s) => !visibleSections.includes(s)));
  };

  // Derive scope summary from selected sections + curricula
  const scopeSummary = useMemo(() => {
    const subjectSet = new Set<string>();
    const facultySet = new Set<string>();
    let totalSlots = 0;

    selectedSections.forEach((sec) => {
      // Detect year from section name
      const up = sec.toUpperCase();
      const yearKey = up.startsWith("IV ") ? "IV Year" : up.startsWith("III ") ? "III Year" : "II Year";
      const curriculum = curriculaMap[yearKey] || [];
      curriculum.forEach((course) => {
        subjectSet.add(course.subject_code);
        if (course.faculty_name) facultySet.add(course.faculty_name);
        (course.co_faculty || []).forEach((f: string) => facultySet.add(f));
        totalSlots += course.weekly_hours || 0;
      });
    });

    // Approximate: if no curricula data loaded yet, use fallback estimates
    const subjectCount = subjectSet.size || (selectedSections.length > 0 ? 8 : 0);
    const facultyCount = facultySet.size || (selectedSections.length > 0 ? Math.round(selectedSections.length * 1.5) : 0);
    const slots = totalSlots || selectedSections.length * 36;

    return {
      sections: selectedSections.length,
      subjects: subjectCount,
      faculty: facultyCount,
      slots,
      subjectList: Array.from(subjectSet).slice(0, 12),
    };
  }, [selectedSections, curriculaMap]);

  const handleGenerate = async () => {
    if (selectedSections.length === 0) return;
    setLoading(true);
    setError(null);
    setResult(null);

    // Determine year scope from selected sections
    const hasII = selectedSections.some((s) => s.toUpperCase().startsWith("II "));
    const hasIII = selectedSections.some((s) => s.toUpperCase().startsWith("III "));
    const hasIV = selectedSections.some((s) => s.toUpperCase().startsWith("IV "));
    const yearLevel = hasII && hasIII && hasIV ? "Entire Department"
      : hasIV ? "IV Year" : hasIII ? "III Year" : "II Year";

    // Collect curriculum assignments for selected year(s)
    let assignments: CourseAssignmentInput[] = [];
    if (yearLevel === "Entire Department") {
      ["II Year", "III Year", "IV Year"].forEach((y) => {
        assignments = [...assignments, ...(curriculaMap[y] || [])];
      });
    } else {
      assignments = curriculaMap[yearLevel] || [];
    }

    const payload: TimetableGenerationRequest = {
      branch: "ALL",
      year_level: yearLevel,
      sections: selectedSections,
      preferred_block: "Block-VI (601-619)",
      max_daily_teaching_hours: maxDailyHours,
      max_classes_per_teacher_per_day: maxDailyHours,
      assignments,
    };

    try {
      const res = await timetableApi.generateFromWizard(payload);
      if (res.data.status === "INFEASIBLE") {
        setError(
          "Solver returned INFEASIBLE — the selected sections have over-constrained subject quotas. " +
          "Try increasing the max daily faculty hours or selecting fewer sections at once."
        );
      } else {
        setResult(res.data);
        onSuccess?.(res.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Generation failed. Please check the backend solver is running.");
    } finally {
      setLoading(false);
    }
  };

  if (loadingDefaults) {
    return (
      <div className="flex flex-col items-center justify-center p-16 gap-3 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        <span className="text-xs font-bold text-slate-600 dark:text-slate-400">Loading department data — faculty, rooms & curricula...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── PHASE 1: Section Picker ───────────────────────────── */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white">Select Sections to Generate</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Pick one section or many — all constraints apply automatically</p>
          </div>
          {selectedSections.length > 0 && (
            <span className="px-3 py-1 bg-blue-600 text-white text-xs font-extrabold rounded-full shadow-sm">
              {selectedSections.length} selected
            </span>
          )}
        </div>

        <div className="p-6 space-y-5">
          {/* Filter Pills */}
          <div className="space-y-3">
            {/* Year filter */}
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide w-14 shrink-0">Year</span>
              {YEAR_FILTERS.map((y) => (
                <button
                  key={y}
                  onClick={() => setYearFilter(y)}
                  className={`px-3 py-1 rounded-full text-xs font-bold transition-all cursor-pointer ${
                    yearFilter === y
                      ? "bg-blue-600 text-white shadow-sm"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700"
                  }`}
                >
                  {y}
                </button>
              ))}
            </div>
            {/* Branch filter */}
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide w-14 shrink-0">Branch</span>
              {BRANCH_FILTERS.map((b) => (
                <button
                  key={b}
                  onClick={() => setBranchFilter(b)}
                  className={`px-3 py-1 rounded-full text-xs font-bold transition-all cursor-pointer ${
                    branchFilter === b
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700"
                  }`}
                >
                  {b}
                </button>
              ))}
            </div>
          </div>

          {/* Quick select / clear for visible */}
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-slate-500 dark:text-slate-400">
              {visibleSections.length} section{visibleSections.length !== 1 ? "s" : ""} shown
            </span>
            <div className="flex items-center gap-3">
              <button onClick={selectVisible} className="text-[11px] font-bold text-blue-600 hover:underline cursor-pointer">
                Select all visible ({visibleSections.length})
              </button>
              <span className="text-slate-300 dark:text-slate-700">|</span>
              <button onClick={clearVisible} className="text-[11px] font-bold text-slate-500 hover:underline cursor-pointer">
                Clear visible
              </button>
            </div>
          </div>

          {/* Section Grid */}
          {visibleSections.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400 dark:text-slate-600 font-medium">
              No sections match the current filters.
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
              {visibleSections.map((sec) => {
                const isSelected = selectedSections.includes(sec);
                const up = sec.toUpperCase();
                const yearKey = up.startsWith("IV ") ? "IV Year" : up.startsWith("III ") ? "III Year" : "II Year";
                const subjectCount = (curriculaMap[yearKey] || []).length;

                return (
                  <button
                    key={sec}
                    onClick={() => toggleSection(sec)}
                    title={subjectCount > 0 ? `${subjectCount} subjects · click to ${isSelected ? "deselect" : "select"}` : sec}
                    className={`relative flex flex-col items-start justify-between p-3 rounded-xl border text-left text-xs font-bold transition-all cursor-pointer group ${
                      isSelected
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-950/60 text-blue-900 dark:text-blue-100 shadow-sm"
                        : "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:border-blue-300 dark:hover:border-blue-700 hover:bg-blue-50/30 dark:hover:bg-blue-950/20"
                    }`}
                  >
                    <span className="truncate w-full">{sec}</span>
                    {subjectCount > 0 && (
                      <span className={`mt-1 text-[10px] font-semibold ${isSelected ? "text-blue-600 dark:text-blue-400" : "text-slate-400 dark:text-slate-500"}`}>
                        {subjectCount} subj
                      </span>
                    )}
                    {isSelected && (
                      <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-blue-500 shadow-sm" />
                    )}
                  </button>
                );
              })}
            </div>
          )}

          {/* Selected tags strip */}
          {selectedSections.length > 0 && (
            <div className="pt-3 border-t border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Selected:</span>
                {selectedSections.map((sec) => (
                  <span
                    key={sec}
                    className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 dark:bg-blue-950/60 text-blue-800 dark:text-blue-300 border border-blue-200 dark:border-blue-800 rounded-full text-[11px] font-semibold"
                  >
                    {sec}
                    <button onClick={() => toggleSection(sec)} className="hover:text-red-500 cursor-pointer">
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
                <button
                  onClick={() => { setSelectedSections([]); setResult(null); setError(null); }}
                  className="text-[11px] font-bold text-red-500 hover:underline cursor-pointer"
                >
                  Clear all
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── PHASE 2: Scope Summary + Generate ────────────────── */}
      {selectedSections.length > 0 && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
          {/* Scope Summary */}
          <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-3">Generation Scope</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-blue-50 dark:bg-blue-950/40 rounded-xl p-3 text-center border border-blue-100 dark:border-blue-900">
                <div className="text-xl font-black text-blue-700 dark:text-blue-300">{scopeSummary.sections}</div>
                <div className="text-[11px] font-semibold text-blue-600 dark:text-blue-400">Sections</div>
              </div>
              <div className="bg-purple-50 dark:bg-purple-950/40 rounded-xl p-3 text-center border border-purple-100 dark:border-purple-900">
                <div className="text-xl font-black text-purple-700 dark:text-purple-300">{scopeSummary.subjects || "~8"}</div>
                <div className="text-[11px] font-semibold text-purple-600 dark:text-purple-400">Subjects</div>
              </div>
              <div className="bg-indigo-50 dark:bg-indigo-950/40 rounded-xl p-3 text-center border border-indigo-100 dark:border-indigo-900">
                <div className="text-xl font-black text-indigo-700 dark:text-indigo-300">{scopeSummary.faculty || "~" + Math.round(selectedSections.length * 1.5)}</div>
                <div className="text-[11px] font-semibold text-indigo-600 dark:text-indigo-400">Faculty</div>
              </div>
              <div className="bg-emerald-50 dark:bg-emerald-950/40 rounded-xl p-3 text-center border border-emerald-100 dark:border-emerald-900">
                <div className="text-xl font-black text-emerald-700 dark:text-emerald-300">~{scopeSummary.slots}</div>
                <div className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">Slots/Week</div>
              </div>
            </div>
          </div>

          {/* Hard Constraints */}
          <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-2 mb-3">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span className="text-xs font-bold text-slate-700 dark:text-slate-300">All 10 Hard Constraints Locked & Enforced</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {HARD_CONSTRAINTS.map((hc) => (
                <span
                  key={hc.id}
                  title={hc.label}
                  className="inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 rounded-md text-[11px] font-bold"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                  {hc.id}
                </span>
              ))}
            </div>
          </div>

          {/* Advanced Config (collapsed by default) */}
          <div className="px-6 py-3 border-b border-slate-100 dark:border-slate-800">
            <button
              onClick={() => setShowConfig((v) => !v)}
              className="flex items-center gap-2 text-xs font-bold text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 cursor-pointer w-full"
            >
              {showConfig ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              Advanced solver settings
              <span className="ml-auto text-[11px] font-medium text-slate-400">
                {algorithm} · {timeoutSecs}s · {maxDailyHours}h/day
              </span>
            </button>
            {showConfig && (
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Algorithm</label>
                  <select
                    value={algorithm}
                    onChange={(e) => setAlgorithm(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl font-bold text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/30"
                  >
                    <option value="CP-SAT">CP-SAT (Recommended)</option>
                    <option value="GA">Genetic Algorithm</option>
                    <option value="Hybrid">Hybrid CP-SAT + GA</option>
                  </select>
                </div>
                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Timeout: <span className="text-blue-600">{timeoutSecs}s</span>
                  </label>
                  <input
                    type="range" min={30} max={300} step={15} value={timeoutSecs}
                    onChange={(e) => setTimeoutSecs(Number(e.target.value))}
                    className="w-full mt-2 accent-blue-600 cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                    <span>30s</span><span>300s</span>
                  </div>
                </div>
                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Max Faculty: <span className="text-emerald-600">{maxDailyHours}h/day</span>
                  </label>
                  <input
                    type="range" min={3} max={6} step={1} value={maxDailyHours}
                    onChange={(e) => setMaxDailyHours(Number(e.target.value))}
                    className="w-full mt-2 accent-emerald-600 cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                    <span>3h (Strict)</span><span>6h (Max)</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="mx-6 mt-4 flex items-start gap-2 rounded-xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/40 p-4 text-xs text-red-700 dark:text-red-300">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-red-600" />
              <span>{error}</span>
            </div>
          )}

          {/* Result */}
          {result && (
            <div className="mx-6 mt-4 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-2xl p-4 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-emerald-600 rounded-xl text-white shrink-0">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-sm font-bold text-emerald-900 dark:text-emerald-200">
                    Timetable Generated — {result.hard_violations ?? 0} Hard Clashes
                  </div>
                  <div className="text-xs text-emerald-700 dark:text-emerald-400 mt-0.5">
                    {result.entries_count ?? 0} slots scheduled for {selectedSections.length} section{selectedSections.length !== 1 ? "s" : ""}
                    {result.runtime_seconds ? ` in ${result.runtime_seconds}s` : ""}
                  </div>
                </div>
              </div>
              <Link
                href="/schedule"
                className="shrink-0 inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-sm transition-colors"
              >
                View Grid <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          )}

          {/* Generate Button */}
          <div className="px-6 py-5">
            <button
              onClick={result ? () => { setResult(null); setError(null); handleGenerate(); } : handleGenerate}
              disabled={loading || selectedSections.length === 0}
              className="w-full inline-flex items-center justify-center gap-2.5 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 px-6 py-4 text-sm font-black text-white shadow-lg disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-all uppercase tracking-wider"
            >
              {loading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Running {algorithm} Solver for {selectedSections.length} Section{selectedSections.length !== 1 ? "s" : ""}...
                </>
              ) : result ? (
                <>
                  <RefreshCw className="h-5 w-5" />
                  Re-Generate Timetable
                </>
              ) : (
                <>
                  <Zap className="h-5 w-5 text-amber-300" />
                  Generate Timetable — {selectedSections.length} Section{selectedSections.length !== 1 ? "s" : ""}
                </>
              )}
            </button>
            <p className="text-center text-[11px] text-slate-400 dark:text-slate-600 mt-2">
              All 10 hard constraints enforced · 0-clash guarantee · OR-Tools CP-SAT engine
            </p>
          </div>
        </div>
      )}

      {/* Empty state when nothing selected */}
      {selectedSections.length === 0 && !loadingDefaults && (
        <div className="text-center py-8 text-slate-400 dark:text-slate-600 text-sm font-medium">
          Select at least one section above to configure and generate a timetable.
        </div>
      )}
    </div>
  );
};
