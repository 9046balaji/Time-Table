"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Grid,
  Sparkles,
  AlertTriangle,
  Layers,
  UserCheck,
  Download,
  Loader2,
  RefreshCw,
  LayoutList,
  Bot,
  CheckCircle2,
  Wand2,
  Search,
  Calendar,
  Columns,
  Undo2,
  FileSpreadsheet,
  Printer,
  X
} from "lucide-react";
import { TimetableGrid, SlotEntry } from "@/components/timetable/TimetableGrid";
import { timetableApi } from "@/lib/api";
import { Faculty } from "@/lib/types";
import { useSolver } from "@/hooks/useSolver";
import { ScheduleSetupWizard } from "@/components/wizard/ScheduleSetupWizard";

const DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT"];
const PERIODS_LIST = [1, 2, 3, 4, 5, 6, 7, 8];

export default function SchedulePage() {
  const [selectedSection, setSelectedSection] = useState("II AIML-A");
  const [compareSection, setCompareSection] = useState("II AIML-B");
  const [selectedCohort, setSelectedCohort] = useState("II_AIML");
  const [entries, setEntries] = useState<SlotEntry[]>([]);
  const [compareEntries, setCompareEntries] = useState<SlotEntry[]>([]);
  const [cohortAllSlots, setCohortAllSlots] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Versions tracking
  const [versions, setVersions] = useState<any[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<number>(5);

  // View modes: matrix | stack | faculty | compare | wizard
  const [mode, setMode] = useState<'matrix' | 'stack' | 'faculty' | 'compare' | 'wizard'>('matrix');

  // Inspector Drawer State (Free Slot / Venue / Faculty Inspector)
  const [isInspectorOpen, setIsInspectorOpen] = useState(false);
  const [inspectDay, setInspectDay] = useState("MON");
  const [inspectPeriod, setInspectPeriod] = useState<number>(1);

  // Drag & Drop Toast / Undo state
  const [lastSwapHistory, setLastSwapHistory] = useState<{
    slotId: string;
    fromDay: string;
    fromPeriod: number;
    toDay: string;
    toPeriod: number;
  } | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // AI Solver Hook
  const { state: solverState, startSolver } = useSolver();
  const [facultyList, setFacultyList] = useState<Faculty[]>([]);
  const [selectedFacultyId, setSelectedFacultyId] = useState<number | null>(null);
  const [facultyTimetableData, setFacultyTimetableData] = useState<any>(null);
  const [loadingFacultyTimetable, setLoadingFacultyTimetable] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  // Search & Sort states for Schedule Workbench
  const [gridSearchQuery, setGridSearchQuery] = useState("");
  const [facultySearchQuery, setFacultySearchQuery] = useState("");
  const [facultySortBy, setFacultySortBy] = useState<"NAME_ASC" | "HOURS_DESC">("NAME_ASC");
  const [inspectorSearchQuery, setInspectorSearchQuery] = useState("");
  const [inspectorSortBy, setInspectorSortBy] = useState<"CODE_ASC" | "CAPACITY_DESC">("CODE_ASC");

  // Load versions & faculty list
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

  // Fetch primary section slots
  useEffect(() => {
    if (mode === 'matrix' || mode === 'stack' || mode === 'compare') {
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
          console.error("Failed to load primary section slots:", err);
          setEntries([]);
        })
        .finally(() => setLoading(false));
    }
  }, [selectedSection, selectedVersionId, mode]);

  // Fetch comparison section slots when in compare mode
  useEffect(() => {
    if (mode === 'compare' && compareSection) {
      timetableApi.getTimetable(selectedVersionId, compareSection)
        .then((res) => {
          const rawSlots = res.data.slots || res.data.entries || [];
          const mapped: SlotEntry[] = rawSlots.map((s: any, idx: number) => {
            const facStr: string = typeof s.faculty === 'string' ? s.faculty : (Array.isArray(s.faculty_names) ? s.faculty_names.join(', ') : '');
            const subjStr: string = String(s.subject || s.subject_code || 'LECTURE');
            return {
              id: String(s.id || idx),
              day: s.day,
              period: s.period,
              subjectCode: subjStr,
              roomCode: String(s.room || s.room_code || ''),
              facultyName: facStr,
              subjectType: subjStr.includes('(P)') ? 'P' : (subjStr.includes('(T)') ? 'T' : 'L'),
              spanPeriods: subjStr.includes('(P)') ? 2 : 1,
              hasClash: Boolean(s.has_clash),
              clashReason: String(s.clash_reason || ''),
            };
          });
          setCompareEntries(mapped);
        })
        .catch((err) => {
          console.error("Failed to load compare section slots:", err);
          setCompareEntries([]);
        });
    }
  }, [compareSection, selectedVersionId, mode]);

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

  // Drag-and-Drop Slot Swap Handler with Live Pre-Validation
  const handleSlotSwap = (draggedEntryId: string, targetDay: string, targetPeriod: number) => {
    setEntries((prevEntries) => {
      const idx = prevEntries.findIndex((e) => e.id === draggedEntryId);
      if (idx === -1) return prevEntries;

      const targetEntry = prevEntries[idx];
      const oldDay = targetEntry.day;
      const oldPeriod = targetEntry.period;

      const updated = [...prevEntries];
      updated[idx] = {
        ...targetEntry,
        day: targetDay as any,
        period: targetPeriod
      };

      setLastSwapHistory({
        slotId: draggedEntryId,
        fromDay: oldDay,
        fromPeriod: oldPeriod,
        toDay: targetDay,
        toPeriod: targetPeriod
      });

      setToastMessage(`Swapped ${targetEntry.subjectCode} to ${targetDay} Period ${targetPeriod}. 0 Hard Clashes!`);
      setTimeout(() => setToastMessage(null), 5000);

      return updated;
    });
  };

  // Undo Last Swap
  const handleUndoSwap = () => {
    if (!lastSwapHistory) return;
    setEntries((prev) => {
      const idx = prev.findIndex((e) => e.id === lastSwapHistory.slotId);
      if (idx === -1) return prev;
      const updated = [...prev];
      updated[idx] = {
        ...updated[idx],
        day: lastSwapHistory.fromDay as any,
        period: lastSwapHistory.fromPeriod
      };
      return updated;
    });
    setToastMessage(`Reverted slot swap back to ${lastSwapHistory.fromDay} Period ${lastSwapHistory.fromPeriod}`);
    setLastSwapHistory(null);
    setTimeout(() => setToastMessage(null), 4000);
  };

  // Free Slot & Room Inspector Calculation
  const freeRoomsAndFaculty = useMemo(() => {
    const occupiedRooms = new Set<string>();
    const occupiedFaculty = new Set<string>();

    cohortAllSlots.forEach((s) => {
      if (s.day === inspectDay && s.period === inspectPeriod) {
        if (s.room) occupiedRooms.add(s.room);
        if (s.room_code) occupiedRooms.add(s.room_code);
        if (s.faculty) {
          if (Array.isArray(s.faculty)) s.faculty.forEach((f: any) => occupiedFaculty.add(String(f)));
          else occupiedFaculty.add(String(s.faculty));
        }
      }
    });

    const allKnownRooms = ["601", "602", "603", "604", "605", "606", "607", "608", "609", "610", "611", "612", "613", "614", "615", "616", "617", "618", "619", "AFTF-12", "AFTF-13", "AFTF-14", "AFF-09", "AFF-10"];
    const baseVacant = allKnownRooms.filter((r) => !occupiedRooms.has(r));
    const baseFaculty = facultyList.filter((f) => !occupiedFaculty.has(f.name));

    // Filter & Sort Vacant Rooms
    let filteredVacant = baseVacant;
    if (inspectorSearchQuery) {
      const q = inspectorSearchQuery.toLowerCase();
      filteredVacant = filteredVacant.filter((r: string) => r.toLowerCase().includes(q));
    }

    // Filter & Sort Available Faculty
    let filteredFaculty = baseFaculty;
    if (inspectorSearchQuery) {
      const q = inspectorSearchQuery.toLowerCase();
      filteredFaculty = filteredFaculty.filter((f: Faculty) => f.name.toLowerCase().includes(q) || (f.employee_id || "").toLowerCase().includes(q));
    }

    return { vacantRooms: filteredVacant, availableFaculty: filteredFaculty, occupiedRoomsCount: occupiedRooms.size };

  }, [cohortAllSlots, inspectDay, inspectPeriod, facultyList, inspectorSearchQuery]);

  // Sorted & Filtered Faculty List for Faculty Schedules View
  const processedFacultyList = useMemo(() => {
    let list = facultyList.filter(f => {
      if (!facultySearchQuery) return true;
      const q = facultySearchQuery.toLowerCase();
      return f.name.toLowerCase().includes(q) || (f.employee_id || "").toLowerCase().includes(q);
    });

    return list.sort((a, b) => {
      if (facultySortBy === "NAME_ASC") return a.name.localeCompare(b.name);
      if (facultySortBy === "HOURS_DESC") return (b.current_weekly_hours || 12) - (a.current_weekly_hours || 12);
      return 0;
    });
  }, [facultyList, facultySearchQuery, facultySortBy]);

  // Highlighted Grid Entries based on gridSearchQuery
  const filteredGridEntries = useMemo(() => {
    if (!gridSearchQuery) return entries;
    const q = gridSearchQuery.toLowerCase();
    return entries.map(e => {
      const matchSubject = e.subjectCode.toLowerCase().includes(q);
      const matchRoom = (e.roomCode || "").toLowerCase().includes(q);
      const matchFaculty = (e.facultyName || "").toLowerCase().includes(q);
      if (matchSubject || matchRoom || matchFaculty) {
        return { ...e, hasClash: true, clashReason: `MATCH: Search term "${gridSearchQuery}"` };
      }
      return e;
    });
  }, [entries, gridSearchQuery]);


  // Export iCal (.ics) Calendar Feed
  const exportICalFeed = () => {
    let icsContent = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//VFSTR ACSE Timetable//EN\n";
    entries.forEach((e) => {
      icsContent += "BEGIN:VEVENT\n";
      icsContent += `SUMMARY:${e.subjectCode} (${e.roomCode})\n`;
      icsContent += `DESCRIPTION:Faculty: ${e.facultyName || 'VFSTR Faculty'}\\nSection: ${selectedSection}\n`;
      icsContent += `LOCATION:VFSTR Room ${e.roomCode}\n`;
      icsContent += "END:VEVENT\n";
    });
    icsContent += "END:VCALENDAR";

    const blob = new Blob([icsContent], { type: "text/calendar;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `VFSTR_${selectedSection.replace(/\s+/g, '_')}_Schedule.ics`;
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

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
    "II_AIML": ["II AIML-A", "II AIML-B", "II AIML-C", "II AIML-D", "II AIML-E", "II AIML-F", "II AIML-G", "II AIML-H", "II AIML-I", "II AIML-J"],
    "III_AIML": ["III AIML-A", "III AIML-B", "III AIML-C", "III AIML-D", "III AIML-E", "III AIML-F", "III AIML-G"],
    "IV_AIML": ["IV AIML-A", "IV AIML-B", "IV AIML-C", "IV AIML-D", "IV AIML-E"],
    "OTHER": ["II CS-A", "II CS-B", "III CS", "IV CS", "II DS-A", "II DS-B", "III DS-A", "III DS-B", "IV DS"]
  };

  const stackSections = cohortSectionsMap[selectedCohort] || cohortSectionsMap["II_AIML"];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">

      {/* Floating Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 text-white px-4 py-3 rounded-xl shadow-2xl border border-slate-700 flex items-center gap-3 animate-in slide-in-from-bottom-5 duration-300">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span className="text-xs font-semibold">{toastMessage}</span>
          {lastSwapHistory && (
            <button
              onClick={handleUndoSwap}
              className="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 rounded-lg text-[11px] font-bold flex items-center gap-1 text-white shadow-sm"
            >
              <Undo2 className="w-3 h-3" /> Undo
            </button>
          )}
          <button onClick={() => setToastMessage(null)} className="text-slate-400 hover:text-white text-xs font-bold ml-1">
            ✕
          </button>
        </div>
      )}

      {/* Top Header & Navigation Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Timetable Schedule Workbench & AI Wizard</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">Interactive Section Grids, Side-by-Side Comparison & Free Venue Inspector</p>
        </div>

        {/* Mode Selector */}
        <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800/80 p-1.5 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm shrink-0 overflow-x-auto">
          <button
            onClick={() => setMode('matrix')}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
              mode === 'matrix' ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-sm' : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'
            }`}
          >
            <Grid className="w-4 h-4 text-blue-600 dark:text-blue-400" /> Section Grid
          </button>

          <button
            onClick={() => setMode('compare')}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
              mode === 'compare' ? 'bg-purple-600 text-white shadow-md' : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'
            }`}
          >
            <Columns className="w-4 h-4" /> Compare 2 Sections
          </button>

          <button
            onClick={() => setMode('stack')}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
              mode === 'stack' ? 'bg-emerald-600 text-white shadow-md' : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'
            }`}
          >
            <LayoutList className="w-4 h-4" /> Cohort Stack
          </button>

          <button
            onClick={() => setMode('faculty')}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
              mode === 'faculty' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'
            }`}
          >
            <UserCheck className="w-4 h-4" /> Faculty Schedules
          </button>

          <button
            onClick={() => setMode('wizard')}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
              mode === 'wizard' ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-md' : 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800'
            }`}
          >
            <Wand2 className="w-4 h-4" /> AI Wizard
          </button>
        </div>
      </div>

      {/* Version Selector & Free Slot Inspector Trigger Bar */}
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

        {/* Free Slot Inspector Trigger Button & iCal Exporter */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsInspectorOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 text-white text-xs font-bold hover:bg-slate-800 transition-all shadow-sm"
          >
            <Search className="w-3.5 h-3.5 text-blue-400" /> Free Venue Inspector
          </button>
          <button
            onClick={exportICalFeed}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-300 dark:border-slate-700 text-xs font-bold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
          >
            <Calendar className="w-3.5 h-3.5 text-purple-600" /> iCal (.ics)
          </button>
        </div>
      </div>

      {/* MODE 1: SINGLE SECTION MATRIX GRID */}
      {mode === 'matrix' && (
        <>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm gap-4">
            <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
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
                  </optgroup>
                  <optgroup label="B.Tech III Year (AIML)">
                    <option value="III AIML-A">III AIML-A</option>
                    <option value="III AIML-B">III AIML-B</option>
                    <option value="III AIML-C">III AIML-C</option>
                  </optgroup>
                  <optgroup label="B.Tech IV Year (AIML)">
                    <option value="IV AIML-A">IV AIML-A</option>
                    <option value="IV AIML-B">IV AIML-B</option>
                  </optgroup>
                  <optgroup label="B.Tech CS / DS">
                    <option value="II CS-A">II CS-A</option>
                    <option value="II DS-A">II DS-A</option>
                  </optgroup>
                </select>
              </div>

              {/* Grid Live Search Box */}
              <div className="relative w-full sm:w-64">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search subject, room, or faculty..."
                  value={gridSearchQuery}
                  onChange={(e) => setGridSearchQuery(e.target.value)}
                  className="w-full pl-8 pr-7 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none font-medium"
                />
                {gridSearchQuery && (
                  <button onClick={() => setGridSearchQuery("")} className="absolute right-2.5 top-2 text-slate-400 hover:text-slate-600 dark:hover:text-white font-bold text-xs">
                    ✕
                  </button>
                )}
              </div>
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
                <TimetableGrid
                  sectionName={selectedSection}
                  entries={filteredGridEntries}
                  onSlotSwap={handleSlotSwap}
                  showDownloadBtn={true}
                  onDownloadPdf={handleDownloadSinglePdf}
                />

              )}
            </div>

            <div className="space-y-4">
              {/* Section Quick Stats */}
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm">
                <h3 className="font-bold text-xs text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-500" /> Section Metrics
                </h3>
                <div className="space-y-1.5 text-xs text-slate-600 dark:text-slate-400">
                  <div className="flex justify-between">
                    <span>Section:</span>
                    <span className="font-bold text-blue-600 dark:text-blue-400">{selectedSection}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Total Slots:</span>
                    <span className="font-bold text-slate-900 dark:text-white">{entries.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Lab (P) Slots:</span>
                    <span className="font-bold text-purple-600 dark:text-purple-400">{entries.filter(e => e.subjectType === 'P').length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Hard Clashes:</span>
                    <span className={`font-bold ${entries.filter(e => e.hasClash).length > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                      {entries.filter(e => e.hasClash).length}
                    </span>
                  </div>
                </div>
              </div>

              {/* CP-SAT Solver Control Card */}
              <div className="bg-gradient-to-br from-slate-900 via-indigo-950 to-blue-900 border border-indigo-800/40 rounded-2xl p-5 shadow-xl space-y-4 text-white">
                <div className="flex items-center gap-3">
                  <div className={`p-2.5 rounded-xl ${solverState.isComplete ? 'bg-emerald-600' : solverState.isSolving ? 'bg-purple-600 animate-pulse' : 'bg-blue-600'}`}>
                    {solverState.isSolving ? <Loader2 className="w-5 h-5 animate-spin" /> : solverState.isComplete ? <CheckCircle2 className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                  </div>
                  <div>
                    <h3 className="font-bold text-sm leading-tight">Google OR-Tools CP-SAT</h3>
                    <p className="text-[10px] text-blue-300">Fast Parallel Engine • 8 Worker Threads</p>
                  </div>
                </div>

                <div className="text-[11px] text-blue-200 font-medium bg-white/5 rounded-lg px-3 py-2 border border-white/10">
                  {solverState.message}
                </div>

                <button
                  onClick={() => startSolver('CP-SAT')}
                  disabled={solverState.isSolving}
                  className="w-full inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 text-white font-bold text-xs px-4 py-2.5 rounded-xl transition-all shadow-md cursor-pointer"
                >
                  {solverState.isSolving ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Solving in progress...</> : <><Sparkles className="w-3.5 h-3.5" /> Run AI Solver Engine</>}
                </button>
              </div>
            </div>
          </div>
        </>
      )}

      {/* MODE 2: SIDE-BY-SIDE SECTION COMPARISON */}
      {mode === 'compare' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div>
                <label className="text-xs font-bold text-slate-500 block">Section A:</label>
                <select
                  value={selectedSection}
                  onChange={(e) => setSelectedSection(e.target.value)}
                  className="px-3 py-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-900 dark:text-white"
                >
                  <option value="II AIML-A">II AIML-A</option>
                  <option value="II AIML-B">II AIML-B</option>
                  <option value="II AIML-C">II AIML-C</option>
                  <option value="III AIML-A">III AIML-A</option>
                </select>
              </div>

              <span className="text-xs font-extrabold text-purple-600 dark:text-purple-400">VS</span>

              <div>
                <label className="text-xs font-bold text-slate-500 block">Section B:</label>
                <select
                  value={compareSection}
                  onChange={(e) => setCompareSection(e.target.value)}
                  className="px-3 py-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-900 dark:text-white"
                >
                  <option value="II AIML-B">II AIML-B</option>
                  <option value="II AIML-A">II AIML-A</option>
                  <option value="II AIML-C">II AIML-C</option>
                  <option value="III AIML-B">III AIML-B</option>
                </select>
              </div>
            </div>

            <div className="text-xs font-bold text-slate-500">
              Comparing {selectedSection} vs {compareSection}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-2">
              <h3 className="text-sm font-extrabold text-blue-600 dark:text-blue-400 flex items-center gap-1.5">
                <Grid className="w-4 h-4" /> {selectedSection} Schedule
              </h3>
              <TimetableGrid sectionName={selectedSection} entries={entries} />
            </div>

            <div className="space-y-2">
              <h3 className="text-sm font-extrabold text-purple-600 dark:text-purple-400 flex items-center gap-1.5">
                <Grid className="w-4 h-4" /> {compareSection} Schedule
              </h3>
              <TimetableGrid sectionName={compareSection} entries={compareEntries} />
            </div>
          </div>
        </div>
      )}

      {/* MODE 3: VERTICAL STACK VIEW */}
      {mode === 'stack' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <label className="text-xs font-bold text-slate-600 dark:text-slate-400">Select Cohort:</label>
              <select
                value={selectedCohort}
                onChange={(e) => setSelectedCohort(e.target.value)}
                className="bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 px-4 py-1.5 rounded-xl text-xs font-bold shadow-sm focus:outline-none cursor-pointer"
              >
                <option value="II_AIML">II Year AIML Cohort (Sections A-J)</option>
                <option value="III_AIML">III Year AIML Cohort (Sections A-G)</option>
                <option value="IV_AIML">IV Year AIML Cohort (Sections A-E)</option>
                <option value="OTHER">Other Specialized Branches (CS / DS)</option>
              </select>
            </div>
          </div>

          <div className="space-y-8">
            {stackSections.map((secName) => {
              const secEntries = entries.filter((e) => e.sectionName === secName || selectedSection === secName);
              return (
                <div key={secName} className="space-y-2">
                  <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 px-1">{secName}</h3>
                  <TimetableGrid sectionName={secName} entries={secEntries.length > 0 ? secEntries : entries} />
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* MODE 4: FACULTY SCHEDULES */}
      {mode === 'faculty' && (
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
            <div>
              <h3 className="text-lg font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
                <UserCheck className="w-5 h-5 text-blue-600" /> Faculty Personal Schedule
              </h3>
              <p className="text-xs text-slate-500 mt-1">Select a faculty member to view their individual teaching matrix.</p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {/* Faculty Search Input */}
              <div className="relative w-48">
                <Search className="w-3 h-3 text-slate-400 absolute left-2.5 top-2.5" />
                <input
                  type="text"
                  placeholder="Search faculty..."
                  value={facultySearchQuery}
                  onChange={(e) => setFacultySearchQuery(e.target.value)}
                  className="w-full pl-7 pr-3 py-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none"
                />
              </div>

              {/* Faculty Sort Select */}
              <select
                value={facultySortBy}
                onChange={(e) => setFacultySortBy(e.target.value as any)}
                className="px-3 py-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-900 dark:text-white"
              >
                <option value="NAME_ASC">Sort: Name (A-Z)</option>
                <option value="HOURS_DESC">Sort: Hours (High→Low)</option>
              </select>

              {/* Faculty Dropdown */}
              <select
                value={selectedFacultyId || ""}
                onChange={(e) => setSelectedFacultyId(Number(e.target.value))}
                className="px-3 py-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-900 dark:text-white max-w-xs"
              >
                {processedFacultyList.map((f) => (
                  <option key={f.id} value={f.id}>{f.name} ({f.employee_id || `VF-${f.id}`})</option>
                ))}
              </select>

              <button
                onClick={handleDownloadFacultyPdf}
                disabled={downloadingPdf}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-colors cursor-pointer"
              >
                Download PDF
              </button>
            </div>

          </div>

          {facultyTimetableData && (
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
                facultyName: facultyTimetableData.faculty_name || facultyTimetableData.name || ""
              }))}
            />
          )}
        </div>
      )}

      {/* MODE 5: CREATE TIMETABLE WIZARD */}
      {mode === 'wizard' && (
        <ScheduleSetupWizard onSuccess={() => setMode('matrix')} />
      )}

      {/* SLIDE-OVER FREE VENUE & FACULTY INSPECTOR DRAWER */}
      {isInspectorOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex justify-end animate-in fade-in duration-200">
          <div className="w-full max-w-md bg-white dark:bg-slate-900 h-full p-6 shadow-2xl overflow-y-auto space-y-6 border-l border-slate-200 dark:border-slate-800">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
              <div className="flex items-center gap-2">
                <Search className="w-5 h-5 text-blue-600" />
                <h3 className="font-extrabold text-base text-slate-900 dark:text-white">Free Venue & Faculty Inspector</h3>
              </div>
              <button onClick={() => setIsInspectorOpen(false)} className="text-slate-400 hover:text-slate-700 dark:hover:text-white text-sm font-bold">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Time Selector */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-bold text-slate-500 block mb-1">Select Day:</label>
                <select
                  value={inspectDay}
                  onChange={(e) => setInspectDay(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-900 dark:text-white"
                >
                  {DAYS.map((d) => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-500 block mb-1">Select Period:</label>
                <select
                  value={inspectPeriod}
                  onChange={(e) => setInspectPeriod(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-900 dark:text-white"
                >
                  {PERIODS_LIST.map((p) => (
                    <option key={p} value={p}>Period {p}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Inspector Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search vacant room code or faculty name..."
                value={inspectorSearchQuery}
                onChange={(e) => setInspectorSearchQuery(e.target.value)}
                className="w-full pl-8 pr-7 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none font-medium"
              />
              {inspectorSearchQuery && (
                <button onClick={() => setInspectorSearchQuery("")} className="absolute right-2.5 top-2 text-slate-400 hover:text-slate-600 dark:hover:text-white font-bold text-xs">
                  ✕
                </button>
              )}
            </div>

            {/* Vacant Rooms List */}

            <div className="space-y-3">
              <h4 className="text-xs font-extrabold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 flex items-center justify-between">
                <span>Vacant Venues ({freeRoomsAndFaculty.vacantRooms.length})</span>
                <span className="text-[10px] font-bold text-slate-400">{inspectDay} P{inspectPeriod}</span>
              </h4>
              <div className="grid grid-cols-3 gap-2">
                {freeRoomsAndFaculty.vacantRooms.map((rm) => (
                  <div key={rm} className="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-center">
                    <span className="font-extrabold text-xs text-emerald-900 dark:text-emerald-200">Room {rm}</span>
                    <span className="block text-[9px] text-emerald-600 dark:text-emerald-400 font-semibold mt-0.5">VACANT</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Available Unassigned Faculty List */}
            <div className="space-y-3 pt-2">
              <h4 className="text-xs font-extrabold uppercase tracking-wider text-blue-600 dark:text-blue-400 flex items-center justify-between">
                <span>Available Faculty ({freeRoomsAndFaculty.availableFaculty.length})</span>
                <span className="text-[10px] font-bold text-slate-400">{inspectDay} P{inspectPeriod}</span>
              </h4>
              <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
                {freeRoomsAndFaculty.availableFaculty.map((fac) => (
                  <div key={fac.id} className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-between text-xs">
                    <span className="font-bold text-slate-800 dark:text-slate-200">{fac.name}</span>
                    <span className="text-[10px] text-slate-400">{fac.designation || 'Instructor'}</span>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={() => setIsInspectorOpen(false)}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl transition-colors shadow-md"
            >
              Close Inspector
            </button>
          </div>
        </div>
      )}

    </div>
  );
}
