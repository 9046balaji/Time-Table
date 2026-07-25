"use client";

import React, { useMemo, useState } from "react";

export interface SlotEntry {
  id: string;
  day: "MON" | "TUE" | "WED" | "THU" | "FRI" | "SAT";
  period: number; // 1 to 8
  subjectCode: string;
  roomCode: string;
  facultyName?: string;
  facultyNames?: string[];
  subjectType: "L" | "P" | "T" | "LIBRARY" | "IDP" | "MINORS_HONORS" | "SL_EL" | "OE" | "CRT" | "QALR" | "BREAK" | "LUNCH";
  spanPeriods?: number; // 1 or 2
  hasClash?: boolean;
  clashReason?: string;
}

interface TimetableGridProps {
  sectionName: string;
  entries: SlotEntry[];
  onCellClick?: (entry: SlotEntry) => void;
  onSlotSwap?: (draggedEntryId: string, targetDay: string, targetPeriod: number) => void;
}

const PERIODS = [
  { id: 1, label: "1", time: "8:15-9:05" },
  { id: 2, label: "2", time: "9:05-09:55" },
  { id: null, label: "09:55-10:10", time: "09:55-10:10", isBreak: true },
  { id: 3, label: "3", time: "10:10-11:00" },
  { id: 4, label: "4", time: "11:00-11:50" },
  { id: 5, label: "5", time: "11:50-12:40" },
  { id: null, label: "12:40-1:40", time: "12:40-1:40", isBreak: true },
  { id: 6, label: "6", time: "1:40-2:30" },
  { id: 7, label: "7", time: "2:30-3:20" },
  { id: 8, label: "8", time: "3:20-4:05" },
] as const;

const DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT"] as const;

export const TimetableGrid: React.FC<TimetableGridProps> = ({
  sectionName,
  entries,
  onCellClick,
  onSlotSwap,
}) => {
  const [draggedSlotId, setDraggedSlotId] = useState<string | null>(null);

  // O(1) lookup by day_period key
  const slotMap = useMemo(() => {
    const map = new Map<string, SlotEntry>();
    entries.forEach((e) => map.set(`${e.day}_${e.period}`, e));
    return map;
  }, [entries]);

  // Build 2-column faculty legend matching screenshot rows 14..22
  const { lectureRows, labRows } = useMemo(() => {
    const lectureMap = new Map<string, { name: string; faculty: string }>();
    const labMap = new Map<string, { name: string; faculty: string }>();
    const allSubjNames: Record<string, string> = {
      "DS": "Data Structures",
      "DBMS": "Data Base Management Systems",
      "AI": "Artificial Intelligence Search Methods for Problem Solving",
      "OOPS": "Object Oriented Programming",
      "SFCDS": "Statistical Foundation for Computing and Data Science",
      "DMS": "Discrete Mathematical Structures",
      "DEF": "Data Engineering Foundations",
      "DL": "Deep Learning & Neural Networks",
      "WT": "Web Technologies",
      "CV": "Computer Vision & Image Processing",
      "ADS": "Advanced Data Structures & Algorithms",
      "MLOP": "MLOps & AI Model Deployment",
      "IDP": "Interdisciplinary Project",
      "CNS": "Cryptography & Network Security",
      "TM": "Technical Modules",
      "GENAI": "Generative AI & LLMs",
      "IOT": "Internet of Things & Sensor Networks",
      "QALR": "Quantitative Aptitude & Logical Reasoning",
      "KRR": "Knowledge Representation & Reasoning",
      "Ethics-AI": "Ethics in Artificial Intelligence",
      "OE": "Open Elective Course",
    };

    entries.forEach((e) => {
      if (!e.subjectCode) return;
      const facs = e.facultyNames?.length
        ? e.facultyNames.filter(Boolean).join(", ")
        : (e.facultyName && e.facultyName !== "undefined" ? e.facultyName : "");
      
      const rawCode = e.subjectCode.replace("(P)", "").replace("(T)", "").replace("(T&P)", "").trim();
      if (!rawCode || rawCode === "BREAK" || rawCode === "LUNCH" || rawCode === "LIBRARY") return;

      const fullName = allSubjNames[rawCode] || rawCode;
      const isLab = e.subjectType === "P" || e.subjectCode.includes("(P)") || e.subjectCode.includes("(T&P)");
      const isTut = e.subjectType === "T" || e.subjectCode.includes("(T)");

      if (isLab || isTut) {
        if (!labMap.has(rawCode) || (!labMap.get(rawCode)?.faculty && facs)) {
          labMap.set(rawCode, { name: fullName, faculty: facs });
        }
      } else {
        if (!lectureMap.has(rawCode) || (!lectureMap.get(rawCode)?.faculty && facs)) {
          lectureMap.set(rawCode, { name: fullName, faculty: facs });
        }
      }
    });

    return {
      lectureRows: Array.from(lectureMap.entries()),
      labRows: Array.from(labMap.entries()),
    };
  }, [entries]);

  const handleDragStart = (e: React.DragEvent, entry: SlotEntry) => {
    e.dataTransfer.setData("text/plain", entry.id);
    setDraggedSlotId(entry.id);
  };

  const handleDragOver = (e: React.DragEvent) => e.preventDefault();

  const handleDrop = (e: React.DragEvent, day: string, period: number) => {
    e.preventDefault();
    const entryId = e.dataTransfer.getData("text/plain") || draggedSlotId;
    if (entryId) onSlotSwap?.(entryId, day, period);
    setDraggedSlotId(null);
  };

  // Shorten faculty name for in-cell display: "Dr. S. Srikantha Reddy" → "Dr. S. Reddy"
  const shortFaculty = (entry: SlotEntry): string => {
    const raw: any = (Array.isArray(entry.facultyNames) && entry.facultyNames.length > 0)
      ? entry.facultyNames[0]
      : entry.facultyName;
    const full: string = typeof raw === 'string' ? raw : (Array.isArray(raw) ? (raw as string[]).join(', ') : String(raw || ''));
    if (!full || full === 'undefined' || full === 'null') return "";
    const parts = full.trim().split(/\s+/);
    if (parts.length <= 2) return full;
    const title = parts[0].match(/^(Dr|Mr|Ms|Prof)\./i) ? parts[0] + " " : "";
    return title + parts[parts.length - 1];
  };

  return (
    <div className="w-full overflow-x-auto rounded-2xl border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm transition-colors">
      {/* ── Section Banner ── */}
      <div className="text-center py-2 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">
          Academic year 2026-27 (I Semester)
        </div>
        <div className="mt-1 bg-purple-200 dark:bg-purple-950/80 border border-purple-300 dark:border-purple-800 text-purple-950 dark:text-purple-200 font-extrabold text-sm py-1.5 px-4 inline-block rounded-lg shadow-sm uppercase tracking-widest">
          {sectionName}
        </div>
      </div>

      {/* ── Timetable Grid ── */}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[980px] border-collapse text-left text-xs border border-slate-300 dark:border-slate-800">
          <thead>
            {/* Row 5: Period Numbers */}
            <tr className="bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 font-bold text-center border-b border-slate-300 dark:border-slate-800">
              <th className="p-2 border border-slate-300 dark:border-slate-800 w-16">Period</th>
              <th className="p-2 border border-slate-300 dark:border-slate-800">1</th>
              <th className="p-2 border border-slate-300 dark:border-slate-800">2</th>
              <th className="p-2 border border-slate-300 dark:border-slate-800 bg-slate-200 dark:bg-slate-700/60 text-[10px] font-semibold text-slate-800 dark:text-slate-200">
                09:55-10:10
              </th>
              <th className="p-2 border border-slate-300 dark:border-slate-800">3</th>
              <th className="p-2 border border-slate-300 dark:border-slate-800">4</th>
              <th className="p-2 border border-slate-300 dark:border-slate-800">5</th>
              <th className="p-2 border border-slate-300 dark:border-slate-800 bg-slate-200 dark:bg-slate-700/60 text-[10px] font-semibold text-slate-800 dark:text-slate-200">
                12:40-1:40
              </th>
              <th className="p-2 border border-slate-300 dark:border-slate-800">6</th>
              <th className="p-2 border border-slate-300 dark:border-slate-800">7</th>
              <th className="p-2 border border-slate-300 dark:border-slate-800">8</th>
            </tr>
            {/* Row 6: Time Ranges */}
            <tr className="bg-slate-50 dark:bg-slate-800/60 text-slate-700 dark:text-slate-300 text-[10px] font-semibold text-center border-b border-slate-300 dark:border-slate-800">
              <th className="p-1 border border-slate-300 dark:border-slate-800">Day/Hour</th>
              <th className="p-1 border border-slate-300 dark:border-slate-800">8:15-9:05</th>
              <th className="p-1 border border-slate-300 dark:border-slate-800">9:05-09:55</th>
              <th className="p-1 border border-slate-300 dark:border-slate-800 bg-slate-200 dark:bg-slate-700/60">09:55-10:10</th>
              <th className="p-1 border border-slate-300 dark:border-slate-800">10:10-11:00</th>
              <th className="p-1 border border-slate-300 dark:border-slate-800">11:00-11:50</th>
              <th className="p-1 border border-slate-300 dark:border-slate-800">11:50-12:40</th>
              <th className="p-1 border border-slate-300 dark:border-slate-800 bg-slate-200 dark:bg-slate-700/60">12:40-1:40</th>
              <th className="p-1 border border-slate-300 dark:border-slate-800">1:40-2:30</th>
              <th className="p-1 border border-slate-300 dark:border-slate-800">2:30-3:20</th>
              <th className="p-1 border border-slate-300 dark:border-slate-800">3:20-4:05</th>
            </tr>
          </thead>

          <tbody>
            {DAYS.map((day, dIdx) => {
              let skipPeriods = 0;
              return (
                <tr key={day} className="border-b border-slate-300 dark:border-slate-800">
                  {/* Day label */}
                  <td className="p-1.5 border border-slate-300 dark:border-slate-800 font-bold bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 text-center text-xs">
                    {day}
                  </td>

                  {PERIODS.map((p, pIdx) => {
                    // ── BREAK / LUNCH merged columns (rowSpan=6, only on MON row) ──
                    if ('isBreak' in p && p.isBreak) {
                      if (dIdx === 0) {
                        const isLunch = p.label.includes("12:40");
                        return (
                          <td
                            key={pIdx}
                            rowSpan={6}
                            className="bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-800 text-center text-[10px] font-bold align-middle p-1 w-12"
                          >
                            <div className="flex flex-col items-center gap-0 leading-4 font-extrabold text-slate-800 dark:text-slate-200 tracking-widest">
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

                    const facShort = entry ? shortFaculty(entry) : "";

                    return (
                      <td
                        key={pIdx}
                        colSpan={colSpan}
                        draggable={!!entry}
                        onDragStart={(e) => entry && handleDragStart(e, entry)}
                        onDragOver={handleDragOver}
                        onDrop={(e) => handleDrop(e, day, periodId)}
                        onClick={() => entry && onCellClick?.(entry)}
                        className={`border border-slate-300 dark:border-slate-800 text-center transition-all duration-150 cursor-pointer h-16 align-middle p-0.5 ${
                          entry?.hasClash
                            ? "bg-red-100 dark:bg-red-950/70 border-l-4 border-l-red-600"
                            : "bg-white dark:bg-slate-900 hover:bg-purple-50 dark:hover:bg-purple-950/40"
                        }`}
                        title={entry?.hasClash ? `CLASH: ${entry.clashReason}` : ""}
                      >
                        {entry ? (
                          <div className="flex flex-col items-center justify-center h-full gap-0.5">
                            {/* Line 1: Subject Code — Bold Text */}
                            <div className="font-bold text-slate-900 dark:text-slate-100 text-[11px] leading-tight">
                              {entry.subjectCode}
                            </div>
                            {/* Line 2: Room Code — Bold Red */}
                            {entry.roomCode && (
                              <div className="text-red-600 dark:text-red-400 font-extrabold text-[11px] leading-tight">
                                {entry.roomCode}
                              </div>
                            )}
                            {/* Line 3: Faculty short name — italic muted text */}
                            {facShort && (
                              <div className="text-slate-500 dark:text-slate-400 text-[9px] italic leading-tight truncate max-w-[110px]">
                                {facShort}
                              </div>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-300 dark:text-slate-700 text-[10px]">—</span>
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

      {/* ── 2-Column Faculty Allocation Legend (matching screenshot rows 14..22) ── */}
      {(lectureRows.length > 0 || labRows.length > 0) && (
        <div className="border-t border-slate-300 dark:border-slate-800 text-[11px]">
          <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-200 dark:divide-slate-800">
            {/* Left column: Lecture (L) faculty */}
            <div className="divide-y divide-slate-100 dark:divide-slate-800/60">
              {lectureRows.map(([code, { name, faculty }], i) => (
                <div key={i} className="px-3 py-1.5 text-slate-800 dark:text-slate-200 leading-snug">
                  <span className="font-semibold">{name}(L):</span>{" "}
                  <span className="text-slate-600 dark:text-slate-400">{faculty || "Department Instructor"}</span>
                </div>
              ))}
            </div>
            {/* Right column: Practical/Tutorial (P/T&P) faculty */}
            <div className="divide-y divide-slate-100 dark:divide-slate-800/60">
              {labRows.map(([code, { name, faculty }], i) => {
                const suffix = entries.find(e => e.subjectCode.startsWith(code) && e.subjectCode.includes("(T)")) ? "(T&P)" : "(P)";
                return (
                  <div key={i} className="px-3 py-1.5 text-slate-800 dark:text-slate-200 leading-snug">
                    <span className="font-semibold">{name}{suffix}:</span>{" "}
                    <span className="text-slate-600 dark:text-slate-400">{faculty || "Lab Instructor Team"}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
