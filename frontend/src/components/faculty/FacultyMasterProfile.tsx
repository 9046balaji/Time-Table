"use client";

import React, { useState, useMemo } from "react";
import {
  Users,
  Search,
  Filter,
  UserCheck,
  Phone,
  Mail,
  Building2,
  BookOpen,
  Plus,
  Edit,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  Layers,
  X,
  Sparkles,
  Award,
  Clock,
  Printer,
  Download,
  Calendar,
  Grid,
  List,
  Check,
  Shield,
  FileText,
  SlidersHorizontal
} from "lucide-react";
import { Faculty, Subject, Section } from "@/lib/types";

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

type SubTab = "roster" | "dossier";


export const FacultyMasterProfile: React.FC<FacultyMasterProfileProps> = ({
  facultyList,
  subjectList = [],
  sectionList = [],
  onAddFaculty,
  onUpdateFaculty,
  onDeleteFaculty
}) => {
  // Sub-Navigation Tab State
  const [activeSubTab, setActiveSubTab] = useState<SubTab>("roster");

  // Roster Controls
  const [searchQuery, setSearchQuery] = useState("");
  const [designationFilter, setDesignationFilter] = useState("ALL");
  const [workloadFilter, setWorkloadFilter] = useState("ALL");
  const [viewMode, setViewMode] = useState<"CARDS" | "TABLE">("CARDS");

  // Selected Faculty for Dossier Inspector & Availability Matrix
  const [selectedFacultyId, setSelectedFacultyId] = useState<number>(facultyList[0]?.id || 1);

  // Add/Edit Modal State
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingFaculty, setEditingFaculty] = useState<Partial<Faculty> | null>(null);

  // Form Fields State
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

  const selectedFaculty = useMemo(() => {
    return facultyList.find((f) => f.id === selectedFacultyId) || facultyList[0] || null;
  }, [facultyList, selectedFacultyId]);

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
      phone: formData.phone || "N/A",
      email: formData.email,
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

  const [sortBy, setSortBy] = useState<string>("NAME_ASC");

  // Filtered & Sorted Faculty Roster
  const filteredFaculty = useMemo(() => {
    const list = facultyList.filter((fac) => {
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const matchName = fac.name.toLowerCase().includes(q);
        const matchEmpId = (fac.employee_id || "").toLowerCase().includes(q);
        const matchPhone = (fac.phone || "").toLowerCase().includes(q);
        const matchSubj = (fac.subjects_taught || []).some((s) => s.toLowerCase().includes(q));
        if (!matchName && !matchEmpId && !matchPhone && !matchSubj) return false;
      }

      if (designationFilter !== "ALL" && fac.designation !== designationFilter) {
        return false;
      }

      const curHours = fac.current_weekly_hours ?? fac.hours_this_week ?? 12;
      const maxHours = fac.max_hours_per_week ?? fac.max_hours ?? 16;
      if (workloadFilter === "OVERLOAD" && curHours <= maxHours) return false;
      if (workloadFilter === "UNDERLOAD" && curHours >= 8) return false;

      return true;
    });

    return list.sort((a, b) => {
      if (sortBy === "NAME_ASC") return a.name.localeCompare(b.name);
      if (sortBy === "NAME_DESC") return b.name.localeCompare(a.name);
      if (sortBy === "LOAD_DESC") {
        const loadA = a.current_weekly_hours ?? a.hours_this_week ?? 12;
        const loadB = b.current_weekly_hours ?? b.hours_this_week ?? 12;
        return loadB - loadA;
      }
      if (sortBy === "LOAD_ASC") {
        const loadA = a.current_weekly_hours ?? a.hours_this_week ?? 12;
        const loadB = b.current_weekly_hours ?? b.hours_this_week ?? 12;
        return loadA - loadB;
      }
      if (sortBy === "EMPID_ASC") {
        return (a.employee_id || "").localeCompare(b.employee_id || "");
      }
      return 0;
    });
  }, [facultyList, searchQuery, designationFilter, workloadFilter, sortBy]);

  // Auto-sync selectedFacultyId if current selection is filtered out
  React.useEffect(() => {
    if (filteredFaculty.length > 0) {
      const exists = filteredFaculty.some((f) => f.id === selectedFacultyId);
      if (!exists) {
        setSelectedFacultyId(filteredFaculty[0].id);
      }
    }
  }, [filteredFaculty, selectedFacultyId]);


  // Overall Stats
  const stats = useMemo(() => {
    const total = facultyList.length;
    const profs = facultyList.filter((f) => f.designation.includes("Professor") && !f.designation.includes("Assistant")).length;
    const avgLoad = Math.round(
      facultyList.reduce((acc, f) => acc + (f.current_weekly_hours ?? f.hours_this_week ?? 12), 0) / (total || 1)
    );
    const overloaded = facultyList.filter(
      (f) => (f.current_weekly_hours ?? f.hours_this_week ?? 12) > (f.max_hours_per_week ?? 16)
    ).length;
    return { total, profs, avgLoad, overloaded };
  }, [facultyList]);

  return (
    <div className="space-y-6">

      {/* TOP SUB-TAB NAVIGATION SWITCHER */}
      <div className="bg-white dark:bg-slate-900 p-2 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto p-1 bg-slate-100 dark:bg-slate-800/80 rounded-xl">
          <button
            onClick={() => setActiveSubTab("roster")}
            className={`px-4 py-2 rounded-lg text-xs font-extrabold transition-all inline-flex items-center gap-2 shrink-0 ${
              activeSubTab === "roster"
                ? "bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <Users className="w-4 h-4" /> Faculty Directory ({stats.total})
          </button>

          <button
            onClick={() => setActiveSubTab("dossier")}
            className={`px-4 py-2 rounded-lg text-xs font-extrabold transition-all inline-flex items-center gap-2 shrink-0 ${
              activeSubTab === "dossier"
                ? "bg-white dark:bg-slate-900 text-purple-600 dark:text-purple-400 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <FileText className="w-4 h-4" /> Master Dossier Inspector
          </button>


        </div>

        {/* Global Action Button */}
        <button
          onClick={handleOpenAddModal}
          className="w-full sm:w-auto px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm inline-flex items-center justify-center gap-1.5 shrink-0"
        >
          <Plus className="w-4 h-4" /> Add New Instructor
        </button>
      </div>

      {/* SUB-VIEW 1: FACULTY DIRECTORY & ROSTER */}
      {activeSubTab === "roster" && (
        <div className="space-y-6">


          {/* Unified Search & Filter Toolbar */}
          <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="relative flex-1 w-full">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search by Name, Employee ID (VF-101), Phone (91776...), or Subject..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
              />
            </div>

            <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto justify-end">
              <select
                value={designationFilter}
                onChange={(e) => setDesignationFilter(e.target.value)}
                className="px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-900 dark:text-white shrink-0"
              >
                <option value="ALL">All Designations</option>
                <option value="Professor">Professor</option>
                <option value="Associate Professor">Associate Professor</option>
                <option value="Assistant Professor">Assistant Professor</option>
              </select>

              <select
                value={workloadFilter}
                onChange={(e) => setWorkloadFilter(e.target.value)}
                className="px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-900 dark:text-white shrink-0"
              >
                <option value="ALL">All Workloads</option>
                <option value="OVERLOAD">Overloaded (&gt;16h)</option>
                <option value="UNDERLOAD">Underloaded (&lt;8h)</option>
              </select>

              {/* Sort Selector */}
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-900 dark:text-white shrink-0"
              >
                <option value="NAME_ASC">Sort: Name (A-Z)</option>
                <option value="NAME_DESC">Sort: Name (Z-A)</option>
                <option value="LOAD_DESC">Sort: Workload (High to Low)</option>
                <option value="LOAD_ASC">Sort: Workload (Low to High)</option>
                <option value="EMPID_ASC">Sort: Employee ID</option>
              </select>


              <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl shrink-0">
                <button
                  onClick={() => setViewMode("CARDS")}
                  className={`p-1.5 rounded-lg text-xs font-bold transition-all ${
                    viewMode === "CARDS" ? "bg-white dark:bg-slate-900 text-blue-600 shadow-sm" : "text-slate-500"
                  }`}
                >
                  <Grid className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode("TABLE")}
                  className={`p-1.5 rounded-lg text-xs font-bold transition-all ${
                    viewMode === "TABLE" ? "bg-white dark:bg-slate-900 text-blue-600 shadow-sm" : "text-slate-500"
                  }`}
                >
                  <List className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* CARDS VIEW */}
          {viewMode === "CARDS" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredFaculty.map((fac) => {
                const curHours = fac.current_weekly_hours ?? fac.hours_this_week ?? 12;
                const maxHours = fac.max_hours_per_week ?? fac.max_hours ?? 16;
                const pct = Math.min(100, Math.round((curHours / maxHours) * 100));
                const empId = fac.employee_id || `VF-ACSE-${100 + fac.id}`;
                const subsList = fac.subjects_taught && fac.subjects_taught.length > 0
                  ? fac.subjects_taught
                  : ["22CS406", "BDA [P]", "Cloud Computing", "MLOps"];

                return (
                  <div
                    key={fac.id}
                    className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-all flex flex-col justify-between gap-4"
                  >
                    <div className="space-y-3">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-1.5">
                            <span className="px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 font-mono text-[10px] font-extrabold">
                              {empId}
                            </span>
                            <span className="text-[10px] font-bold text-slate-400">{fac.designation}</span>
                          </div>
                          <h3 className="text-base font-extrabold text-slate-900 dark:text-white mt-1 leading-snug">
                            {fac.name}
                          </h3>
                        </div>

                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleOpenEditModal(fac)}
                            className="p-1.5 text-slate-400 hover:text-blue-600 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                          >
                            <Edit className="w-3.5 h-3.5" />
                          </button>
                          {onDeleteFaculty && (
                            <button
                              onClick={() => onDeleteFaculty(fac.id)}
                              className="p-1.5 text-slate-400 hover:text-red-600 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </div>

                      <div className="space-y-1 text-xs text-slate-600 dark:text-slate-400">
                        <div className="flex items-center gap-1.5 font-medium">
                          <Phone className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                          <a href={`tel:${fac.phone || "9177649711"}`} className="hover:underline font-bold text-slate-800 dark:text-slate-200">
                            {fac.phone || "+91 91776 49711"}
                          </a>
                        </div>
                        {fac.email && (
                          <div className="flex items-center gap-1.5 font-medium">
                            <Mail className="w-3.5 h-3.5 text-purple-500 shrink-0" />
                            <span className="truncate">{fac.email}</span>
                          </div>
                        )}
                      </div>

                      <div className="space-y-1.5 bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl border border-slate-100 dark:border-slate-700/60">
                        <div className="flex items-center justify-between text-[11px] font-bold">
                          <span className="text-slate-500 dark:text-slate-400">Weekly Workload:</span>
                          <span className={curHours > maxHours ? "text-red-600" : "text-emerald-600"}>
                            {curHours} / {maxHours} hrs ({pct}%)
                          </span>
                        </div>
                        <div className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className={`h-full transition-all ${
                              curHours > maxHours ? "bg-red-500" : "bg-gradient-to-r from-blue-500 to-emerald-500"
                            }`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>

                      <div className="space-y-1">
                        <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Courses Taught:</span>
                        <div className="flex flex-wrap gap-1">
                          {subsList.map((sCode, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-0.5 rounded-md bg-purple-50 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 font-bold text-[10px] border border-purple-200 dark:border-purple-800"
                            >
                              {sCode}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => {
                        setSelectedFacultyId(fac.id);
                        setActiveSubTab("dossier");
                      }}
                      className="w-full py-2 bg-slate-100 dark:bg-slate-800 hover:bg-blue-600 hover:text-white dark:hover:bg-blue-600 text-slate-700 dark:text-slate-300 font-bold text-xs rounded-xl transition-all inline-flex items-center justify-center gap-1.5"
                    >
                      <BookOpen className="w-3.5 h-3.5" /> Inspect Master Dossier
                    </button>
                  </div>
                );
              })}
            </div>
          )}

          {/* TABLE VIEW */}
          {viewMode === "TABLE" && (
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[900px] border-collapse text-xs text-left">
                  <thead>
                    <tr className="bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-bold border-b border-slate-200 dark:border-slate-700">
                      <th className="p-3">Employee ID</th>
                      <th className="p-3">Faculty Name</th>
                      <th className="p-3">Designation</th>
                      <th className="p-3">Contact Phone</th>
                      <th className="p-3">Subjects Taught</th>
                      <th className="p-3">Weekly Workload</th>
                      <th className="p-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {filteredFaculty.map((fac) => {
                      const curHours = fac.current_weekly_hours ?? fac.hours_this_week ?? 12;
                      const maxHours = fac.max_hours_per_week ?? fac.max_hours ?? 16;
                      const empId = fac.employee_id || `VF-ACSE-${100 + fac.id}`;

                      return (
                        <tr key={fac.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                          <td className="p-3 font-mono font-extrabold text-blue-600 dark:text-blue-400">{empId}</td>
                          <td className="p-3 font-extrabold text-slate-900 dark:text-slate-100">{fac.name}</td>
                          <td className="p-3 font-medium text-slate-600 dark:text-slate-400">{fac.designation}</td>
                          <td className="p-3 font-bold text-slate-800 dark:text-slate-200">{fac.phone || "+91 91776 49711"}</td>
                          <td className="p-3">
                            <div className="flex flex-wrap gap-1">
                              {(fac.subjects_taught && fac.subjects_taught.length > 0
                                ? fac.subjects_taught
                                : ["22CS406", "BDA [P]"]
                              ).map((s, i) => (
                                <span key={i} className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-[10px] font-bold">
                                  {s}
                                </span>
                              ))}
                            </div>
                          </td>
                          <td className="p-3 font-bold">
                            <span className={curHours > maxHours ? "text-red-600" : "text-emerald-600"}>
                              {curHours} / {maxHours} hrs
                            </span>
                          </td>
                          <td className="p-3 text-right">
                            <button
                              onClick={() => {
                                setSelectedFacultyId(fac.id);
                                setActiveSubTab("dossier");
                              }}
                              className="px-3 py-1 bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400 font-bold rounded-lg hover:bg-blue-100 text-[11px]"
                            >
                              Dossier
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* SUB-VIEW 2: MASTER DOSSIER INSPECTOR */}
      {activeSubTab === "dossier" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Faculty Selector List */}
          <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
            <h3 className="text-xs font-extrabold uppercase text-slate-400 tracking-wider">Select Faculty Dossier</h3>
            <div className="space-y-1 max-h-[600px] overflow-y-auto pr-1">
              {facultyList.map((fac) => {
                const isSelected = selectedFacultyId === fac.id;
                return (
                  <button
                    key={fac.id}
                    onClick={() => setSelectedFacultyId(fac.id)}
                    className={`w-full text-left p-3 rounded-xl transition-all flex items-center justify-between border ${
                      isSelected
                        ? "bg-blue-50 dark:bg-blue-950/80 border-blue-300 dark:border-blue-700 text-blue-900 dark:text-blue-200"
                        : "bg-white dark:bg-slate-900 border-slate-100 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50"
                    }`}
                  >
                    <div>
                      <div className="font-extrabold text-xs leading-snug">{fac.name}</div>
                      <div className="text-[10px] font-mono text-slate-400">{fac.employee_id || `VF-${fac.id}`} • {fac.designation}</div>
                    </div>
                    {isSelected && <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0" />}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right Master Dossier Panel */}
          {selectedFaculty && (
            <div className="lg:col-span-2 bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
                <div>
                  <span className="px-2.5 py-0.5 rounded bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 font-mono text-xs font-bold">
                    {selectedFaculty.employee_id || `VF-ACSE-${100 + selectedFaculty.id}`}
                  </span>
                  <h2 className="text-xl font-black text-slate-900 dark:text-white mt-1">{selectedFaculty.name}</h2>
                  <p className="text-xs text-slate-500 font-medium mt-0.5">{selectedFaculty.designation} • ACSE Department</p>
                </div>

                <button
                  onClick={() => handleOpenEditModal(selectedFaculty)}
                  className="px-3.5 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 font-bold text-xs rounded-xl inline-flex items-center gap-1.5"
                >
                  <Edit className="w-3.5 h-3.5" /> Edit Master Profile
                </button>
              </div>

              {/* Quick Contact & Workload Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-slate-50 dark:bg-slate-800/60 p-4 rounded-xl border border-slate-100 dark:border-slate-700/60">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Contact Phone</span>
                  <div className="text-sm font-extrabold text-blue-600 dark:text-blue-400 mt-1">
                    <a href={`tel:${selectedFaculty.phone || "9177649711"}`} className="hover:underline">
                      {selectedFaculty.phone || "+91 91776 49711"}
                    </a>
                  </div>
                </div>

                <div className="bg-slate-50 dark:bg-slate-800/60 p-4 rounded-xl border border-slate-100 dark:border-slate-700/60">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Weekly Hours Cap</span>
                  <div className="text-sm font-extrabold text-slate-900 dark:text-white mt-1">
                    {selectedFaculty.max_hours_per_week || 16} Hours Limit
                  </div>
                </div>

                <div className="bg-slate-50 dark:bg-slate-800/60 p-4 rounded-xl border border-slate-100 dark:border-slate-700/60">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Daily Class Limit</span>
                  <div className="text-sm font-extrabold text-slate-900 dark:text-white mt-1">
                    Max {selectedFaculty.max_daily_classes || 5} Classes/Day
                  </div>
                </div>
              </div>

              {/* Courses & Labs Taught */}
              <div className="space-y-2">
                <h4 className="text-xs font-extrabold uppercase text-slate-400 tracking-wider">Courses & Practical Labs Taught</h4>
                <div className="flex flex-wrap gap-2">
                  {(selectedFaculty.subjects_taught && selectedFaculty.subjects_taught.length > 0
                    ? selectedFaculty.subjects_taught
                    : ["22CS406 (Privacy Preserving)", "BDA [P] (Big Data Lab)", "Cloud Computing [L]", "MLOps Lab"]
                  ).map((sub, i) => (
                    <span key={i} className="px-3 py-1.5 rounded-xl bg-purple-50 dark:bg-purple-950/60 text-purple-800 dark:text-purple-200 font-extrabold text-xs border border-purple-200 dark:border-purple-800">
                      {sub}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}



      {/* ADD / EDIT FACULTY FORM MODAL */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <h3 className="text-base font-extrabold text-slate-900 dark:text-white">
                {editingFaculty ? "Edit Faculty Master Record" : "Add New Faculty Instructor"}
              </h3>
              <button onClick={() => setShowEditModal(false)} className="text-slate-400 hover:text-white font-bold">
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveForm} className="space-y-3 text-xs">
              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Faculty Full Name:</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Dr. Kiran Kumar Kaveti"
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white font-bold"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Employee ID:</label>
                  <input
                    type="text"
                    value={formData.employee_id}
                    onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                    placeholder="VF-ACSE-104"
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white font-mono"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Designation Rank:</label>
                  <select
                    value={formData.designation}
                    onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white font-bold"
                  >
                    <option value="Professor">Professor</option>
                    <option value="Associate Professor">Associate Professor</option>
                    <option value="Assistant Professor">Assistant Professor</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Contact Phone:</label>
                  <input
                    type="text"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    placeholder="9177649711"
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white font-bold"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Max Weekly Hours:</label>
                  <input
                    type="number"
                    min={1}
                    max={30}
                    value={formData.max_hours_per_week}
                    onChange={(e) => setFormData({ ...formData, max_hours_per_week: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white font-bold"
                  />
                </div>
              </div>

              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Subjects Taught (comma separated):</label>
                <input
                  type="text"
                  value={formData.subjects_taught_str}
                  onChange={(e) => setFormData({ ...formData, subjects_taught_str: e.target.value })}
                  placeholder="22CS406, BDA [P], Cloud Computing, MLOps"
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white font-semibold"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="px-4 py-2 border border-slate-300 text-slate-600 rounded-xl font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold shadow-md"
                >
                  Save Master Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
