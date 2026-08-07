"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  X,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  Clock,
  Building2,
  GraduationCap,
  BookOpen,
  Users,
  Trash2,
  Sparkles,
  Save,
  Loader2,
  ShieldAlert
} from "lucide-react";
import { SlotEntry } from "./TimetableGrid";
import { Faculty, Room, Subject, Section } from "@/lib/types";

interface SlotEditorModalProps {
  isOpen: boolean;
  onClose: () => void;
  slot: SlotEntry | null;
  versionId?: number;
  sectionsList?: (Section | string)[];
  facultyList?: Faculty[];
  roomList?: Room[];
  subjectList?: Subject[];
  cohortAllSlots?: any[];
  onSaveSlot: (updatedData: any) => Promise<void> | void;
  onDeleteSlot?: (entryId: string) => Promise<void> | void;
}

const DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT"];
const PERIODS = [
  { id: 1, label: "Period 1 (8:15 - 9:05)" },
  { id: 2, label: "Period 2 (9:05 - 9:55)" },
  { id: 3, label: "Period 3 (10:10 - 11:00)" },
  { id: 4, label: "Period 4 (11:00 - 11:50)" },
  { id: 5, label: "Period 5 (11:50 - 12:40)" },
  { id: 6, label: "Period 6 (1:40 - 2:30)" },
  { id: 7, label: "Period 7 (2:30 - 3:20)" },
  { id: 8, label: "Period 8 (3:20 - 4:05)" },
];

export const SlotEditorModal: React.FC<SlotEditorModalProps> = ({
  isOpen,
  onClose,
  slot,
  versionId = 5,
  sectionsList = [],
  facultyList = [],
  roomList = [],
  subjectList = [],
  cohortAllSlots = [],
  onSaveSlot,
  onDeleteSlot
}) => {
  const [day, setDay] = useState<string>("MON");
  const [period, setPeriod] = useState<number>(1);
  const [sectionName, setSectionName] = useState<string>("II AIML-A");
  const [subjectCode, setSubjectCode] = useState<string>("DS");
  const [subjectType, setSubjectType] = useState<string>("L");
  const [roomCode, setRoomCode] = useState<string>("601");
  const [selectedFacultyNames, setSelectedFacultyNames] = useState<string[]>([]);
  
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Initialize form when slot opens
  useEffect(() => {
    if (slot) {
      setDay(slot.day || "MON");
      setPeriod(Number(slot.period || 1));
      setSectionName(slot.sectionName || "II AIML-A");
      setSubjectCode(slot.subjectCode || "DS");
      setSubjectType(slot.subjectType || "L");
      setRoomCode(slot.roomCode || "601");

      const facs: string[] = Array.isArray(slot.facultyNames) && slot.facultyNames.length > 0
        ? slot.facultyNames
        : (slot.facultyName ? [slot.facultyName] : []);
      setSelectedFacultyNames(facs);
    }
  }, [slot]);

  // Real-Time Local Conflict Detection
  const clashDiagnosis = useMemo(() => {
    if (!cohortAllSlots || cohortAllSlots.length === 0) {
      return { hasClash: false, message: "No conflicts detected." };
    }

    const tDay = day.trim().toUpperCase();
    const tPeriod = Number(period);
    const currentEntryId = slot?.id;

    // 1. Room Clash Check (HC-01)
    if (roomCode && !["", "LIBRARY", "BREAK", "LUNCH", "VIRTUAL_LIBRARY"].includes(roomCode.toUpperCase())) {
      const roomConflict = cohortAllSlots.find((s: any) => {
        const sId = String(s.id || "");
        if (currentEntryId && sId === String(currentEntryId)) return false;
        const sRoom = String(s.room || s.room_code || "").trim().toUpperCase();
        const sDay = String(s.day || "").trim().toUpperCase();
        const sPeriod = Number(s.period);
        return sRoom === roomCode.toUpperCase() && sDay === tDay && sPeriod === tPeriod;
      });

      if (roomConflict) {
        const secConf = roomConflict.section || roomConflict.section_name || "Another Section";
        const subjConf = roomConflict.subject || roomConflict.subject_code || "Subject";
        return {
          hasClash: true,
          type: "ROOM",
          message: `Room Conflict (HC-01): Venue ${roomCode} is ALREADY assigned to ${secConf} (${subjConf}) on ${tDay} Period ${tPeriod}!`
        };
      }
    }

    // 2. Faculty Double-Booking Check (HC-02)
    for (const facName of selectedFacultyNames) {
      if (!facName || facName === "undefined") continue;
      const cleanFac = facName.replace(/^(Dr|Mr|Ms|Prof)\.?\s*/i, "").trim().toLowerCase();

      const facConflict = cohortAllSlots.find((s: any) => {
        const sId = String(s.id || "");
        if (currentEntryId && sId === String(currentEntryId)) return false;
        const sDay = String(s.day || "").trim().toUpperCase();
        const sPeriod = Number(s.period);
        if (sDay !== tDay || sPeriod !== tPeriod) return false;

        const sFacs = Array.isArray(s.faculty) ? s.faculty.map((f: any) => String(f).toLowerCase()) : [String(s.faculty || "").toLowerCase()];
        return sFacs.some((f: string) => f.includes(cleanFac) || cleanFac.includes(f));
      });

      if (facConflict) {
        const secConf = facConflict.section || facConflict.section_name || "Another Section";
        const rmConf = facConflict.room || facConflict.room_code || "another room";
        return {
          hasClash: true,
          type: "FACULTY",
          message: `Faculty Conflict (HC-02): ${facName} is ALREADY teaching ${secConf} in Room ${rmConf} on ${tDay} Period ${tPeriod}!`
        };
      }
    }

    // 3. Section Double-Booking Check (HC-03)
    const sectionConflict = cohortAllSlots.find((s: any) => {
      const sId = String(s.id || "");
      if (currentEntryId && sId === String(currentEntryId)) return false;
      const sSec = String(s.section || s.section_name || "").trim().toUpperCase();
      const sDay = String(s.day || "").trim().toUpperCase();
      const sPeriod = Number(s.period);
      return sSec === sectionName.trim().toUpperCase() && sDay === tDay && sPeriod === tPeriod;
    });

    if (sectionConflict) {
      const subjConf = sectionConflict.subject || sectionConflict.subject_code || "Subject";
      return {
        hasClash: true,
        type: "SECTION",
        message: `Section Conflict (HC-03): Section ${sectionName} ALREADY has ${subjConf} scheduled on ${tDay} Period ${tPeriod}!`
      };
    }

    return {
      hasClash: false,
      message: "Assignment Verified — No room, faculty, or section conflicts."
    };
  }, [day, period, roomCode, selectedFacultyNames, sectionName, cohortAllSlots, slot]);

  if (!isOpen) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        version_id: versionId,
        entry_id: slot?.id,
        section_name: sectionName,
        subject_code: subjectType === "P" && !subjectCode.includes("(P)") ? `${subjectCode}(P)` : subjectCode,
        subject_type: subjectType,
        room_code: roomCode,
        day: day,
        period: Number(period),
        faculty_names: selectedFacultyNames
      };
      await onSaveSlot(payload);
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!slot?.id || !confirm("Are you sure you want to clear/delete this slot?")) return;
    setDeleting(true);
    try {
      if (onDeleteSlot) await onDeleteSlot(slot.id);
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Modal Header */}
        <div className="px-6 py-4 bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-100 dark:bg-blue-950/80 text-blue-700 dark:text-blue-300 rounded-2xl border border-blue-200 dark:border-blue-800">
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-extrabold text-slate-900 dark:text-white">
                Interactive Timetable Slot Editor
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Modify Subject, Room, Instructors, and Schedule Coordinates in Real Time
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-white rounded-xl hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Real-Time Conflict Inspection Banner */}
        <div className={`px-6 py-3 border-b text-xs font-bold flex items-center gap-2.5 ${
          clashDiagnosis.hasClash
            ? "bg-red-50 dark:bg-red-950/80 border-red-200 dark:border-red-800 text-red-700 dark:text-red-300"
            : "bg-emerald-50 dark:bg-emerald-950/80 border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300"
        }`}>
          {clashDiagnosis.hasClash ? (
            <ShieldAlert className="w-4 h-4 text-red-500 shrink-0" />
          ) : (
            <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
          )}
          <span>{clashDiagnosis.message}</span>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSave} className="p-6 space-y-5 overflow-y-auto flex-1">
          
          {/* Day & Period Selectors */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-blue-500" /> Academic Day
              </label>
              <select
                value={day}
                onChange={(e) => setDay(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl px-3 py-2 text-xs font-bold text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {DAYS.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-purple-500" /> Period Slot
              </label>
              <select
                value={period}
                onChange={(e) => setPeriod(Number(e.target.value))}
                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl px-3 py-2 text-xs font-bold text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {PERIODS.map((p) => (
                  <option key={p.id} value={p.id}>{p.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Section & Subject Selectors */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1 flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-amber-500" /> Target Section
              </label>
              <select
                value={sectionName}
                onChange={(e) => setSectionName(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl px-3 py-2 text-xs font-bold text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {sectionsList.map((s, idx) => {
                  const secStr = typeof s === 'string' ? s : (s.name || (s as any).section_name || String(s));
                  return (
                    <option key={idx} value={secStr}>{secStr}</option>
                  );
                })}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1 flex items-center gap-1.5">
                <BookOpen className="w-3.5 h-3.5 text-emerald-500" /> Course Subject
              </label>
              <select
                value={subjectCode}
                onChange={(e) => setSubjectCode(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl px-3 py-2 text-xs font-bold text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {subjectList.length > 0 ? (
                  subjectList.map((sub) => (
                    <option key={sub.id} value={sub.code}>{sub.code} - {sub.full_name}</option>
                  ))
                ) : (
                  <>
                    <option value="DS">DS - Data Structures</option>
                    <option value="DBMS">DBMS - Data Base Management Systems</option>
                    <option value="AI">AI - Artificial Intelligence</option>
                    <option value="SFCDS">SFCDS - Statistical Foundations</option>
                    <option value="DL">DL - Deep Learning</option>
                    <option value="WT">WT - Web Technologies</option>
                    <option value="LIBRARY">LIBRARY - Library Hours</option>
                  </>
                )}
              </select>
            </div>
          </div>

          {/* Room Venue & Subject Type */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1 flex items-center gap-1.5">
                <Building2 className="w-3.5 h-3.5 text-indigo-500" /> Room / Venue
              </label>
              <select
                value={roomCode}
                onChange={(e) => setRoomCode(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl px-3 py-2 text-xs font-bold text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {roomList.length > 0 ? (
                  roomList.map((rm) => (
                    <option key={rm.id} value={rm.code}>
                      {rm.code} ({rm.room_type || rm.type || "room"}) - Cap: {rm.capacity || 60}
                    </option>
                  ))
                ) : (
                  <>
                    <option value="601">601 (Classroom) - Cap: 66</option>
                    <option value="604">604 (Computer Lab) - Cap: 60</option>
                    <option value="AFTF-12">AFTF-12 (GPU Compute Lab) - Cap: 72</option>
                    <option value="AFTF-13">AFTF-13 (GPU Compute Lab) - Cap: 72</option>
                    <option value="611">611 (Computer Lab) - Cap: 60</option>
                    <option value="612">612 (Computer Lab) - Cap: 60</option>
                  </>
                )}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                Subject Type & Slot Span
              </label>
              <select
                value={subjectType}
                onChange={(e) => setSubjectType(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl px-3 py-2 text-xs font-bold text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="L">Lecture (1 Period)</option>
                <option value="P">Practical Lab (2 Consecutive Periods)</option>
                <option value="T">Tutorial (1 Period)</option>
                <option value="LIBRARY">Library / Self Learning</option>
              </select>
            </div>
          </div>

          {/* Faculty Instructors Multi-Select */}
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1 flex items-center gap-1.5">
              <GraduationCap className="w-3.5 h-3.5 text-teal-500" /> Assigned Faculty Instructor(s)
            </label>
            <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-300 dark:border-slate-700 rounded-xl p-3 max-h-36 overflow-y-auto space-y-1.5">
              {facultyList.length > 0 ? (
                facultyList.map((fac) => {
                  const isChecked = selectedFacultyNames.some(
                    (fn) => fn.toLowerCase().includes(fac.name.toLowerCase()) || fac.name.toLowerCase().includes(fn.toLowerCase())
                  );
                  return (
                    <label key={fac.id} className="flex items-center gap-2 text-xs font-semibold text-slate-800 dark:text-slate-200 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 p-1 rounded-lg">
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedFacultyNames((prev) => [...prev, fac.name]);
                          } else {
                            setSelectedFacultyNames((prev) =>
                              prev.filter((fn) => !fn.toLowerCase().includes(fac.name.toLowerCase()) && !fac.name.toLowerCase().includes(fn.toLowerCase()))
                            );
                          }
                        }}
                        className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span>{fac.name}</span>
                      <span className="text-[10px] text-slate-400">({fac.designation})</span>
                    </label>
                  );
                })
              ) : (
                <div className="text-xs text-slate-500 italic">No faculty records loaded.</div>
              )}
            </div>
          </div>

          {/* Modal Footer Controls */}
          <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between gap-3">
            {slot?.id ? (
              <button
                type="button"
                onClick={handleDelete}
                disabled={deleting}
                className="inline-flex items-center gap-1.5 px-3 py-2 bg-red-50 dark:bg-red-950/60 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800 rounded-xl text-xs font-bold hover:bg-red-100 transition-colors cursor-pointer"
              >
                {deleting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                Clear Slot
              </button>
            ) : <div></div>}

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-xl text-xs font-bold hover:bg-slate-200 transition-colors cursor-pointer"
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={saving}
                className="inline-flex items-center gap-1.5 px-5 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-md cursor-pointer disabled:opacity-50"
              >
                {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                Save & Apply Slot
              </button>
            </div>
          </div>

        </form>
      </div>
    </div>
  );
};
