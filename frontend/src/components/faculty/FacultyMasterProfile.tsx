"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Users,
  Search,
  UserCheck,
  Phone,
  Mail,
  Building2,
  BookOpen,
  Plus,
  Edit,
  Trash2,
  X,
  Clock,
  Calendar,
  Grid,
  List,
  Shield,
  FileText,
  CheckCircle2,
  AlertCircle,
  Loader2
} from "lucide-react";
import { Faculty, Subject, Section } from "@/lib/types";
import { timetableApi } from "@/lib/api";

interface FacultyMasterProfileProps {
  facultyList: Faculty[];
  subjectList?: Subject[];
  sectionList?: Section[];
  onAddFaculty?: (newFac: Partial<Faculty>) => void;
  onUpdateFaculty?: (id: number, updatedFac: Partial<Faculty>) => void;
  onDeleteFaculty?: (id: number) => void;
}

const DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT"];
const PERIODS = [1, 2, 3, 4, 5, 6, 7, 8];

export const FacultyMasterProfile: React.FC<FacultyMasterProfileProps> = ({
  facultyList,
  subjectList = [],
  sectionList = [],
  onAddFaculty,
  onUpdateFaculty,
  onDeleteFaculty
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [quickFilter, setQuickFilter] = useState<"ALL" | "PROF" | "CAP" | "OVERLOAD">("ALL");
  const [sortBy, setSortBy] = useState<"NAME" | "LOAD">("NAME");

  // Selected Faculty for Slide-Over Drawer
  const [selectedFaculty, setSelectedFaculty] = useState<Faculty | null>(null);
  const [facultySchedule, setFacultySchedule] = useState<any[]>([]);
  const [loadingSchedule, setLoadingSchedule] = useState(false);

  // Edit Modal State
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingFaculty, setEditingFaculty] = useState<Partial<Faculty> | null>(null);

  const [formData, setFormData] = useState({
    name: "",
    employee_id: "",
    designation: "Assistant Professor",
    phone: "",
    email: "",
    max_hours_per_week: 16,
    max_daily_classes: 5,
    is_external: false,
    subjects_taught_str: ""
  });

  // Fetch teaching schedule whenever selectedFaculty changes
  useEffect(() => {
    if (selectedFaculty && selectedFaculty.id) {
      setLoadingSchedule(true);
      timetableApi.getFacultyTimetable(selectedFaculty.id)
        .then((res) => {
          const items = Array.isArray(res.data) ? res.data : (res.data as any)?.entries || (res.data as any)?.items || [];
          setFacultySchedule(items);
        })
        .catch(() => setFacultySchedule([]))
        .finally(() => setLoadingSchedule(false));
    } else {
      setFacultySchedule([]);
    }
  }, [selectedFaculty]);

  const handleOpenAddModal = () => {
    setEditingFaculty(null);
    setFormData({
      name: "",
      employee_id: `VF-ACSE-${100 + facultyList.length + 1}`,
      designation: "Assistant Professor",
      phone: "",
      email: "",
      max_hours_per_week: 16,
      max_daily_classes: 5,
      is_external: false,
      subjects_taught_str: ""
    });
    setShowEditModal(true);
  };

  const handleOpenEditModal = (fac: Faculty) => {
    setEditingFaculty(fac);
    setFormData({
      name: fac.name || "",
      employee_id: fac.employee_id || `VF-${fac.id}`,
      designation: fac.designation || "Assistant Professor",
      phone: fac.phone || "",
      email: fac.email || "",
      max_hours_per_week: fac.max_hours_per_week || 16,
      max_daily_classes: fac.max_daily_classes || 5,
      is_external: fac.is_external || false,
      subjects_taught_str: (fac.subjects_taught || []).join(", ")
    });
    setShowEditModal(true);
  };

  const handleSaveForm = (e: React.FormEvent) => {
    e.preventDefault();
    const subsArray = formData.subjects_taught_str
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    const payload: Partial<Faculty> = {
      name: formData.name,
      employee_id: formData.employee_id,
      designation: formData.designation,
      phone: formData.phone || undefined,
      email: formData.email || undefined,
      max_hours_per_week: Number(formData.max_hours_per_week),
      max_daily_classes: Number(formData.max_daily_classes),
      is_external: formData.is_external,
      subjects_taught: subsArray
    };

    if (editingFaculty && editingFaculty.id && onUpdateFaculty) {
      onUpdateFaculty(editingFaculty.id, payload);
    } else if (onAddFaculty) {
      onAddFaculty(payload);
    }
    setShowEditModal(false);
  };

  // Filtered Faculty Roster
  const filteredFaculty = useMemo(() => {
    return facultyList
      .filter((fac) => {
        if (searchQuery) {
          const q = searchQuery.toLowerCase();
          const matchName = fac.name.toLowerCase().includes(q);
          const matchEmpId = (fac.employee_id || "").toLowerCase().includes(q);
          const matchSubj = (fac.subjects_taught || []).some((s) => s.toLowerCase().includes(q));
          if (!matchName && !matchEmpId && !matchSubj) return false;
        }

        const curHours = fac.current_weekly_hours ?? fac.hours_this_week ?? 12;
        const maxHours = fac.max_hours_per_week ?? fac.max_hours ?? 16;
        const loadPct = (curHours / maxHours) * 100;

        if (quickFilter === "PROF" && !fac.designation.includes("Professor")) return false;
        if (quickFilter === "CAP" && (loadPct < 75 || loadPct > 100)) return false;
        if (quickFilter === "OVERLOAD" && curHours <= maxHours) return false;

        return true;
      })
      .sort((a, b) => {
        if (sortBy === "LOAD") {
          const loadA = a.current_weekly_hours ?? a.hours_this_week ?? 12;
          const loadB = b.current_weekly_hours ?? b.hours_this_week ?? 12;
          return loadB - loadA;
        }
        return a.name.localeCompare(b.name);
      });
  }, [facultyList, searchQuery, quickFilter, sortBy]);

  // Helper to find scheduled teaching slot for selected faculty
  const getScheduledSlot = (day: string, period: number) => {
    return facultySchedule.find((s) => s.day === day && Number(s.period) === period);
  };

  return (
    <div className="space-y-6">

      {/* 1. Header Action Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Faculty Directory & Workload Registry</h2>
            <span className="px-2.5 py-0.5 bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 text-xs font-bold rounded-full border border-blue-200 dark:border-blue-800">
              {facultyList.length} Active Instructors
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Click any instructor card to open their Slide-Over Dossier, active teaching schedule, and availability grid.
          </p>
        </div>

        <button
          onClick={handleOpenAddModal}
          className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-xl font-bold text-xs shadow-sm transition-all cursor-pointer"
        >
          <Plus className="w-4 h-4" /> Add Instructor
        </button>
      </div>

      {/* 2. Simplified Search & Quick Filters Bar */}
      <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search by name, employee ID, or course..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          />
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider shrink-0">Filters:</span>

          <button
            onClick={() => setQuickFilter("ALL")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 cursor-pointer ${
              quickFilter === "ALL"
                ? "bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-sm"
                : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
            }`}
          >
            All ({facultyList.length})
          </button>

          <button
            onClick={() => setQuickFilter("PROF")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 cursor-pointer ${
              quickFilter === "PROF"
                ? "bg-blue-600 text-white shadow-sm"
                : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
            }`}
          >
            Professors
          </button>

          <button
            onClick={() => setQuickFilter("CAP")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 cursor-pointer ${
              quickFilter === "CAP"
                ? "bg-amber-600 text-white shadow-sm"
                : "bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800"
            }`}
          >
            Near Capacity
          </button>

          <button
            onClick={() => setQuickFilter("OVERLOAD")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 cursor-pointer ${
              quickFilter === "OVERLOAD"
                ? "bg-red-600 text-white shadow-sm"
                : "bg-red-50 dark:bg-red-950/60 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800"
            }`}
          >
            Overloaded
          </button>

          <div className="h-4 w-px bg-slate-200 dark:bg-slate-700 mx-1 shrink-0" />

          <button
            onClick={() => setSortBy(sortBy === "NAME" ? "LOAD" : "NAME")}
            className="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-xl text-xs font-bold hover:bg-slate-200 dark:hover:bg-slate-700 shrink-0 cursor-pointer"
          >
            Sort: {sortBy === "NAME" ? "Name (A-Z)" : "Workload (High)"}
          </button>
        </div>
      </div>

      {/* 3. Clean Interactive Card Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredFaculty.map((fac) => {
          const empId = fac.employee_id || `VF-ACSE-${fac.id}`;
          const curHours = fac.current_weekly_hours ?? fac.hours_this_week ?? 12;
          const maxHours = fac.max_hours_per_week ?? fac.max_hours ?? 16;
          const loadPercentage = Math.round((curHours / maxHours) * 100);
          const isOverloaded = curHours > maxHours;
          const isNearCap = loadPercentage >= 75 && !isOverloaded;

          const coursesList = fac.subjects_taught && fac.subjects_taught.length > 0
            ? fac.subjects_taught
            : ["DS", "AI", "DBMS"];

          return (
            <div
              key={fac.id}
              onClick={() => setSelectedFaculty(fac)}
              className="group bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-lg transition-all cursor-pointer relative flex flex-col justify-between"
            >
              <div>
                {/* Header Tag & Designation */}
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[11px] font-bold text-blue-700 dark:text-blue-300 bg-blue-50 dark:bg-blue-950/80 px-2.5 py-0.5 rounded-lg border border-blue-200 dark:border-blue-800">
                    {empId}
                  </span>
                  <span className="text-xs text-slate-500 dark:text-slate-400 font-semibold">{fac.designation}</span>
                </div>

                {/* Name */}
                <h3 className="font-bold text-slate-900 dark:text-white text-base group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                  {fac.name}
                </h3>

                {/* Contact Email (Cleanly displayed only if present) */}
                {fac.email && (
                  <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5 truncate">{fac.email}</p>
                )}

                {/* Workload Progress Gauge */}
                <div className="mt-4 space-y-1.5">
                  <div className="flex justify-between text-xs font-bold">
                    <span className="text-slate-500 dark:text-slate-400">Weekly Workload</span>
                    <span className={isOverloaded ? "text-red-600 dark:text-red-400" : isNearCap ? "text-amber-600 dark:text-amber-400" : "text-slate-800 dark:text-slate-200"}>
                      {curHours} / {maxHours} hrs ({loadPercentage}%)
                    </span>
                  </div>

                  <div className="w-full h-2.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden p-0.5 border border-slate-200 dark:border-slate-700">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        isOverloaded ? "bg-red-500" : isNearCap ? "bg-amber-500" : "bg-emerald-500"
                      }`}
                      style={{ width: `${Math.min(loadPercentage, 100)}%` }}
                    />
                  </div>
                </div>

                {/* Assigned Courses Pills */}
                <div className="mt-4 flex flex-wrap gap-1.5">
                  {coursesList.map((course, idx) => (
                    <span key={idx} className="text-[11px] bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2.5 py-1 rounded-lg font-bold border border-slate-200 dark:border-slate-700">
                      {course}
                    </span>
                  ))}
                </div>
              </div>

              {/* Action Hint Footer */}
              <div className="mt-5 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-blue-600 dark:text-blue-400 font-bold group-hover:translate-x-0.5 transition-transform">
                <span>Inspect Dossier & Schedule</span>
                <span>→</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* 4. Slide-Over Master Dossier Drawer */}
      {selectedFaculty && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 backdrop-blur-sm flex justify-end animate-in fade-in">
          <div className="w-full max-w-xl bg-white dark:bg-slate-900 h-full shadow-2xl p-6 flex flex-col justify-between overflow-y-auto animate-in slide-in-from-right duration-200 border-l border-slate-200 dark:border-slate-800">
            <div className="space-y-6">

              {/* Drawer Top Header */}
              <div className="flex justify-between items-start pb-4 border-b border-slate-200 dark:border-slate-800">
                <div>
                  <span className="text-xs text-blue-600 dark:text-blue-400 font-bold">{selectedFaculty.employee_id || `VF-ACSE-${selectedFaculty.id}`}</span>
                  <h2 className="text-xl font-bold text-slate-900 dark:text-white">{selectedFaculty.name}</h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{selectedFaculty.designation} • Department of ACSE</p>
                </div>
                <button
                  onClick={() => setSelectedFaculty(null)}
                  className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Workload Metric Gauge */}
              <div className="p-4 bg-slate-50 dark:bg-slate-800/60 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-2">
                <div className="flex justify-between text-xs font-bold text-slate-700 dark:text-slate-300">
                  <span>Weekly Teaching Workload</span>
                  <span>{facultySchedule.length || (selectedFaculty.current_weekly_hours ?? selectedFaculty.hours_this_week ?? 12)} / {(selectedFaculty.max_hours_per_week ?? 16)} Hours</span>
                </div>
                <div className="w-full h-3 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      (facultySchedule.length || 12) > (selectedFaculty.max_hours_per_week ?? 16) ? "bg-red-500" : "bg-blue-600"
                    }`}
                    style={{ width: `${Math.min((((facultySchedule.length || 12) / (selectedFaculty.max_hours_per_week ?? 16)) * 100), 100)}%` }}
                  />
                </div>
              </div>

              {/* Quick Academic Policy Limits */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-4 bg-blue-50 dark:bg-blue-950/40 rounded-2xl border border-blue-100 dark:border-blue-800/60">
                  <span className="text-[11px] text-blue-700 dark:text-blue-300 font-bold uppercase">Weekly Maximum Cap</span>
                  <p className="text-base font-extrabold text-blue-950 dark:text-blue-100 mt-1">
                    {selectedFaculty.max_hours_per_week || 16} Hours / Week
                  </p>
                </div>

                <div className="p-4 bg-purple-50 dark:bg-purple-950/40 rounded-2xl border border-purple-100 dark:border-purple-800/60">
                  <span className="text-[11px] text-purple-700 dark:text-purple-300 font-bold uppercase">Daily Class Limit</span>
                  <p className="text-base font-extrabold text-purple-950 dark:text-purple-100 mt-1">
                    Max {selectedFaculty.max_daily_classes || 5} Classes / Day
                  </p>
                </div>
              </div>

              {/* Assigned Subjects & Course Codes */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Assigned Subjects & Electives</h4>
                <div className="flex flex-wrap gap-2">
                  {(selectedFaculty.subjects_taught || ["DS", "AI", "DBMS"]).map((c, i) => (
                    <span key={i} className="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-xs font-bold rounded-xl border border-slate-200 dark:border-slate-700">
                      {c}
                    </span>
                  ))}
                </div>
              </div>

              {/* Actual Assigned Weekly Teaching Schedule Grid */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Active Teaching Schedule & Assigned Periods</h4>
                  {loadingSchedule && <Loader2 className="w-3.5 h-3.5 text-blue-600 animate-spin" />}
                </div>

                <div className="grid grid-cols-6 gap-1.5 bg-slate-50 dark:bg-slate-800/60 p-3 rounded-2xl border border-slate-200 dark:border-slate-800">
                  {DAYS.map((day) => (
                    <div key={day} className="text-center">
                      <span className="text-[11px] font-extrabold text-slate-700 dark:text-slate-300 block mb-1.5">{day}</span>
                      <div className="space-y-1.5">
                        {PERIODS.map((p) => {
                          const slot = getScheduledSlot(day, p);
                          if (slot) {
                            return (
                              <div
                                key={p}
                                title={`${slot.subject || "Teaching Slot"} (${slot.section || ""}) - Room ${slot.room || ""}`}
                                className="w-full py-1.5 px-1 rounded-lg bg-blue-600 text-white text-[9px] font-extrabold shadow-sm border border-blue-700 leading-tight truncate"
                              >
                                <span className="block font-black">{slot.subject || `P${p}`}</span>
                                <span className="block opacity-90 text-[8px] font-medium">{slot.section || ""}</span>
                                <span className="block opacity-75 text-[7.5px] font-mono">{slot.room || ""}</span>
                              </div>
                            );
                          }

                          return (
                            <div
                              key={p}
                              className="w-full py-1.5 px-1 rounded-lg bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 text-[9px] font-semibold flex items-center justify-center border border-emerald-500/25"
                            >
                              Free
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>

            {/* Footer Buttons */}
            <div className="pt-6 mt-6 border-t border-slate-200 dark:border-slate-800 flex gap-3">
              <button
                onClick={() => setSelectedFaculty(null)}
                className="flex-1 py-3 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
              >
                Close
              </button>

              <button
                onClick={() => {
                  const fac = selectedFaculty;
                  setSelectedFaculty(null);
                  handleOpenEditModal(fac);
                }}
                className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-md cursor-pointer inline-flex items-center justify-center gap-2"
              >
                <Edit className="w-4 h-4" /> Edit Faculty Profile
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add / Edit Modal */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl p-6 w-full max-w-md space-y-4">
            <div className="flex justify-between items-center pb-3 border-b border-slate-200 dark:border-slate-800">
              <h3 className="font-bold text-slate-900 dark:text-white text-base">
                {editingFaculty ? "Edit Faculty Profile" : "Add New Instructor"}
              </h3>
              <button onClick={() => setShowEditModal(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveForm} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-xs font-bold text-slate-900 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Employee ID</label>
                  <input
                    type="text"
                    value={formData.employee_id}
                    onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-xs font-bold text-slate-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Designation</label>
                  <select
                    value={formData.designation}
                    onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-xs font-bold text-slate-900 dark:text-white"
                  >
                    <option value="Professor">Professor</option>
                    <option value="Associate Professor">Associate Professor</option>
                    <option value="Assistant Professor">Assistant Professor</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Max Weekly Hours</label>
                  <input
                    type="number"
                    min={6}
                    max={24}
                    value={formData.max_hours_per_week}
                    onChange={(e) => setFormData({ ...formData, max_hours_per_week: Number(e.target.value) })}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-xs font-bold text-slate-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Max Daily Classes</label>
                  <input
                    type="number"
                    min={1}
                    max={8}
                    value={formData.max_daily_classes}
                    onChange={(e) => setFormData({ ...formData, max_daily_classes: Number(e.target.value) })}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-xs font-bold text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Assigned Subjects (comma separated)</label>
                <input
                  type="text"
                  placeholder="e.g. DS, AI, DBMS"
                  value={formData.subjects_taught_str}
                  onChange={(e) => setFormData({ ...formData, subjects_taught_str: e.target.value })}
                  className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-xs font-bold text-slate-900 dark:text-white"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="px-4 py-2 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-300"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-md"
                >
                  Save Profile
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
