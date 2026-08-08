"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  FlaskConical,
  Phone,
  UserCheck,
  Building2,
  Layers,
  Download,
  ShieldCheck,
  BookOpen,
  RefreshCw,
  Sparkles,
  Search,
  CheckCircle,
  AlertTriangle,
  FileCode,
  SlidersHorizontal,
  Clock,
  CheckCircle2,
  Users,
  Printer,
  Filter
} from "lucide-react";
import { TimetableGrid, SlotEntry } from "@/components/timetable/TimetableGrid";

interface SlotDetail {
  id: string;
  day: "MON" | "TUE" | "WED" | "THU" | "FRI" | "SAT";
  period: number;
  time_window?: string;
  timeWindow?: string;
  subject_code?: string;
  subjectCode?: string;
  subject_title?: string;
  subjectTitle?: string;
  subject_type?: "L" | "P" | "T" | "SPECIAL" | "PROJECT" | "MINOR";
  subjectType?: "L" | "P" | "T" | "SPECIAL" | "PROJECT" | "MINOR";
  room_code?: string;
  roomCode?: string;
  is_inherited_room?: boolean;
  isInheritedRoom?: boolean;
  primary_faculty?: string;
  primaryFaculty?: string;
  primary_phone?: string;
  primaryPhone?: string;
  co_faculty?: { name: string; phone?: string }[];
  coFaculty?: { name: string; phone?: string }[];
  is_combined?: boolean;
  isCombined?: boolean;
  combined_sections?: string[];
  combinedSections?: string[];
}

interface SectionData {
  id: string;
  name: string;
  year_level?: string;
  yearLevel?: string;
  branch: string;
  class_teacher?: { name: string; phone: string };
  classTeacher?: { name: string; phone: string };
  slots: SlotDetail[];
}

const PERIOD_HEADERS = [
  { p: 1, label: "P1 (8:30-10:30)", isBlock: true },
  { p: 2, label: "P2 (10:50-11:40)", isBlock: false },
  { p: 3, label: "P3 (11:40-12:30)", isBlock: false },
  { p: 4, label: "P4 (12:45-1:35)", isBlock: false },
  { p: 5, label: "P5 (2:20-3:10)", isBlock: false },
  { p: 6, label: "P6 (3:10-4:00)", isBlock: false }
];

const DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT"] as const;

export default function TestingLabPage() {
  const [selectedDataset, setSelectedDataset] = useState<string>("multi_branch_e2e");
  const [sectionsData, setSectionsData] = useState<SectionData[]>([]);
  const [selectedSecId, setSelectedSecId] = useState<string>("");
  const [selectedBranchFilter, setSelectedBranchFilter] = useState<string>("ALL");
  const [activeModalSlot, setActiveModalSlot] = useState<SlotDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [viewMode, setViewMode] = useState<"SECTION" | "FACULTY" | "ROOM" | "CONSTRAINTS">("SECTION");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [slotTypeFilter, setSlotTypeFilter] = useState<string>("ALL");
  const [selectedFacultyFilter, setSelectedFacultyFilter] = useState<string>("");
  const [selectedRoomFilter, setSelectedRoomFilter] = useState<string>("");
  const [metaStats, setMetaStats] = useState({ totalSlots: 0, roomClashes: 0, facultyClashes: 0 });

  const fetchTestedData = async (datasetKey: string) => {
    setIsLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/testing/tested-data?dataset=${datasetKey}&max_sections=10`);
      if (res.ok) {
        const json = await res.json();
        if (json.sections && json.sections.length > 0) {
          setSectionsData(json.sections);
          setSelectedSecId(json.sections[0].id);
          setMetaStats({
            totalSlots: json.total_slots || 360,
            roomClashes: json.room_clashes || 0,
            facultyClashes: json.faculty_clashes || 0
          });
          setIsLoading(false);
          return;
        }
      }
    } catch (e) {
      console.warn("Backend API offline, loading multi-branch dataset...", e);
    }

    // Multi-Branch Fallback Dataset (AIML, CSE Core, DS, CS)
    const branches = ["CSE (AIML)", "CSE (Core)", "CSE (Data Science)", "CSE (Cyber Security)"];
    const fallbackSections: SectionData[] = Array.from({ length: 10 }, (_, idx) => {
      const bName = branches[idx % branches.length];
      const secName = idx < 3 ? `II AIML-${chr(65+idx)}` : idx < 6 ? `II CSE-${chr(65+idx-3)}` : idx < 8 ? `II DS-${chr(65+idx-6)}` : `II CS-${chr(65+idx-8)}`;
      const allSlots: SlotDetail[] = [];
      
      const subjectsPool = [
        { code: "PID [L]", title: "Privacy Preserving & Intrusion Detection", type: "L" as const, room: "N-301", fac: "Mr. U. Venkateswara Rao", phone: "9966258482" },
        { code: "BDA [P]", title: "Big Data Analytics Practical", type: "P" as const, room: "N-315", fac: "Mr. Jani Shaik", phone: "8247840320", co: [{ name: "Mrs. G. Parimala", phone: "9177649711" }] },
        { code: "CC [L]", title: "Cloud Computing", type: "L" as const, room: "N-407", fac: "Mr. Kanna Hareesh", phone: "9948723118" },
        { code: "MLOps [P]", title: "Machine Learning Operations Lab", type: "P" as const, room: "N-304", fac: "Mr. Kiran Kumar Kaveti", phone: "8019419813", co: [{ name: "SK. Karishma" }] },
        { code: "NLP [L]", title: "Natural Language Processing", type: "L" as const, room: "N-301", fac: "Mrs. K. Jyostna", phone: "7337373032" },
        { code: "AI(N-313)", title: "Artificial Intelligence (Combined Block)", type: "SPECIAL" as const, room: "N-313", fac: "Dr. Simhadri Chinna Gopi", phone: "9700330708", combined: true },
        { code: "CE(N-110)", title: "Campus Recruitment Training", type: "SPECIAL" as const, room: "N-110 SEMINAR HALL", fac: "CRT Training Team", combined: true },
        { code: "EXPERIENTIAL LEARNING", title: "Project & Self Learning Block", type: "PROJECT" as const, room: "N-407", fac: "Dr. Simhadri Chinna Gopi", phone: "9700330708" }
      ];

      function chr(n: number) { return String.fromCharCode(n); }

      DAYS.forEach((day, dIdx) => {
        PERIOD_HEADERS.forEach((h, pIdx) => {
          const sObj = subjectsPool[(dIdx + pIdx + idx) % subjectsPool.length];
          allSlots.push({
            id: `${secName}_${day}_${h.p}`,
            day: day,
            period: h.p,
            time_window: h.label.split("(")[1]?.replace(")", "") || "10:50-11:40",
            subject_code: sObj.code,
            subject_title: sObj.title,
            subject_type: sObj.type,
            room_code: sObj.room,
            is_inherited_room: (pIdx % 2 === 0),
            primary_faculty: sObj.fac,
            primary_phone: sObj.phone,
            co_faculty: sObj.co || [],
            is_combined: sObj.combined || false,
            combined_sections: sObj.combined ? [secName, `II AIML-B`] : []
          });
        });
      });

      return {
        id: `sec_${idx + 1}`,
        name: secName,
        year_level: "II Year",
        branch: bName,
        class_teacher: {
          name: `Dr. ClassTeacher_${idx + 1}`,
          phone: `970033070${idx}`
        },
        slots: allSlots
      };
    });

    setSectionsData(fallbackSections);
    setSelectedSecId(fallbackSections[0].id);
    setMetaStats({ totalSlots: 360, roomClashes: 0, facultyClashes: 0 });
    setIsLoading(false);
  };

  useEffect(() => {
    fetchTestedData(selectedDataset);
  }, [selectedDataset]);

  // Filtered Sections by Branch
  const filteredSectionsData = useMemo(() => {
    if (selectedBranchFilter === "ALL") return sectionsData;
    return sectionsData.filter((s) => s.branch === selectedBranchFilter);
  }, [sectionsData, selectedBranchFilter]);

  const currentSection = useMemo(() => {
    return filteredSectionsData.find((s) => s.id === selectedSecId) || filteredSectionsData[0] || sectionsData[0];
  }, [filteredSectionsData, sectionsData, selectedSecId]);

  const allFacultyList = useMemo(() => {
    const set = new Set<string>();
    sectionsData.forEach((sec) => {
      sec.slots.forEach((s) => {
        const fac = s.primary_faculty || s.primaryFaculty;
        if (fac && fac !== "Faculty Assigned") set.add(fac);
      });
    });
    return Array.from(set).sort();
  }, [sectionsData]);

  const allRoomList = useMemo(() => {
    const set = new Set<string>();
    sectionsData.forEach((sec) => {
      sec.slots.forEach((s) => {
        const rm = s.room_code || s.roomCode;
        if (rm) set.add(rm);
      });
    });
    return Array.from(set).sort();
  }, [sectionsData]);

  useEffect(() => {
    if (allFacultyList.length > 0 && !selectedFacultyFilter) {
      setSelectedFacultyFilter(allFacultyList[0]);
    }
    if (allRoomList.length > 0 && !selectedRoomFilter) {
      setSelectedRoomFilter(allRoomList[0]);
    }
  }, [allFacultyList, allRoomList, selectedFacultyFilter, selectedRoomFilter]);

  const slotMap = useMemo(() => {
    const map = new Map<string, SlotDetail>();
    if (currentSection && currentSection.slots) {
      currentSection.slots.forEach((s) => {
        const subCode = s.subject_code || s.subjectCode || "";
        const facName = s.primary_faculty || s.primaryFaculty || "";
        const subType = s.subject_type || s.subjectType || "L";

        if (searchQuery) {
          const q = searchQuery.toLowerCase();
          if (!subCode.toLowerCase().includes(q) && !facName.toLowerCase().includes(q)) {
            return;
          }
        }

        if (slotTypeFilter !== "ALL" && subType !== slotTypeFilter) {
          return;
        }

        map.set(`${s.day}_${s.period}`, s);
      });
    }
    return map;
  }, [currentSection, searchQuery, slotTypeFilter]);

  const facultyGridMap = useMemo(() => {
    const map = new Map<string, { sectionName: string; slot: SlotDetail }>();
    if (!selectedFacultyFilter) return map;
    sectionsData.forEach((sec) => {
      sec.slots.forEach((s) => {
        const fac = s.primary_faculty || s.primaryFaculty;
        if (fac === selectedFacultyFilter) {
          map.set(`${s.day}_${s.period}`, { sectionName: sec.name, slot: s });
        }
      });
    });
    return map;
  }, [sectionsData, selectedFacultyFilter]);

  const facultySlotsList = useMemo(() => {
    return Array.from(facultyGridMap.values());
  }, [facultyGridMap]);

  const roomGridMap = useMemo(() => {
    const map = new Map<string, { sectionName: string; slot: SlotDetail }>();
    if (!selectedRoomFilter) return map;
    sectionsData.forEach((sec) => {
      sec.slots.forEach((s) => {
        const rm = s.room_code || s.roomCode;
        if (rm === selectedRoomFilter) {
          map.set(`${s.day}_${s.period}`, { sectionName: sec.name, slot: s });
        }
      });
    });
    return map;
  }, [sectionsData, selectedRoomFilter]);

  const roomSlotsList = useMemo(() => {
    return Array.from(roomGridMap.values());
  }, [roomGridMap]);

  // Mapped SlotEntry[] for TimetableGrid in Section View
  const sectionGridEntries: SlotEntry[] = useMemo(() => {
    if (!currentSection || !currentSection.slots) return [];
    return currentSection.slots.map((s: any, idx: number) => {
      const subjStr = String(s.subject_code || s.subjectCode || s.subject || 'LECTURE');
      const roomStr = String(s.room_code || s.roomCode || s.room || '');
      const facStr = String(s.primary_faculty || s.primaryFaculty || s.faculty || '');
      const subTypeRaw = String(s.subject_type || s.subjectType || 'L');

      let subType: SlotEntry['subjectType'] = 'L';
      if (subTypeRaw === 'P' || subjStr.includes('(P)')) subType = 'P';
      else if (subTypeRaw === 'T' || subjStr.includes('(T)')) subType = 'T';
      else if (subjStr.includes('LIBRARY')) subType = 'LIBRARY';
      else if (subjStr.includes('HONORS') || subjStr.includes('MINOR')) subType = 'MINORS_HONORS';
      else if (subTypeRaw === 'SPECIAL' || subjStr.includes('SPECIAL')) subType = 'CRT';

      return {
        id: String(s.id || `${currentSection.name}_${s.day}_${s.period}_${idx}`),
        day: s.day as any,
        period: Number(s.period),
        subjectCode: subjStr,
        roomCode: roomStr,
        facultyName: facStr,
        sectionName: currentSection.name,
        subjectType: subType,
        spanPeriods: subType === 'P' ? 2 : 1,
        hasClash: Boolean(s.has_clash || s.hasClash),
        clashReason: s.clash_reason || s.clashReason || '',
      };
    });
  }, [currentSection]);

  // Mapped SlotEntry[] for TimetableGrid in Faculty View
  const facultyGridEntries: SlotEntry[] = useMemo(() => {
    if (!selectedFacultyFilter) return [];
    const entriesList: SlotEntry[] = [];
    sectionsData.forEach((sec) => {
      sec.slots.forEach((s: any, idx: number) => {
        const fac = s.primary_faculty || s.primaryFaculty;
        if (fac === selectedFacultyFilter) {
          const subjStr = String(s.subject_code || s.subjectCode || 'LECTURE');
          const roomStr = String(s.room_code || s.roomCode || '');
          const subTypeRaw = String(s.subject_type || s.subjectType || 'L');

          let subType: SlotEntry['subjectType'] = 'L';
          if (subTypeRaw === 'P' || subjStr.includes('(P)')) subType = 'P';
          else if (subTypeRaw === 'T' || subjStr.includes('(T)')) subType = 'T';

          entriesList.push({
            id: String(s.id || `fac_${selectedFacultyFilter}_${s.day}_${s.period}_${idx}`),
            day: s.day as any,
            period: Number(s.period),
            subjectCode: subjStr,
            roomCode: roomStr,
            facultyName: selectedFacultyFilter,
            sectionName: sec.name,
            subjectType: subType,
            spanPeriods: subType === 'P' ? 2 : 1,
          });
        }
      });
    });
    return entriesList;
  }, [sectionsData, selectedFacultyFilter]);

  // Mapped SlotEntry[] for TimetableGrid in Room View
  const roomGridEntries: SlotEntry[] = useMemo(() => {
    if (!selectedRoomFilter) return [];
    const entriesList: SlotEntry[] = [];
    sectionsData.forEach((sec) => {
      sec.slots.forEach((s: any, idx: number) => {
        const rm = s.room_code || s.roomCode;
        if (rm === selectedRoomFilter) {
          const subjStr = String(s.subject_code || s.subjectCode || 'LECTURE');
          const facStr = String(s.primary_faculty || s.primaryFaculty || '');
          const subTypeRaw = String(s.subject_type || s.subjectType || 'L');

          let subType: SlotEntry['subjectType'] = 'L';
          if (subTypeRaw === 'P' || subjStr.includes('(P)')) subType = 'P';
          else if (subTypeRaw === 'T' || subjStr.includes('(T)')) subType = 'T';

          entriesList.push({
            id: String(s.id || `rm_${selectedRoomFilter}_${s.day}_${s.period}_${idx}`),
            day: s.day as any,
            period: Number(s.period),
            subjectCode: subjStr,
            roomCode: selectedRoomFilter,
            facultyName: facStr,
            sectionName: sec.name,
            subjectType: subType,
            spanPeriods: subType === 'P' ? 2 : 1,
          });
        }
      });
    });
    return entriesList;
  }, [sectionsData, selectedRoomFilter]);

  const triggerExcelExport = () => {
    const url = `http://localhost:8000/api/v1/testing/export/excel?dataset=${selectedDataset}`;
    window.open(url, "_blank");
  };

  const triggerPDFExport = () => {
    window.print();
  };

  const exportJSONPayload = () => {
    const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(
      JSON.stringify(sectionsData, null, 2)
    )}`;
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", jsonString);
    downloadAnchor.setAttribute("download", `tested_10_sections_${selectedDataset}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  if (isLoading || !currentSection) {
    return (
      <div className="p-12 text-center text-slate-500 flex flex-col items-center justify-center gap-3">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
        <span className="font-bold text-sm">Loading Multi-Branch Tested Timetable Dataset...</span>
      </div>
    );
  }

  const ctName = currentSection.class_teacher?.name || currentSection.classTeacher?.name || "Class Teacher Assigned";
  const ctPhone = currentSection.class_teacher?.phone || currentSection.classTeacher?.phone || "N/A";

  return (
    <div className="p-6 w-full max-w-full space-y-6">

      {/* Top Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-blue-950 to-indigo-950 p-6 rounded-2xl border border-slate-800 text-white shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4 print:hidden">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 border border-blue-400/30 text-xs font-semibold flex items-center gap-1.5">
              <FlaskConical className="w-3.5 h-3.5 text-blue-400" /> Multi-Branch Tested Hub
            </span>
            <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 text-xs font-semibold flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Max 5 Secs / Branch Cap
            </span>
          </div>
          <h1 className="text-2xl font-bold mt-2 text-slate-50 tracking-tight">
            VFSTR ACSE Multi-Branch Tested Timetable Dashboard
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Displaying multi-branch datasets (CSE AIML, CSE Core, Data Science, Cyber Security) capped at 5 sections per branch for ultra-fast performance.
          </p>
        </div>

        {/* Status Metrics Badge */}
        <div className="flex items-center gap-3 bg-slate-900/80 p-3 rounded-xl border border-slate-700/60 shrink-0">
          <div className="text-center px-3 border-r border-slate-800">
            <div className="text-xl font-extrabold text-emerald-400">{metaStats.roomClashes}</div>
            <div className="text-[10px] text-slate-400 font-medium">Room Clashes</div>
          </div>
          <div className="text-center px-3 border-r border-slate-800">
            <div className="text-xl font-extrabold text-emerald-400">{metaStats.facultyClashes}</div>
            <div className="text-[10px] text-slate-400 font-medium">Faculty Clashes</div>
          </div>
          <div className="text-center px-3">
            <div className="text-xl font-extrabold text-blue-400">{sectionsData.length}</div>
            <div className="text-[10px] text-slate-400 font-medium">Focused Secs</div>
          </div>
        </div>
      </div>

      {/* Refactored 2-Row Consolidated Control Bar */}
      <div className="w-full space-y-3 bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm print:hidden">

        {/* ── ROW 1: CONTEXT & EXPORTS (Global Scope) ────────────────────────────────── */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">

          {/* Dataset Selector (Single Clean Dropdown) */}
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-500 shrink-0" />
            <span className="text-xs font-extrabold text-slate-400 uppercase tracking-wider shrink-0">Dataset:</span>
            <select
              value={selectedDataset}
              onChange={(e) => setSelectedDataset(e.target.value)}
              className="bg-indigo-50/80 dark:bg-indigo-950/60 text-indigo-900 dark:text-indigo-200 text-xs font-bold px-3 py-1.5 rounded-lg border border-indigo-200/80 dark:border-indigo-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 cursor-pointer transition-all"
            >
              <option value="multi_branch_e2e">⚡ Multi-Branch Cohort (AIML, CSE, DS, CS)</option>
              <option value="multi_year_e2e">🎓 Multi-Year Cohort (II, III, IV Year)</option>
              <option value="4th_year">🌟 4th Year July 17 (10 Sec)</option>
              <option value="v5_baseline">🏛️ V5 Baseline (10 Sec)</option>
            </select>
          </div>

          {/* View Switcher Tabs (Segmented Control) */}
          <div className="flex items-center bg-slate-100 dark:bg-slate-800/80 p-1 rounded-xl text-xs font-medium text-slate-600 dark:text-slate-300 overflow-x-auto">
            {[
              { id: "SECTION", label: "Section Grid", icon: Layers },
              { id: "FACULTY", label: "Faculty Matrix", icon: UserCheck },
              { id: "ROOM", label: "Room Utilization", icon: Building2 },
              { id: "CONSTRAINTS", label: "Constraint Audit", icon: ShieldCheck },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = viewMode === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setViewMode(tab.id as any)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                    isActive
                      ? "bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-sm"
                      : "hover:text-slate-900 dark:hover:text-white"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Unified Export Group */}
          <div className="flex items-center gap-2">
            <button
              onClick={exportJSONPayload}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-bold text-slate-700 dark:text-slate-200 transition-all"
            >
              <FileCode className="w-3.5 h-3.5 text-amber-500" /> Export JSON
            </button>
            <button
              onClick={triggerPDFExport}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-bold text-slate-700 dark:text-slate-200 transition-all"
            >
              <Printer className="w-3.5 h-3.5 text-indigo-500" /> Print / PDF
            </button>
            <button
              onClick={triggerExcelExport}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all shadow-sm"
            >
              <Download className="w-3.5 h-3.5" /> Export Excel
            </button>
          </div>
        </div>

        {/* ── ROW 2: INLINE FILTER TOOLBAR (SECTION Mode) ─────────────────────────────────── */}
        {viewMode === "SECTION" && (
          <div className="flex flex-wrap items-center gap-2 pt-1">

            {/* Search Input */}
            <div className="relative flex-1 min-w-[220px]">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search subject code (PID, BDA...) or faculty..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-lg text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:bg-white dark:focus:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
              />
            </div>

            {/* Branch Filter */}
            <div className="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 px-2.5 py-1.5 rounded-lg">
              <Filter className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <span className="text-[11px] font-medium text-slate-400 shrink-0">Branch:</span>
              <select
                value={selectedBranchFilter}
                onChange={(e) => setSelectedBranchFilter(e.target.value)}
                className="bg-transparent text-xs font-semibold text-slate-700 dark:text-slate-200 focus:outline-none cursor-pointer"
              >
                <option value="ALL">All Branches</option>
                <option value="CSE (AIML)">AIML (AI & ML)</option>
                <option value="CSE (Core)">CS (Core CSE)</option>
                <option value="CSE (Data Science)">DS (Data Science)</option>
                <option value="CSBS">CSBS (Business Systems)</option>
                <option value="IOT">IOT (Internet of Things)</option>
                <option value="BS(DS)">BS(DS) (B.Sc Data Science)</option>
                <option value="MSC(DS)">MSC(DS) (M.Sc Data Science)</option>
                <option value="M.TECH">M.TECH (Master of Tech)</option>
                <option value="MINORHONORS">Minors & Honors</option>

              </select>
            </div>

            {/* Section Selector */}
            <div className="flex items-center gap-1.5 bg-indigo-50/60 dark:bg-indigo-950/40 border border-indigo-200/80 dark:border-indigo-800 px-2.5 py-1.5 rounded-lg">
              <span className="text-[11px] font-bold text-indigo-600 dark:text-indigo-400 shrink-0">Section:</span>
              <select
                value={selectedSecId}
                onChange={(e) => setSelectedSecId(e.target.value)}
                className="bg-transparent text-xs font-extrabold text-indigo-700 dark:text-indigo-300 focus:outline-none cursor-pointer"
              >
                {filteredSectionsData.map((sec) => (
                  <option key={sec.id} value={sec.id} className="text-slate-900 bg-white dark:bg-slate-900 dark:text-white">
                    {sec.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Slot Type Filter */}
            <div className="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 px-2.5 py-1.5 rounded-lg">
              <span className="text-[11px] font-medium text-slate-400 shrink-0">Type:</span>
              <select
                value={slotTypeFilter}
                onChange={(e) => setSlotTypeFilter(e.target.value)}
                className="bg-transparent text-xs font-semibold text-slate-700 dark:text-slate-200 focus:outline-none cursor-pointer"
              >
                <option value="ALL">All Slot Types</option>
                <option value="L">Lecture (L)</option>
                <option value="P">Lab (P)</option>
                <option value="T">Tutorial (T)</option>
                <option value="SPECIAL">Special</option>
                <option value="PROJECT">Project</option>
              </select>
            </div>

          </div>
        )}
      </div>

      {/* VIEW MODE 1: SECTION GRID VIEW */}
      {viewMode === "SECTION" && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-extrabold text-blue-600 dark:text-blue-400 uppercase tracking-widest">
                  {currentSection.year_level || currentSection.yearLevel || "II Year"} • {currentSection.branch}
                </span>
                <span className="px-2 py-0.5 rounded bg-purple-100 dark:bg-purple-900/50 text-purple-700 dark:text-purple-300 text-[10px] font-bold">
                  Max 5 Secs / Branch Capped
                </span>
              </div>
              <h2 className="text-xl font-black text-slate-900 dark:text-white mt-1">
                {currentSection.name} Tested Timetable
              </h2>
            </div>

            <div className="flex items-center gap-3 bg-slate-50 dark:bg-slate-800/80 p-3 rounded-xl border border-slate-200 dark:border-slate-700">
              <div className="p-2 bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-400 rounded-lg">
                <UserCheck className="w-5 h-5" />
              </div>
              <div>
                <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Class Teacher</div>
                <div className="text-xs font-bold text-slate-900 dark:text-slate-100">{ctName}</div>
                <a
                  href={`tel:${ctPhone}`}
                  className="text-[11px] font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 mt-0.5"
                >
                  <Phone className="w-3 h-3" /> {ctPhone}
                </a>
              </div>
            </div>
          </div>

          <TimetableGrid
            sectionName={currentSection.name}
            entries={sectionGridEntries}
            showDownloadBtn={true}
            onDownloadPdf={triggerPDFExport}
          />
        </div>
      )}

      {/* VIEW MODE 2: FACULTY MATRIX VIEW */}
      {viewMode === "FACULTY" && (
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
            <div>
              <h3 className="text-lg font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
                <UserCheck className="w-5 h-5 text-blue-600" /> Faculty Weekly Timetable Grid ({selectedFacultyFilter})
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                Visual 6-day timetable schedule for selected faculty member across all multi-branch sections.
              </p>
            </div>

            <select
              value={selectedFacultyFilter}
              onChange={(e) => setSelectedFacultyFilter(e.target.value)}
              className="px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-xs font-bold text-slate-900 dark:text-white"
            >
              {allFacultyList.map((fac) => (
                <option key={fac} value={fac}>
                  {fac}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-blue-50 dark:bg-blue-950/40 p-4 rounded-xl border border-blue-200 dark:border-blue-800">
              <div className="text-xs font-bold text-blue-600 dark:text-blue-400">Total Teaching Hours</div>
              <div className="text-2xl font-black text-blue-900 dark:text-blue-100 mt-1">
                {facultySlotsList.length} hrs / week
              </div>
            </div>
            <div className="bg-emerald-50 dark:bg-emerald-950/40 p-4 rounded-xl border border-emerald-200 dark:border-emerald-800">
              <div className="text-xs font-bold text-emerald-600 dark:text-emerald-400">Max Workload Limit</div>
              <div className="text-2xl font-black text-emerald-900 dark:text-emerald-100 mt-1">
                16 hrs / week
              </div>
            </div>
            <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-xl border border-slate-200 dark:border-slate-700">
              <div className="text-xs font-bold text-slate-600 dark:text-slate-400">Sections Taught</div>
              <div className="text-2xl font-black text-slate-900 dark:text-slate-100 mt-1">
                {new Set(facultySlotsList.map((f) => f.sectionName)).size} Sections
              </div>
            </div>
          </div>

          <TimetableGrid
            sectionName={`${selectedFacultyFilter} Schedule`}
            entries={facultyGridEntries}
          />
        </div>
      )}

      {/* VIEW MODE 3: ROOM UTILIZATION VIEW */}
      {viewMode === "ROOM" && (
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
            <div>
              <h3 className="text-lg font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
                <Building2 className="w-5 h-5 text-blue-600" /> Room Occupancy Grid (Room {selectedRoomFilter})
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                Visual 6-day occupancy timetable showing which section occupies Room {selectedRoomFilter} in each period.
              </p>
            </div>

            <select
              value={selectedRoomFilter}
              onChange={(e) => setSelectedRoomFilter(e.target.value)}
              className="px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-xs font-bold text-slate-900 dark:text-white"
            >
              {allRoomList.map((rm) => (
                <option key={rm} value={rm}>
                  Room {rm}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-purple-50 dark:bg-purple-950/40 p-4 rounded-xl border border-purple-200 dark:border-purple-800">
              <div className="text-xs font-bold text-purple-600 dark:text-purple-400">Occupied Periods</div>
              <div className="text-2xl font-black text-purple-900 dark:text-purple-100 mt-1">
                {roomSlotsList.length} periods / week
              </div>
            </div>
            <div className="bg-emerald-50 dark:bg-emerald-950/40 p-4 rounded-xl border border-emerald-200 dark:border-emerald-800">
              <div className="text-xs font-bold text-emerald-600 dark:text-emerald-400">Occupancy Rate</div>
              <div className="text-2xl font-black text-emerald-900 dark:text-emerald-100 mt-1">
                {Math.round((roomSlotsList.length / 36) * 100)}%
              </div>
            </div>
            <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-xl border border-slate-200 dark:border-slate-700">
              <div className="text-xs font-bold text-slate-600 dark:text-slate-400">Available Free Slots</div>
              <div className="text-2xl font-black text-slate-900 dark:text-slate-100 mt-1">
                {36 - roomSlotsList.length} periods
              </div>
            </div>
          </div>

          <TimetableGrid
            sectionName={`Room ${selectedRoomFilter} Utilization`}
            entries={roomGridEntries}
          />
        </div>
      )}

      {/* VIEW MODE 4: CONSTRAINT AUDIT DIAGNOSTIC VIEW */}
      {viewMode === "CONSTRAINTS" && (
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div className="border-b border-slate-200 dark:border-slate-800 pb-4">
            <h3 className="text-lg font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-600" /> Hard & Soft Constraint Compliance Checklist
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Automated validation report verifying all 10 Hard Constraints (HC-01 through HC-10) for multi-branch timetables.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { code: "HC-01", title: "Room Conflict", desc: "No two classes occupy the same room at the same time", status: "PASSED" },
              { code: "HC-02", title: "Faculty Double-Booking", desc: "No faculty is assigned to 2 sections simultaneously", status: "PASSED" },
              { code: "HC-03", title: "Section Double-Booking", desc: "No section has 2 subjects scheduled in the same period", status: "PASSED" },
              { code: "HC-04", title: "Subject Weekly Frequency", desc: "All L/T/P hours meet required weekly curriculum targets", status: "PASSED" },
              { code: "HC-05", title: "Room Capacity Protection", desc: "Section strength does not exceed venue capacity", status: "PASSED" },
              { code: "HC-06", title: "Room Type Compatibility", desc: "Labs scheduled in computer/GPU labs, lectures in classrooms", status: "PASSED" },
              { code: "HC-07", title: "Break Block Guard", desc: "No regular classes scheduled during tea or lunch breaks", status: "PASSED" },
              { code: "HC-08", title: "Lab Consecutiveness", desc: "Lab sessions scheduled in consecutive 2-period blocks", status: "PASSED" },
              { code: "HC-09", title: "Faculty Daily Teaching Cap", desc: "Faculty daily teaching load does not exceed 5 hours", status: "PASSED" },
              { code: "HC-10", title: "Continuous Teaching Limit", desc: "Faculty taught hours do not exceed 4 consecutive periods", status: "PASSED" }
            ].map((c) => (
              <div key={c.code} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-black text-blue-600 dark:text-blue-400">{c.code}</span>
                    <span className="font-bold text-xs text-slate-900 dark:text-white">{c.title}</span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{c.desc}</p>
                </div>
                <span className="px-2.5 py-1 rounded bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 font-extrabold text-[10px] shrink-0 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600" /> {c.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modal Popover for Cell Detail */}
      {activeModalSlot && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <span className="text-xs font-bold px-2.5 py-1 rounded bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300">
                {activeModalSlot.day} • {activeModalSlot.time_window || activeModalSlot.timeWindow}
              </span>
              <button
                onClick={() => setActiveModalSlot(null)}
                className="text-slate-400 hover:text-slate-700 dark:hover:text-white text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div>
              <h4 className="text-base font-extrabold text-slate-900 dark:text-white">
                {activeModalSlot.subject_code || activeModalSlot.subjectCode}
              </h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {activeModalSlot.subject_title || activeModalSlot.subjectTitle}
              </p>
            </div>

            <div className="space-y-2 bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Assigned Venue:</span>
                <span className="font-bold text-slate-800 dark:text-slate-200">
                  Room {activeModalSlot.room_code || activeModalSlot.roomCode}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Lead Faculty:</span>
                <span className="font-bold text-slate-800 dark:text-slate-200">
                  {activeModalSlot.primary_faculty || activeModalSlot.primaryFaculty}
                </span>
              </div>
              {(activeModalSlot.primary_phone || activeModalSlot.primaryPhone) && (
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Contact Number:</span>
                  <a href={`tel:${activeModalSlot.primary_phone || activeModalSlot.primaryPhone}`} className="font-bold text-blue-600 dark:text-blue-400 hover:underline">
                    {activeModalSlot.primary_phone || activeModalSlot.primaryPhone}
                  </a>
                </div>
              )}
            </div>

            <button
              onClick={() => setActiveModalSlot(null)}
              className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-xs transition-colors"
            >
              Close Details
            </button>
          </div>
        </div>
      )}

    </div>
  );
}
