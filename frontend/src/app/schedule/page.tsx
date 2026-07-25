"use client";

import React, { useState, useEffect } from "react";
import { Grid, Sparkles, AlertTriangle, Layers, UserCheck, Download, Loader2, RefreshCw, LayoutList, Bot, CheckCircle2, Wand2 } from "lucide-react";
import { TimetableGrid, SlotEntry } from "@/components/timetable/TimetableGrid";
import { timetableApi } from "@/lib/api";
import { Faculty } from "@/lib/types";
import { useSolver } from "@/hooks/useSolver";
import { ScheduleSetupWizard } from "@/components/wizard/ScheduleSetupWizard";

export default function SchedulePage() {
  const [selectedSection, setSelectedSection] = useState("II AIML-A");
  const [selectedCohort, setSelectedCohort] = useState("II_AIML");
  const [entries, setEntries] = useState<SlotEntry[]>([]);
  const [cohortAllSlots, setCohortAllSlots] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Versions tracking
  const [versions, setVersions] = useState<any[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<number>(5);

  // View mode: matrix = single section grid, stack = vertical cohort, faculty = per-faculty, wizard = create new timetable
  const [mode, setMode] = useState<'matrix' | 'stack' | 'faculty' | 'wizard'>('matrix');

  // AI Solver
  const { state: solverState, startSolver } = useSolver();
  const [facultyList, setFacultyList] = useState<Faculty[]>([]);
  const [selectedFacultyId, setSelectedFacultyId] = useState<number | null>(null);
  const [facultyTimetableData, setFacultyTimetableData] = useState<any>(null);
  const [loadingFacultyTimetable, setLoadingFacultyTimetable] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  // Load versions
  useEffect(() => {
    timetableApi.getVersions()
      .then(res => {
        const vList = Array.isArray(res.data) && res.data.length > 0 ? res.data : [
          { id: 5, version_label: 'V5', effective_date: '15-07-2026', hard_violations_count: 51, notes: 'Current baseline imported from V5 Excel dataset' },
          { id: 3, version_label: 'V3', effective_date: '13-07-2026', hard_violations_count: 64, notes: 'Previous revision imported from V3 Excel dataset' }
        ];
        setVersions(vList);
        setSelectedVersionId(vList[0].id);
      })
      .catch(() => {
        setVersions([
          { id: 5, version_label: 'V5', effective_date: '15-07-2026', hard_violations_count: 51, notes: 'Current baseline' }
        ]);
        setSelectedVersionId(5);
      });

    timetableApi.getFaculty().then(res => {
      const facs = Array.isArray(res.data) ? res.data : ((res.data as any)?.items || []);
      setFacultyList(facs);
      if (facs.length > 0) setSelectedFacultyId(facs[0].id);
    });
  }, []);

  // Fetch section timetable slots
  useEffect(() => {
    if (mode === 'matrix' || mode === 'stack') {
      setLoading(true);
      const targetSecName = mode === 'stack' ? 'ALL' : selectedSection;
      timetableApi.getTimetable(selectedVersionId, targetSecName)
        .then((res) => {
          const rawSlots = res.data.slots || res.data.entries || [];
          setCohortAllSlots(rawSlots);
          const mapped: SlotEntry[] = rawSlots.map((s: any, idx: number) => {
            const facList: string[] = Array.isArray(s.faculty)
              ? s.faculty.map((f: any) => String(f))
              : (Array.isArray(s.faculty_names)
                  ? s.faculty_names.map((f: any) => String(f))
                  : (typeof s.faculty === 'string' && s.faculty ? [s.faculty] : []));

            const facStr: string = typeof s.faculty === 'string'
              ? s.faculty
              : (facList.length > 0 ? facList.join(', ') : '');

            const subjStr: string = String(s.subject || s.subject_code || 'LECTURE');

            return {
              id: String(s.id || idx),
              day: s.day,
              period: s.period,
              subjectCode: subjStr,
              roomCode: String(s.room || s.room_code || ''),
              facultyName: facStr,
              facultyNames: facList,
              subjectType: subjStr.includes('(P)') ? 'P' : (subjStr.includes('(T)') ? 'T' : 'L'),
              spanPeriods: subjStr.includes('(P)') ? 2 : 1,
              hasClash: Boolean(s.has_clash),
              clashReason: String(s.clash_reason || ''),
            };
          });
          setEntries(mapped);
        })
        .catch((err) => {
          console.error("Failed to load section slots:", err);
          setEntries([]);
        })
        .finally(() => setLoading(false));
    }
  }, [selectedSection, selectedVersionId, mode]);

  // Fetch faculty timetable slots
  useEffect(() => {
    if (mode === 'faculty' && selectedFacultyId) {
      setLoadingFacultyTimetable(true);
      timetableApi.getFacultyTimetable(selectedFacultyId, selectedVersionId)
        .then((res) => {
          setFacultyTimetableData(res.data);
        })
        .catch((err) => {
          console.error("Failed to load faculty timetable:", err);
          setFacultyTimetableData(null);
        })
        .finally(() => setLoadingFacultyTimetable(false));
    }
  }, [selectedFacultyId, selectedVersionId, mode]);

  const handleDownloadSinglePdf = async () => {
    setDownloadingPdf(true);
    try {
      const res = await timetableApi.exportSectionPdfs(selectedVersionId);
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Timetable_${selectedSection}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Download PDF error:', err);
    } finally {
      setDownloadingPdf(false);
    }
  };

  const handleDownloadFacultyPdf = async () => {
    if (!selectedFacultyId) return;
    setDownloadingPdf(true);
    try {
      const res = await timetableApi.exportSingleFacultyPdf(selectedFacultyId, selectedVersionId);
      const facObj = facultyList.find(f => f.id === selectedFacultyId);
      const fnameClean = facObj?.name.replace(/[^a-zA-Z0-9]/g, '_') || `Faculty_${selectedFacultyId}`;
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `VFSTR_V${selectedVersionId}_Schedule_${fnameClean}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Failed to download faculty PDF', err);
    } finally {
      setDownloadingPdf(false);
    }
  };

  const cohortSectionsMap: Record<string, string[]> = {
    "II_AIML": ["II AIML-A", "II AIML-B", "II AIML-C", "II AIML-D", "II AIML-E", "II AIML-F", "II AIML-G", "II AIML-H", "II AIML-I", "II AIML-J", "II AIML-K", "II AIML-L"],
    "III_AIML": ["III AIML-A", "III AIML-B", "III AIML-C", "III AIML-D", "III AIML-E", "III AIML-F", "III AIML-G"],
    "IV_AIML": ["IV AIML-A", "IV AIML-B", "IV AIML-C", "IV AIML-D", "IV AIML-E"],
    "OTHER": ["II CS-A", "II CS-B", "III CS", "IV CS", "II DS-A", "II DS-B", "III DS-A", "III DS-B", "IV DS", "II CSBS", "III CSBS", "IV CSBS", "II IOT", "III IOT"]
  };

  const stackSections = cohortSectionsMap[selectedCohort] || cohortSectionsMap["II_AIML"];

  const facultyGridEntries: SlotEntry[] = (facultyTimetableData?.entries || []).map((e: any) => ({
    id: String(e.id),
    day: e.day,
    period: e.period,
    subjectCode: e.subject || "LECTURE",
    roomCode: e.room || "",
    sectionName: e.section || "",
    subjectType: e.entry_type || "L",
    facultyName: facultyTimetableData?.faculty_name || ""
  }));

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Timetable Schedule Workbench & AI Wizard</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">Interactive Section Grids, Vertical Stacked View & Faculty Individual Schedules</p>
        </div>

        {/* Mode Toggle Bar */}
        <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800/80 p-1.5 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm shrink-0">
          <button
            onClick={() => setMode('matrix')}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              mode === 'matrix' ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-sm' : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100'
            }`}
          >
            <Grid className="w-4 h-4 text-blue-600 dark:text-blue-400" /> Single Section Grid
          </button>

          <button
            onClick={() => setMode('stack')}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              mode === 'stack' ? 'bg-emerald-600 text-white shadow-md' : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100'
            }`}
          >
            <LayoutList className="w-4 h-4 text-emerald-200" /> Vertical Stack View
          </button>

          <button
            onClick={() => setMode('faculty')}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              mode === 'faculty' ? 'bg-purple-600 text-white shadow-md' : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100'
            }`}
          >
            <UserCheck className="w-4 h-4" /> Faculty Schedules
          </button>

          <button
            onClick={() => setMode('wizard')}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              mode === 'wizard' ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-md' : 'text-amber-600 dark:text-amber-400 hover:text-amber-800 dark:hover:text-amber-300 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800'
            }`}
          >
            <Wand2 className="w-4 h-4" /> Create Timetable
          </button>
        </div>
      </div>

      {/* Version Selector Bar */}
      <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 rounded-xl border border-blue-200 dark:border-blue-800/60">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block">Timetable Version Track:</label>
            <select
              value={selectedVersionId}
              onChange={(e) => setSelectedVersionId(Number(e.target.value))}
              className="bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 px-4 py-1.5 rounded-xl text-xs font-bold shadow-sm focus:outline-none cursor-pointer mt-0.5"
            >
              {versions.map(v => (
                <option key={v.id} value={v.id}>
                  Version {v.version_label} ({v.effective_date}) — {v.hard_violations_count} Hard Clashes
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-semibold text-slate-600 dark:text-slate-400">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>PostgreSQL Active Version V{selectedVersionId}</span>
        </div>
      </div>

      {/* MODE 1: SINGLE SECTION MATRIX GRID */}
      {mode === 'matrix' && (
        <>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm gap-4">
            <div className="flex items-center gap-2">
              <label className="text-xs font-bold text-slate-600 dark:text-slate-400">Active Section:</label>
              <select
                value={selectedSection}
                onChange={(e) => setSelectedSection(e.target.value)}
                className="bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 px-4 py-1.5 rounded-xl text-xs font-bold shadow-sm focus:outline-none cursor-pointer"
              >
                <optgroup label="B.Tech II Year (AIML)">
                  <option value="II AIML-A">II AIML-A</option>
                  <option value="II AIML-B">II AIML-B</option>
                  <option value="II AIML-C">II AIML-C</option>
                  <option value="II AIML-D">II AIML-D</option>
                  <option value="II AIML-E">II AIML-E</option>
                  <option value="II AIML-F">II AIML-F</option>
                  <option value="II AIML-G">II AIML-G</option>
                  <option value="II AIML-H">II AIML-H</option>
                  <option value="II AIML-I">II AIML-I</option>
                  <option value="II AIML-J">II AIML-J</option>
                  <option value="II AIML-K">II AIML-K</option>
                  <option value="II AIML-L">II AIML-L</option>
                </optgroup>
                <optgroup label="B.Tech III Year (AIML)">
                  <option value="III AIML-A">III AIML-A</option>
                  <option value="III AIML-B">III AIML-B</option>
                  <option value="III AIML-C">III AIML-C</option>
                  <option value="III AIML-D">III AIML-D</option>
                  <option value="III AIML-E">III AIML-E</option>
                  <option value="III AIML-F">III AIML-F</option>
                  <option value="III AIML-G">III AIML-G</option>
                </optgroup>
                <optgroup label="B.Tech IV Year (AIML)">
                  <option value="IV AIML-A">IV AIML-A</option>
                  <option value="IV AIML-B">IV AIML-B</option>
                  <option value="IV AIML-C">IV AIML-C</option>
                  <option value="IV AIML-D">IV AIML-D</option>
                  <option value="IV AIML-E">IV AIML-E</option>
                </optgroup>
                <optgroup label="B.Tech CS / DS">
                  <option value="II CS-A">II CS-A</option>
                  <option value="II CS-B">II CS-B</option>
                  <option value="III CS">III CS</option>
                  <option value="IV CS">IV CS</option>
                  <option value="II DS-A">II DS-A</option>
                  <option value="II DS-B">II DS-B</option>
                  <option value="III DS-A">III DS-A</option>
                  <option value="III DS-B">III DS-B</option>
                  <option value="IV DS">IV DS</option>
                </optgroup>
                <optgroup label="B.Tech CSBS / IOT">
                  <option value="II CSBS">II CSBS</option>
                  <option value="III CSBS">III CSBS</option>
                  <option value="IV - CSBS">IV CSBS</option>
                  <option value="II IOT">II IOT</option>
                  <option value="III IOT">III IOT</option>
                </optgroup>
              </select>
            </div>

            <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
              <span>Total Section Slots: {entries.length}</span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <div className="lg:col-span-3">
              {loading ? (
                <div className="w-full h-80 rounded-2xl border border-slate-200 bg-white flex flex-col items-center justify-center text-slate-400 gap-2">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                  <p className="text-xs font-medium">Loading {selectedSection} Schedule...</p>
                </div>
              ) : (
                <TimetableGrid sectionName={selectedSection} entries={entries} />
              )}
            </div>
            <div className="space-y-4">
              {/* Section Quick Stats */}
              <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
                <h3 className="font-bold text-xs text-slate-700 mb-2 flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-500" /> Section Stats
                </h3>
                <div className="space-y-1.5 text-xs text-slate-600">
                  <div className="flex justify-between">
                    <span>Section:</span>
                    <span className="font-bold text-blue-700">{selectedSection}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Total Slots:</span>
                    <span className="font-bold">{entries.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Lab (P) Slots:</span>
                    <span className="font-bold text-purple-700">{entries.filter(e => e.subjectType === 'P').length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Hard Clashes:</span>
                    <span className={`font-bold ${entries.filter(e => e.hasClash).length > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                      {entries.filter(e => e.hasClash).length}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Version:</span>
                    <span className="font-bold">V{selectedVersionId}</span>
                  </div>
                </div>
              </div>

              {/* ── AI SOLVER PANEL (fully wired to useSolver hook) ── */}
              <div className="bg-gradient-to-br from-slate-900 via-indigo-950 to-blue-900 border border-indigo-800/40 rounded-2xl p-5 shadow-xl space-y-4">
                <div className="flex items-center gap-3">
                  <div className={`p-2.5 rounded-xl text-white ${solverState.isComplete ? 'bg-emerald-600' : solverState.isSolving ? 'bg-purple-600 animate-pulse' : 'bg-blue-600'}`}>
                    {solverState.isSolving
                      ? <Loader2 className="w-5 h-5 animate-spin" />
                      : solverState.isComplete
                      ? <CheckCircle2 className="w-5 h-5" />
                      : <Bot className="w-5 h-5" />}
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-white leading-tight">Google OR-Tools CP-SAT</h3>
                    <p className="text-[10px] text-blue-300">591,360 binary variables • 44 sections</p>
                  </div>
                </div>

                {/* Status message */}
                <div className="text-[11px] text-blue-200 font-medium bg-white/5 rounded-lg px-3 py-2 border border-white/10">
                  {solverState.message}
                </div>

                {/* Progress bar (shows when solving or complete) */}
                {(solverState.isSolving || solverState.isComplete) && (
                  <div className="space-y-2">
                    <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all duration-700 ${solverState.isComplete ? 'bg-emerald-500' : 'bg-gradient-to-r from-blue-500 to-purple-500'}`}
                        style={{ width: `${solverState.isComplete ? 100 : Math.min(95, Math.max(10, Math.round(((51 - solverState.hardViolations) / 51) * 100)))}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[10px] text-blue-300">
                      <span>Gen {solverState.generation} • {solverState.runtimeSeconds}s</span>
                      <span className={`font-bold px-2 py-0.5 rounded ${solverState.hardViolations === 0 ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'}`}>
                        {solverState.hardViolations} hard clashes
                      </span>
                    </div>
                  </div>
                )}

                {/* Error message */}
                {solverState.error && (
                  <div className="text-[10px] text-red-300 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                    ⚠ {solverState.error}
                  </div>
                )}

                {/* Algorithm selector + Run button */}
                <div className="space-y-2 pt-1">
                  <select
                    className="w-full bg-white/10 border border-white/20 text-white text-xs font-medium px-3 py-2 rounded-xl focus:outline-none cursor-pointer"
                    defaultValue="CP-SAT"
                    id="solver-algorithm-select"
                  >
                    <option value="CP-SAT">CP-SAT (Constraint Programming)</option>
                    <option value="GA">Genetic Algorithm</option>
                    <option value="Hybrid">Hybrid CP-SAT + GA</option>
                  </select>

                  <button
                    onClick={() => {
                      const sel = document.getElementById('solver-algorithm-select') as HTMLSelectElement;
                      startSolver(sel?.value || 'CP-SAT');
                    }}
                    disabled={solverState.isSolving}
                    className="w-full inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-bold text-xs px-4 py-2.5 rounded-xl transition-all cursor-pointer shadow-md"
                  >
                    {solverState.isSolving ? (
                      <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Solving in progress...</>
                    ) : solverState.isComplete ? (
                      <><RefreshCw className="w-3.5 h-3.5" /> Re-Run Solver</>
                    ) : (
                      <><Sparkles className="w-3.5 h-3.5" /> Run AI Solver Engine</>
                    )}
                  </button>

                  {solverState.isComplete && solverState.hardViolations === 0 && (
                    <div className="flex items-center gap-2 text-[11px] font-bold text-emerald-300 bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-3 py-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      100% Clash-Free Timetable Generated!
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* MODE 2: VERTICAL STACKED COHORT VIEW (Matching Screenshot 213129) */}
      {mode === 'stack' && (
        <div className="space-y-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between bg-white p-4 rounded-2xl border border-slate-200 shadow-sm gap-4">
            <div className="flex items-center gap-3">
              <label className="text-xs font-bold text-slate-700 block">Select Cohort / Year Level:</label>
              <select
                value={selectedCohort}
                onChange={(e) => setSelectedCohort(e.target.value)}
                className="bg-slate-50 border border-slate-300 text-slate-900 px-4 py-1.5 rounded-xl text-xs font-bold shadow-sm focus:outline-none cursor-pointer"
              >
                <option value="II_AIML">B.Tech II Year AIML (Sections A-L)</option>
                <option value="III_AIML">B.Tech III Year AIML (Sections A-G)</option>
                <option value="IV_AIML">B.Tech IV Year AIML (Sections A-E)</option>
                <option value="CS_DS">B.Tech CS & DS (All Years)</option>
                <option value="CSBS_IOT">B.Tech CSBS & IOT (All Years)</option>
              </select>
            </div>

            <div className="text-xs text-slate-500 font-semibold">
              Rendering {stackSections.length} sections vertically stacked with clean spacing
            </div>
          </div>

          <div className="space-y-12">
            {stackSections.map((secName, sIdx) => {
              const normSecName = secName.replace(/[\s-]/g, "").toUpperCase();
              const secSlots = cohortAllSlots.filter(s => {
                const rawSec = String(s.section || s.section_name || s.section_code || "");
                return rawSec.replace(/[\s-]/g, "").toUpperCase() === normSecName;
              });

              const mappedSecSlots: SlotEntry[] = secSlots.map((s: any, idx: number) => {
                const subStr = String(s.subject || s.subject_code || "LECTURE");
                const rmStr = String(s.room || s.room_code || "");
                const facStr = typeof s.faculty === "string" ? s.faculty : Array.isArray(s.faculty) ? s.faculty.map(String).join(", ") : "";
                const facArr = Array.isArray(s.faculty_names) ? s.faculty_names.map(String) : Array.isArray(s.faculty) ? s.faculty.map(String) : facStr ? [facStr] : [];
                return {
                  id: String(s.id || idx),
                  day: s.day,
                  period: s.period,
                  subjectCode: subStr,
                  roomCode: rmStr,
                  facultyName: facStr,
                  facultyNames: facArr,
                  subjectType: subStr.includes("(P)") ? "P" : subStr.includes("(T)") ? "T" : "L",
                  spanPeriods: subStr.includes("(P)") ? 2 : 1,
                  hasClash: Boolean(s.has_clash),
                  clashReason: String(s.clash_reason || ""),
                };
              });

              return (
                <div key={secName} className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="px-3 py-1 bg-purple-100 text-purple-900 border border-purple-300 font-extrabold text-xs rounded-lg">
                      Section #{sIdx + 1}
                    </span>
                    <span className="text-xs font-bold text-slate-500">Vertical Stack Sequence ({secName})</span>
                  </div>
                  <TimetableGrid sectionName={secName} entries={mappedSecSlots} />
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* MODE 3: FACULTY SCHEDULE VIEW */}
      {mode === 'faculty' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block shrink-0">Select Faculty Member:</label>
              <select
                value={selectedFacultyId || ''}
                onChange={(e) => setSelectedFacultyId(Number(e.target.value))}
                className="bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 px-4 py-1.5 rounded-xl text-xs font-bold shadow-sm focus:outline-none cursor-pointer"
              >
                {facultyList.map(f => (
                  <option key={f.id} value={f.id}>{f.name} ({f.designation})</option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleDownloadFacultyPdf}
                disabled={downloadingPdf || !selectedFacultyId}
                className="inline-flex items-center justify-center gap-2 bg-purple-600 hover:bg-purple-700 text-white font-bold px-4 py-2 rounded-xl text-xs transition-colors shadow-sm cursor-pointer disabled:opacity-50"
              >
                {downloadingPdf ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                Download Individual PDF
              </button>

              <button
                onClick={async () => {
                  try {
                    const res = await timetableApi.exportFacultyPdf(selectedVersionId);
                    const blob = new Blob([res.data], { type: 'application/pdf' });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `VFSTR_V${selectedVersionId}_Faculty_Booklet.pdf`;
                    a.click();
                  } catch (e) {
                    console.error("Booklet export failed", e);
                  }
                }}
                className="inline-flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-900 dark:bg-slate-700 dark:hover:bg-slate-600 text-white font-bold px-4 py-2 rounded-xl text-xs transition-colors shadow-sm cursor-pointer"
              >
                <Download className="w-4 h-4 text-purple-300" /> Full Faculty Booklet PDF
              </button>
            </div>
          </div>

          {loadingFacultyTimetable ? (
            <div className="w-full h-80 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col items-center justify-center text-slate-400 gap-2">
              <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
              <p className="text-xs font-medium">Loading Faculty Teaching Schedule...</p>
            </div>
          ) : facultyTimetableData ? (
            <div className="space-y-6">
              {/* Profile Card & Workload Bar */}
              <div className="bg-gradient-to-r from-purple-900 via-indigo-900 to-slate-900 text-white p-6 rounded-2xl shadow-md border border-purple-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-bold">{facultyTimetableData.faculty_name || facultyTimetableData.name}</h2>
                  <p className="text-xs text-purple-200 mt-0.5">
                    {facultyTimetableData.designation || "Faculty Member"} • ACSE Department • Vignan University
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-2xl font-extrabold text-purple-200">
                    {facultyTimetableData.assigned_hours ?? facultyTimetableData.total_hours ?? (facultyTimetableData.entries || []).length} / {facultyTimetableData.max_hours_per_week ?? facultyTimetableData.max_hours ?? 16} Hours
                  </div>
                  <div className="text-[11px] text-purple-300">Weekly Teaching Load Limit</div>
                  <div className="w-48 h-2 bg-purple-950 rounded-full mt-2 overflow-hidden border border-purple-700/60">
                    <div
                      className="h-full bg-gradient-to-r from-emerald-400 to-purple-400 rounded-full"
                      style={{
                        width: `${Math.min(100, Math.round((((facultyTimetableData.assigned_hours ?? (facultyTimetableData.entries || []).length)) / (facultyTimetableData.max_hours_per_week ?? 16)) * 100))}%`
                      }}
                    />
                  </div>
                </div>
              </div>

              {/* Personal Teaching Schedule Matrix Grid */}
              <TimetableGrid
                sectionName={`${facultyTimetableData.faculty_name || facultyTimetableData.name} Schedule`}
                entries={(facultyTimetableData.entries || []).map((e: any, idx: number) => ({
                  id: String(e.id || idx),
                  day: e.day,
                  period: e.period,
                  subjectCode: e.subject || e.subject_code || "LECTURE",
                  roomCode: e.room || e.room_code || "",
                  sectionName: e.section || e.section_name || "",
                  subjectType: (e.subject || "").includes("(P)") ? "P" : (e.subject || "").includes("(T)") ? "T" : "L",
                  spanPeriods: (e.subject || "").includes("(P)") ? 2 : 1,
                  facultyName: facultyTimetableData.faculty_name || facultyTimetableData.name || ""
                }))}
              />

              {/* Detailed Weekly Teaching Allocation Breakdown Table */}
              <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-3">
                <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                    Weekly Teaching Class Allocation Breakdown — {facultyTimetableData.faculty_name || facultyTimetableData.name}
                  </h3>
                  <span className="text-xs font-semibold text-purple-700 dark:text-purple-300 bg-purple-50 dark:bg-purple-950/60 px-3 py-1 rounded-full border border-purple-200 dark:border-purple-800">
                    {(facultyTimetableData.entries || []).length} Classes Assigned
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left border-collapse">
                    <thead>
                      <tr className="bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold border-b border-slate-200 dark:border-slate-700">
                        <th className="p-2.5 w-10 text-center">#</th>
                        <th className="p-2.5 w-24">Day</th>
                        <th className="p-2.5 w-24">Period / Time</th>
                        <th className="p-2.5">Subject</th>
                        <th className="p-2.5 w-32">Section & Cohort</th>
                        <th className="p-2.5 w-28">Classroom / Lab</th>
                        <th className="p-2.5 w-20 text-center">Type</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(facultyTimetableData.entries || []).map((e: any, i: number) => {
                        const PERIOD_TIMES: Record<number, string> = {
                          1: "8:15–9:05",
                          2: "9:05–9:55",
                          3: "10:10–11:00",
                          4: "11:00–11:50",
                          5: "11:50–12:40",
                          6: "1:40–2:30",
                          7: "2:30–3:20",
                          8: "3:20–4:05"
                        };
                        const subjCode = e.subject || e.subject_code || "LECTURE";
                        const isLab = subjCode.includes("(P)");
                        const isTut = subjCode.includes("(T)");
                        return (
                          <tr key={i} className="border-b border-slate-100 dark:border-slate-800/60 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                            <td className="p-2.5 text-center font-mono text-slate-400">{i + 1}</td>
                            <td className="p-2.5 font-extrabold text-slate-900 dark:text-slate-100">{e.day}</td>
                            <td className="p-2.5 font-semibold text-slate-700 dark:text-slate-300">
                              Period {e.period} <span className="text-[10px] text-slate-400 block font-normal">{PERIOD_TIMES[e.period] || ""}</span>
                            </td>
                            <td className="p-2.5 font-bold text-slate-800 dark:text-slate-200">{subjCode}</td>
                            <td className="p-2.5">
                              <span className="bg-purple-100 dark:bg-purple-950/60 text-purple-900 dark:text-purple-200 font-extrabold px-2 py-0.5 rounded text-[11px] border border-purple-200 dark:border-purple-800">
                                {e.section || e.section_name || "Section"}
                              </span>
                            </td>
                            <td className="p-2.5 font-extrabold text-red-600 dark:text-red-400">{e.room || e.room_code || "Room"}</td>
                            <td className="p-2.5 text-center">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${isLab ? "bg-violet-100 text-violet-800 dark:bg-violet-950/60 dark:text-violet-300" : isTut ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300" : "bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300"}`}>
                                {isLab ? "Lab (P)" : isTut ? "Tutorial (T)" : "Lecture (L)"}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 text-slate-500 text-xs font-medium">
              Select a faculty member to load their personal teaching schedule matrix.
            </div>
          )}
        </div>
      )}


      {/* MODE 4: CREATE TIMETABLE WIZARD */}
      {mode === 'wizard' && (
        <div className="space-y-4">
          {/* Banner */}
          <div className="bg-gradient-to-r from-amber-500 via-orange-500 to-rose-500 text-white rounded-2xl p-5 shadow-md flex items-center justify-between">
            <div>
              <h2 className="text-lg font-extrabold flex items-center gap-2">
                <Wand2 className="w-5 h-5" /> Timetable Creation Wizard
              </h2>
              <p className="text-sm text-amber-100 mt-0.5">
                Select sections, assign faculty to subjects, and let the AI solver generate a clash-free timetable
              </p>
            </div>
            <button
              onClick={() => setMode('matrix')}
              className="text-white/70 hover:text-white text-xs font-bold underline cursor-pointer"
            >
              ← Back to Grid View
            </button>
          </div>

          <ScheduleSetupWizard
            onSuccess={(response) => {
              setMode('matrix');
            }}
          />
        </div>
      )}
    </div>
  );
}
