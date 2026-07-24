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
    };

    entries.forEach((e) => {
      if (!e.subjectCode) return;
      const facs = e.facultyNames?.length
        ? e.facultyNames.join(", ")
        : e.facultyName || "";
      const code = e.subjectCode.replace("(P)", "").replace("(T)", "").replace("(T&P)", "").trim();
      const fullName = allSubjNames[code] || code;

      const isLab = e.subjectType === "P" || e.subjectCode.includes("(P)") || e.subjectCode.includes("(T&P)");
      const isTut = e.subjectType === "T" || e.subjectCode.includes("(T)");

      if (isLab) {
        if (!labMap.has(code)) labMap.set(code, { name: fullName, faculty: facs });
      } else if (isTut) {
        if (!labMap.has(code)) labMap.set(code, { name: fullName, faculty: facs });
      } else {
        if (!lectureMap.has(code)) lectureMap.set(code, { name: fullName, faculty: facs });
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
    const full = entry.facultyNames?.length
      ? entry.facultyNames[0]
      : (entry.facultyName || "");
    if (!full) return "";
    const parts = full.trim().split(/\s+/);
    if (parts.length <= 2) return full;
    // Keep title + first-name-initial + last-name
    const title = parts[0].match(/^(Dr|Mr|Ms|Prof)\./i) ? parts[0] + " " : "";
    return title + parts[parts.length - 1];
  };

  return (
    <div className="w-full overflow-x-auto rounded-2xl border border-slate-300 bg-white shadow-sm">
      {/* ── Section Banner ── */}
      <div className="text-center py-2 bg-white border-b border-slate-200">
        <div className="text-[11px] font-semibold text-slate-500">Academic year 2026-27 (I Semester)</div>
        <div className="mt-1 bg-purple-300 border border-purple-400 text-purple-950 font-extrabold text-sm py-1.5 px-4 inline-block rounded-lg shadow-sm uppercase tracking-widest">
          {sectionName}
        </div>
      </div>

      {/* ── Timetable Grid ── */}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[980px] border-collapse text-left text-xs border border-slate-900">
          <thead>
            {/* Row 5: Period Numbers */}
            <tr className="bg-slate-100 text-slate-900 font-bold text-center border-b border-slate-900">
              <th className="p-2 border border-slate-900 w-16">Period</th>
              <th className="p-2 border border-slate-900">1</th>
              <th className="p-2 border border-slate-900">2</th>
              <th className="p-2 border border-slate-900 bg-slate-200 text-[10px] font-semibold">09:55-10:10</th>
              <th className="p-2 border border-slate-900">3</th>
              <th className="p-2 border border-slate-900">4</th>
              <th className="p-2 border border-slate-900">5</th>
              <th className="p-2 border border-slate-900 bg-slate-200 text-[10px] font-semibold">12:40-1:40</th>
              <th className="p-2 border border-slate-900">6</th>
              <th className="p-2 border border-slate-900">7</th>
              <th className="p-2 border border-slate-900">8</th>
            </tr>
            {/* Row 6: Time Ranges */}
            <tr className="bg-slate-50 text-slate-700 text-[10px] font-semibold text-center border-b border-slate-900">
              <th className="p-1 border border-slate-900">Day/Hour</th>
              <th className="p-1 border border-slate-900">8:15-9:05</th>
              <th className="p-1 border border-slate-900">9:05-09:55</th>
              <th className="p-1 border border-slate-900 bg-slate-200">09:55-10:10</th>
              <th className="p-1 border border-slate-900">10:10-11:00</th>
              <th className="p-1 border border-slate-900">11:00-11:50</th>
              <th className="p-1 border border-slate-900">11:50-12:40</th>
              <th className="p-1 border border-slate-900 bg-slate-200">12:40-1:40</th>
              <th className="p-1 border border-slate-900">1:40-2:30</th>
              <th className="p-1 border border-slate-900">2:30-3:20</th>
              <th className="p-1 border border-slate-900">3:20-4:05</th>
            </tr>
          </thead>

          <tbody>
            {DAYS.map((day, dIdx) => {
              let skipPeriods = 0;
              return (
                <tr key={day} className="border-b border-slate-900">
                  {/* Day label */}
                  <td className="p-1.5 border border-slate-900 font-bold bg-slate-100 text-slate-900 text-center text-xs">
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
                            className="bg-slate-100 border border-slate-900 text-center text-[10px] font-bold align-middle p-1 w-12"
                          >
                            <div className="flex flex-col items-center gap-0 leading-4 font-extrabold text-slate-800 tracking-widest">
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
                        className={`border border-slate-900 text-center transition-all duration-150 cursor-pointer h-16 align-middle p-0.5 ${
                          entry?.hasClash
                            ? "bg-red-100 border-l-4 border-l-red-600"
                            : "bg-white hover:bg-purple-50"
                        }`}
                        title={entry?.hasClash ? `CLASH: ${entry.clashReason}` : ""}
                      >
                        {entry ? (
                          <div className="flex flex-col items-center justify-center h-full gap-0.5">
                            {/* Line 1: Subject Code — Bold Black */}
                            <div className="font-bold text-slate-900 text-[11px] leading-tight">
                              {entry.subjectCode}
                            </div>
                            {/* Line 2: Room Code — Bold Red */}
                            {entry.roomCode && (
                              <div className="text-red-600 font-extrabold text-[11px] leading-tight">
                                {entry.roomCode}
                              </div>
                            )}
                            {/* Line 3: Faculty short name — italic grey */}
                            {facShort && (
                              <div className="text-slate-500 text-[9px] italic leading-tight truncate max-w-[110px]">
                                {facShort}
                              </div>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-300 text-[10px]">—</span>
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
        <div className="border-t border-slate-900 text-[11px]">
          <div className="grid grid-cols-2 divide-x divide-slate-300">
            {/* Left column: Lecture (L) faculty */}
            <div className="divide-y divide-slate-200">
              {lectureRows.map(([code, { name, faculty }], i) => (
                <div key={i} className="px-3 py-1.5 text-slate-800 leading-snug">
                  <span className="font-semibold">{name}(L):</span>{" "}
                  <span className="text-slate-600">{faculty || "Department Instructor"}</span>
                </div>
              ))}
            </div>
            {/* Right column: Practical/Tutorial (P/T&P) faculty */}
            <div className="divide-y divide-slate-200">
              {labRows.map(([code, { name, faculty }], i) => {
                const suffix = entries.find(e => e.subjectCode.startsWith(code) && e.subjectCode.includes("(T)")) ? "(T&P)" : "(P)";
                return (
                  <div key={i} className="px-3 py-1.5 text-slate-800 leading-snug">
                    <span className="font-semibold">{name}{suffix}:</span>{" "}
                    <span className="text-slate-600">{faculty || "Lab Instructor Team"}</span>
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
