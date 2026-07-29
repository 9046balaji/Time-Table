"use client";

import React, { useMemo, useState } from "react";
import { Download } from "lucide-react";

export interface SlotEntry {
  id: string;
  day: "MON" | "TUE" | "WED" | "THU" | "FRI" | "SAT";
  period: number;
  subjectCode: string;
  roomCode: string;
  facultyName?: string;
  facultyNames?: string[];
  sectionName?: string;
  subjectType: "L" | "P" | "T" | "LIBRARY" | "IDP" | "MINORS_HONORS" | "SL_EL" | "OE" | "CRT" | "QALR" | "BREAK" | "LUNCH";
  spanPeriods?: number;
  hasClash?: boolean;
  clashReason?: string;
}

interface TimetableGridProps {
  sectionName: string;
  entries: SlotEntry[];
  onCellClick?: (entry: SlotEntry) => void;
  onSlotSwap?: (draggedEntryId: string, targetDay: string, targetPeriod: number) => void;
  showDownloadBtn?: boolean;
  onDownloadPdf?: () => void;
}

const PERIODS = [
  { id: 1,    label: "1", time: "8:15-9:05" },
  { id: 2,    label: "2", time: "9:05-09:55" },
  { id: null, label: "09:55-10:10", time: "09:55-10:10", isBreak: true },
  { id: 3,    label: "3", time: "10:10-11:00" },
  { id: 4,    label: "4", time: "11:00-11:50" },
  { id: 5,    label: "5", time: "11:50-12:40" },
  { id: null, label: "12:40-1:40",  time: "12:40-1:40",  isBreak: true },
  { id: 6,    label: "6", time: "1:40-2:30" },
  { id: 7,    label: "7", time: "2:30-3:20" },
  { id: 8,    label: "8", time: "3:20-4:05" },
] as const;

const DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT"] as const;

const SUBJECT_NAMES: Record<string, string> = {
  DS:          "Data Structures",
  DBMS:        "Data Base Management Systems",
  AI:          "Artificial Intelligence Search Methods for Problem Solving",
  OOPS:        "Object Oriented Programming",
  SFCDS:       "Statistical Foundation for Computing and Data Science",
  DMS:         "Discrete Mathematical Structures",
  DEF:         "Data Engineering Foundations",
  DL:          "Deep Learning & Neural Networks",
  WT:          "Web Technologies",
  CV:          "Computer Vision & Image Processing",
  ADS:         "Advanced Data Structures & Algorithms",
  MLOP:        "MLOps & AI Model Deployment",
  IDP:         "Interdisciplinary Project",
  CNS:         "Cryptography & Network Security",
  TM:          "Technical Modules",
  GENAI:       "Generative AI & LLMs",
  IOT:         "Internet of Things & Sensor Networks",
  QALR:        "Quantitative Aptitude & Logical Reasoning",
  KRR:         "Knowledge Representation & Reasoning",
  "Ethics-AI": "Ethics in Artificial Intelligence",
  OE:          "Open Elective Course",
  CRT:         "Campus Recruitment Training",
};

type SubjectEntry = {
  code: string;
  fullName: string;
  type: "L" | "T" | "P" | "T&P";
  faculty: string;
};

const SKIP_CODES = new Set(["BREAK", "LUNCH", "LIBRARY", "SL/EL", "IDP", "MINORS_HONORS", "CRT", "SL_EL"]);

function shortFacultyName(entry: SlotEntry): string {
  const rawVal =
    Array.isArray(entry.facultyNames) && entry.facultyNames.length > 0
      ? entry.facultyNames[0]
      : entry.facultyName || "";
  const raw = typeof rawVal === "string" ? rawVal.trim() : String(rawVal || "").trim();
  if (!raw || raw === "undefined" || raw === "null") return "";
  const parts = raw.split(/\s+/);
  if (parts.length <= 2) return raw;
  const title = parts[0].match(/^(Dr|Mr|Ms|Prof)\.?$/i) ? parts[0] + " " : "";
  return title + parts[parts.length - 1];
}

function fullFacultyNames(entry: SlotEntry): string {
  if (Array.isArray(entry.facultyNames) && entry.facultyNames.length > 0) {
    return entry.facultyNames.map(f => typeof f === "string" ? f : String(f || "")).filter(Boolean).join(", ");
  }
  const raw = typeof entry.facultyName === "string" ? entry.facultyName : String(entry.facultyName || "");
  return raw && raw !== "undefined" && raw !== "null" ? raw : "";
}

function slotBg(entry: SlotEntry | undefined): string {
  if (!entry) return "bg-white dark:bg-slate-900";
  if (entry.hasClash) return "bg-red-50 dark:bg-red-950/50 border-l-4 border-l-red-500";
  switch (entry.subjectType) {
    case "P":             return "bg-violet-50 dark:bg-violet-950/40";
    case "T":             return "bg-emerald-50 dark:bg-emerald-950/40";
    case "LIBRARY":       return "bg-amber-50 dark:bg-amber-950/40";
    case "MINORS_HONORS": return "bg-indigo-50 dark:bg-indigo-950/40";
    default:              return "bg-blue-50/60 dark:bg-blue-950/20";
  }
}

export const TimetableGrid: React.FC<TimetableGridProps> = ({
  sectionName,
  entries,
  onCellClick,
  onSlotSwap,
  showDownloadBtn,
  onDownloadPdf,
}) => {
  const [draggedSlotId, setDraggedSlotId] = useState<string | null>(null);

  const slotMap = useMemo(() => {
    const map = new Map<string, SlotEntry>();
    entries.forEach((e) => map.set(`${e.day}_${e.period}`, e));
    return map;
  }, [entries]);

  const allocationRows = useMemo((): SubjectEntry[] => {
    const map = new Map<string, SubjectEntry>();
    entries.forEach((e) => {
      if (!e || !e.subjectCode) return;
      const strCode = typeof e.subjectCode === "string" ? e.subjectCode : String(e.subjectCode || "");
      const rawCode = strCode
        .replace("(P)", "").replace("(T&P)", "").replace("(T)", "").trim();
      if (!rawCode || SKIP_CODES.has(rawCode)) return;

      const hasTaP = strCode.includes("(T&P)");
      const hasP   = strCode.includes("(P)") || e.subjectType === "P";
      const hasT   = strCode.includes("(T)") || e.subjectType === "T";
      const type: SubjectEntry["type"] = hasTaP ? "T&P" : hasP ? "P" : hasT ? "T" : "L";
      const key = `${rawCode}__${type}`;
      const facs = fullFacultyNames(e);
      const fullName = SUBJECT_NAMES[rawCode] || rawCode;

      const existing = map.get(key);
      if (!existing) {
        map.set(key, { code: rawCode, fullName, type, faculty: facs });
      } else if (!existing.faculty && facs) {
        map.set(key, { ...existing, faculty: facs });
      } else if (existing.faculty && facs && !existing.faculty.includes(facs)) {
        map.set(key, { ...existing, faculty: existing.faculty + ", " + facs });
      }
    });
    const order: Record<string, number> = { L: 0, T: 1, P: 2, "T&P": 3 };
    return Array.from(map.values()).sort((a, b) => order[a.type] - order[b.type]);
  }, [entries]);

  const handleDragStart = (ev: React.DragEvent, entry: SlotEntry) => {
    ev.dataTransfer.setData("text/plain", entry.id);
    setDraggedSlotId(entry.id);
  };
  const handleDragOver  = (ev: React.DragEvent) => ev.preventDefault();
  const handleDrop      = (ev: React.DragEvent, day: string, period: number) => {
    ev.preventDefault();
    const id = ev.dataTransfer.getData("text/plain") || draggedSlotId;
    if (id) onSlotSwap?.(id, day, period);
    setDraggedSlotId(null);
  };

  return (
    <div className="w-full overflow-x-auto rounded-2xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-sm transition-colors print:shadow-none print:border-slate-400">

      {/* Academic Year + Section Banner */}
      <div className="text-center pt-3 pb-2 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
        <div className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 tracking-wide">
          Academic year 2026-27 (I Semester)
        </div>
        <div className="mt-1.5 flex items-center justify-center gap-3">
          <div className="bg-purple-200 dark:bg-purple-900/70 border border-purple-400 dark:border-purple-700 text-purple-950 dark:text-purple-100 font-extrabold text-sm py-1.5 px-8 inline-block rounded-md shadow-sm uppercase tracking-widest">
            {sectionName}
          </div>
          {showDownloadBtn && onDownloadPdf && (
            <button
              onClick={onDownloadPdf}
              title="Download PDF for this section"
              className="inline-flex items-center gap-1.5 text-[11px] font-bold text-blue-700 dark:text-blue-300 hover:underline cursor-pointer px-2 py-1 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-950/40 transition-colors"
            >
              <Download className="w-3.5 h-3.5" /> PDF
            </button>
          )}
        </div>
      </div>

      {/* Timetable Grid */}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1020px] border-collapse text-xs border border-slate-300 dark:border-slate-700">
          <thead>
            <tr className="bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 font-bold text-center">
              <th className="p-2 border border-slate-300 dark:border-slate-600 w-14">Period</th>
              <th className="p-2 border border-slate-300 dark:border-slate-600">1</th>
              <th className="p-2 border border-slate-300 dark:border-slate-600">2</th>
              <th className="p-2 border border-slate-300 dark:border-slate-600 bg-slate-200 dark:bg-slate-700 text-[10px] font-semibold">09:55-10:10</th>
              <th className="p-2 border border-slate-300 dark:border-slate-600">3</th>
              <th className="p-2 border border-slate-300 dark:border-slate-600">4</th>
              <th className="p-2 border border-slate-300 dark:border-slate-600">5</th>
              <th className="p-2 border border-slate-300 dark:border-slate-600 bg-slate-200 dark:bg-slate-700 text-[10px] font-semibold">12:40-1:40</th>
              <th className="p-2 border border-slate-300 dark:border-slate-600">6</th>
              <th className="p-2 border border-slate-300 dark:border-slate-600">7</th>
              <th className="p-2 border border-slate-300 dark:border-slate-600">8</th>
            </tr>
            <tr className="bg-slate-50 dark:bg-slate-800/60 text-slate-700 dark:text-slate-300 text-[10px] font-semibold text-center">
              <th className="p-1 border border-slate-300 dark:border-slate-600">Day/Hour</th>
              <th className="p-1 border border-slate-300 dark:border-slate-600">8:15-9:05</th>
              <th className="p-1 border border-slate-300 dark:border-slate-600">9:05-09:55</th>
              <th className="p-1 border border-slate-300 dark:border-slate-600 bg-slate-200 dark:bg-slate-700">09:55-10:10</th>
              <th className="p-1 border border-slate-300 dark:border-slate-600">10:10-11:00</th>
              <th className="p-1 border border-slate-300 dark:border-slate-600">11:00-11:50</th>
              <th className="p-1 border border-slate-300 dark:border-slate-600">11:50-12:40</th>
              <th className="p-1 border border-slate-300 dark:border-slate-600 bg-slate-200 dark:bg-slate-700">12:40-1:40</th>
              <th className="p-1 border border-slate-300 dark:border-slate-600">1:40-2:30</th>
              <th className="p-1 border border-slate-300 dark:border-slate-600">2:30-3:20</th>
              <th className="p-1 border border-slate-300 dark:border-slate-600">3:20-4:05</th>
            </tr>
          </thead>
          <tbody>
            {DAYS.map((day, dIdx) => {
              let skipPeriods = 0;
              return (
                <tr key={day} className="border-b border-slate-200 dark:border-slate-700">
                  <td className="p-1.5 border border-slate-300 dark:border-slate-600 font-extrabold bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 text-center text-xs">
                    {day}
                  </td>
                  {PERIODS.map((p, pIdx) => {
                    if ("isBreak" in p && p.isBreak) {
                      if (dIdx === 0) {
                        const isLunch = p.label.includes("12:40");
                        return (
                          <td key={pIdx} rowSpan={6} className="bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-600 text-center align-middle p-1 w-10">
                            <div className="flex flex-col items-center gap-0 font-extrabold text-slate-700 dark:text-slate-300 tracking-widest text-[10px] leading-4">
                              {isLunch
                                ? ["L","U","N","C","H"].map((c,i)=><span key={i}>{c}</span>)
                                : ["B","R","E","A","K"].map((c,i)=><span key={i}>{c}</span>)}
                            </div>
                          </td>
                        );
                      }
                      return null;
                    }
                    if (skipPeriods > 0) { skipPeriods--; return null; }
                    const periodId = p.id!;
                    const entry = slotMap.get(`${day}_${periodId}`);
                    const colSpan = entry?.spanPeriods && entry.spanPeriods > 1 ? entry.spanPeriods : 1;
                    if (colSpan > 1) skipPeriods = colSpan - 1;
                    const facShort = entry ? shortFacultyName(entry) : "";
                    const facFull  = entry ? fullFacultyNames(entry) : "";
                    return (
                      <td
                        key={pIdx}
                        colSpan={colSpan}
                        draggable={!!entry}
                        onDragStart={(ev) => entry && handleDragStart(ev, entry)}
                        onDragOver={handleDragOver}
                        onDrop={(ev) => handleDrop(ev, day, periodId)}
                        onClick={() => entry && onCellClick?.(entry)}
                        className={`border border-slate-300 dark:border-slate-600 text-center transition-colors cursor-pointer h-[68px] align-middle p-0.5 ${slotBg(entry)}`}
                        title={entry?.hasClash ? `CLASH: ${entry.clashReason}` : facFull ? `${entry?.subjectCode} - ${facFull}` : undefined}
                      >
                        {entry ? (
                          <div className="flex flex-col items-center justify-center h-full gap-0.5 px-0.5">
                            <div className="font-bold text-slate-900 dark:text-slate-100 text-[11px] leading-tight">
                              {entry.subjectCode}
                            </div>
                            {entry.sectionName && (
                              <div className="text-purple-800 dark:text-purple-200 font-extrabold text-[10px] leading-none bg-purple-200/80 dark:bg-purple-950/80 px-1.5 py-0.5 rounded border border-purple-300 dark:border-purple-800">
                                {entry.sectionName}
                              </div>
                            )}
                            {entry.roomCode && entry.roomCode !== "VIRTUAL_LIBRARY" ? (
                              <div className="text-red-600 dark:text-red-400 font-extrabold text-[11px] leading-tight">
                                {entry.roomCode}
                              </div>
                            ) : entry.roomCode === "VIRTUAL_LIBRARY" ? (
                              <div className="text-slate-400 dark:text-slate-500 font-semibold text-[9.5px] italic leading-tight">
                                Library
                              </div>
                            ) : null}

                            {facShort && !entry.sectionName && (
                              <div className="text-slate-500 dark:text-slate-400 text-[9px] italic leading-tight truncate max-w-[120px]">
                                {facShort}
                              </div>
                            )}
                            {entry.hasClash && (
                              <div className="text-red-500 text-[9px] font-bold">CLASH</div>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-300 dark:text-slate-700 text-[10px]">-</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="border-t border-slate-200 dark:border-slate-700 bg-slate-50/60 dark:bg-slate-900/80 rounded-b-2xl">
        {allocationRows.length === 0 ? (
          <p className="px-4 py-2.5 text-[11px] italic text-slate-400 dark:text-slate-500">
            All section slots assigned to department instructors.
          </p>
        ) : (
          <div className="px-4 py-3">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
              Faculty Allocation - {sectionName}
            </p>
            <table className="w-full text-[11px] border-collapse">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="text-left py-1 pr-4 font-bold text-slate-500 dark:text-slate-400 w-8">#</th>
                  <th className="text-left py-1 pr-4 font-bold text-slate-500 dark:text-slate-400 w-16">Code</th>
                  <th className="text-left py-1 pr-4 font-bold text-slate-500 dark:text-slate-400">Subject Name</th>
                  <th className="text-center py-1 pr-4 font-bold text-slate-500 dark:text-slate-400 w-14">Type</th>
                  <th className="text-left py-1 font-bold text-slate-500 dark:text-slate-400">Faculty Assigned</th>
                </tr>
              </thead>
              <tbody>
                {allocationRows.map((row, i) => {
                  const badgeClass: Record<string, string> = {
                    L:     "bg-blue-100 dark:bg-blue-950/60 text-blue-800 dark:text-blue-300 border border-blue-200 dark:border-blue-800",
                    T:     "bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800",
                    P:     "bg-violet-100 dark:bg-violet-950/60 text-violet-800 dark:text-violet-300 border border-violet-200 dark:border-violet-800",
                    "T&P": "bg-indigo-100 dark:bg-indigo-950/60 text-indigo-800 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800",
                  };
                  return (
                    <tr key={i} className="border-b border-slate-100 dark:border-slate-800/50 hover:bg-white dark:hover:bg-slate-800/40 transition-colors">
                      <td className="py-1.5 pr-4 text-slate-400 dark:text-slate-500 font-mono text-[10px]">{i + 1}.</td>
                      <td className="py-1.5 pr-4 font-bold text-slate-800 dark:text-slate-200">{row.code}</td>
                      <td className="py-1.5 pr-4 text-slate-700 dark:text-slate-300">{row.fullName}</td>
                      <td className="py-1.5 pr-4 text-center">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${badgeClass[row.type] ?? ""}`}>
                          ({row.type})
                        </span>
                      </td>
                      <td className="py-1.5 text-slate-700 dark:text-slate-300 font-medium">
                        {row.faculty || (
                          <span className="italic text-slate-400 dark:text-slate-500">Department Instructor</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};