"use client";

import React, { useState, useMemo } from "react";
import {
  BookOpen,
  Search,
  Filter,
  Plus,
  Edit,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  Layers,
  X,
  Sparkles,
  Cpu,
  Grid,
  List,
  Calendar,
  Check,
  Award,
  Clock,
  Zap,
  Bookmark,
  FileText
} from "lucide-react";
import { Subject } from "@/lib/types";

interface CurriculumMasterProfileProps {
  subjectList: Subject[];
  onAddSubject?: (newSub: Partial<Subject>) => void;
  onUpdateSubject?: (id: number, updatedSub: Partial<Subject>) => void;
  onDeleteSubject?: (id: number) => void;
}

type SubTab = "matrix" | "labs" | "credits";

export const CurriculumMasterProfile: React.FC<CurriculumMasterProfileProps> = ({
  subjectList,
  onAddSubject,
  onUpdateSubject,
  onDeleteSubject
}) => {
  // Sub-Tab Navigation
  const [activeSubTab, setActiveSubTab] = useState<SubTab>("matrix");

  // Roster Controls
  const [searchQuery, setSearchQuery] = useState("");
  const [yearFilter, setYearFilter] = useState("ALL");
  const [branchFilter, setBranchFilter] = useState("ALL");
  const [viewMode, setViewMode] = useState<"CARDS" | "TABLE">("CARDS");

  // Selected Subject for Dossier Drawer Modal
  const [selectedSubjectId, setSelectedSubjectId] = useState<number>(subjectList[0]?.id || 1);

  // Add/Edit Form Modal State
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingSubject, setEditingSubject] = useState<Partial<Subject> | null>(null);

  // Form Fields State
  const [formData, setFormData] = useState({
    code: "",
    full_name: "",
    year_level: "II Year",
    branch: "CSE (AIML)",
    lecture_hours: 3,
    tutorial_hours: 0,
    lab_hours: 0,
    slot_type: "L",
    requires_consecutive: 2,
    gpu_required: false
  });

  const selectedSubject = useMemo(() => {
    return subjectList.find((s) => s.id === selectedSubjectId) || subjectList[0] || null;
  }, [subjectList, selectedSubjectId]);

  const handleOpenAddModal = () => {
    setEditingSubject(null);
    setFormData({
      code: "",
      full_name: "",
      year_level: "II Year",
      branch: "CSE (AIML)",
      lecture_hours: 3,
      tutorial_hours: 0,
      lab_hours: 0,
      slot_type: "L",
      requires_consecutive: 2,
      gpu_required: false
    });
    setShowEditModal(true);
  };

  const handleOpenEditModal = (sub: Subject) => {
    setEditingSubject(sub);
    setFormData({
      code: sub.code || "",
      full_name: sub.full_name || "",
      year_level: String(sub.year_level || "II Year"),
      branch: sub.branch || "CSE (AIML)",
      lecture_hours: sub.lecture_hours || 3,
      tutorial_hours: sub.tutorial_hours || 0,
      lab_hours: sub.lab_hours || 0,
      slot_type: sub.slot_type || "L",
      requires_consecutive: sub.requires_consecutive || 2,
      gpu_required: sub.gpu_required || false
    });
    setShowEditModal(true);
  };

  const handleSaveForm = (e: React.FormEvent) => {
    e.preventDefault();
    const isLab = formData.slot_type === "P" || formData.lab_hours > 0;
    const payload: Partial<Subject> = {
      code: formData.code,
      full_name: formData.full_name,
      year_level: formData.year_level,
      branch: formData.branch,
      lecture_hours: Number(formData.lecture_hours),
      tutorial_hours: Number(formData.tutorial_hours),
      lab_hours: Number(formData.lab_hours),
      is_lab: isLab,
      slot_type: formData.slot_type,
      requires_consecutive: Number(formData.requires_consecutive),
      gpu_required: formData.gpu_required
    };

    if (editingSubject && editingSubject.id && onUpdateSubject) {
      onUpdateSubject(editingSubject.id, payload);
    } else if (onAddSubject) {
      onAddSubject(payload);
    }
    setShowEditModal(false);
  };

  // Filtered Subject Inventory
  const filteredSubjects = useMemo(() => {
    return subjectList.filter((sub) => {
      // Search Filter (Code, Title, Year)
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const matchCode = sub.code.toLowerCase().includes(q);
        const matchTitle = sub.full_name.toLowerCase().includes(q);
        if (!matchCode && !matchTitle) return false;
      }

      // Year Filter
      const yLvl = String(sub.year_level || "");
      if (yearFilter !== "ALL") {
        if (yearFilter === "II" && !yLvl.includes("II") && sub.code.startsWith("22CS") === false) return false;
        if (yearFilter === "III" && !yLvl.includes("III")) return false;
        if (yearFilter === "IV" && !yLvl.includes("IV")) return false;
      }

      // Branch Filter
      if (branchFilter !== "ALL" && (sub.branch || "").includes(branchFilter) === false) {
        return false;
      }

      return true;
    });
  }, [subjectList, searchQuery, yearFilter, branchFilter]);

  // Practical Labs subset
  const labSubjects = useMemo(() => {
    return subjectList.filter((sub) => sub.is_lab || sub.slot_type === "P" || sub.lab_hours > 0 || sub.gpu_required);
  }, [subjectList]);

  return (
    <div className="space-y-6">

      {/* TOP SUB-TAB NAVIGATION SWITCHER */}
      <div className="bg-white dark:bg-slate-900 p-2 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto p-1 bg-slate-100 dark:bg-slate-800/80 rounded-xl">
          <button
            onClick={() => setActiveSubTab("matrix")}
            className={`px-4 py-2 rounded-lg text-xs font-extrabold transition-all inline-flex items-center gap-2 shrink-0 ${
              activeSubTab === "matrix"
                ? "bg-white dark:bg-slate-900 text-purple-600 dark:text-purple-400 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <BookOpen className="w-4 h-4" /> Year & Branch Curriculum ({subjectList.length})
          </button>

          <button
            onClick={() => setActiveSubTab("labs")}
            className={`px-4 py-2 rounded-lg text-xs font-extrabold transition-all inline-flex items-center gap-2 shrink-0 ${
              activeSubTab === "labs"
                ? "bg-white dark:bg-slate-900 text-teal-600 dark:text-teal-400 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <Cpu className="w-4 h-4" /> Practical Labs & GPU Rules ({labSubjects.length})
          </button>

          <button
            onClick={() => setActiveSubTab("credits")}
            className={`px-4 py-2 rounded-lg text-xs font-extrabold transition-all inline-flex items-center gap-2 shrink-0 ${
              activeSubTab === "credits"
                ? "bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <Clock className="w-4 h-4" /> L-T-P Credit Rules Audit
          </button>
        </div>

        {/* Global Action Button */}
        <button
          onClick={handleOpenAddModal}
          className="w-full sm:w-auto px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm inline-flex items-center justify-center gap-1.5 shrink-0"
        >
          <Plus className="w-4 h-4" /> Add Subject Curriculum
        </button>
      </div>

      {/* SUB-VIEW 1: YEAR & BRANCH CURRICULUM MATRIX */}
      {activeSubTab === "matrix" && (
        <div className="space-y-6">
          {/* Search & Filter Toolbar */}
          <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="relative flex-1 w-full">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search subject by Code (22CS406, SFCDS, DL) or Course Title..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 font-medium"
              />
            </div>

            <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto justify-end">
              <select
                value={yearFilter}
                onChange={(e) => setYearFilter(e.target.value)}
                className="px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-900 dark:text-white shrink-0"
              >
                <option value="ALL">All Academic Years</option>
                <option value="II">II Year (Sem I)</option>
                <option value="III">III Year (Sem I)</option>
                <option value="IV">IV Year (Sem I)</option>
              </select>

              <select
                value={branchFilter}
                onChange={(e) => setBranchFilter(e.target.value)}
                className="px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-900 dark:text-white shrink-0"
              >
                <option value="ALL">All Branches</option>
                <option value="AIML">CSE (AIML)</option>
                <option value="Core">CSE (Core)</option>
                <option value="DS">CSE (Data Science)</option>
                <option value="CS">CSE (Cyber Security)</option>
              </select>

              <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl shrink-0">
                <button
                  onClick={() => setViewMode("CARDS")}
                  className={`p-1.5 rounded-lg text-xs font-bold transition-all ${
                    viewMode === "CARDS" ? "bg-white dark:bg-slate-900 text-purple-600 shadow-sm" : "text-slate-500"
                  }`}
                >
                  <Grid className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode("TABLE")}
                  className={`p-1.5 rounded-lg text-xs font-bold transition-all ${
                    viewMode === "TABLE" ? "bg-white dark:bg-slate-900 text-purple-600 shadow-sm" : "text-slate-500"
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
              {filteredSubjects.map((sub) => {
                const isLab = sub.is_lab || sub.slot_type === "P" || sub.lab_hours > 0;
                const totHours = (sub.lecture_hours || 0) + (sub.tutorial_hours || 0) + (sub.lab_hours || 0);

                return (
                  <div
                    key={sub.id}
                    className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-all flex flex-col justify-between gap-4"
                  >
                    <div className="space-y-3">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-1.5">
                            <span className="px-2.5 py-0.5 rounded bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 font-mono text-xs font-black">
                              {sub.code}
                            </span>
                            <span className="text-[10px] font-bold text-slate-400 uppercase">
                              {sub.slot_type === "P" ? "Practical Lab" : sub.slot_type === "T" ? "Tutorial" : "Theory Lecture"}
                            </span>
                          </div>
                          <h3 className="text-base font-extrabold text-slate-900 dark:text-white mt-1 leading-snug">
                            {sub.full_name}
                          </h3>
                        </div>

                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleOpenEditModal(sub)}
                            className="p-1.5 text-slate-400 hover:text-purple-600 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                          >
                            <Edit className="w-3.5 h-3.5" />
                          </button>
                          {onDeleteSubject && (
                            <button
                              onClick={() => onDeleteSubject(sub.id)}
                              className="p-1.5 text-slate-400 hover:text-red-600 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </div>

                      {/* L-T-P Credit Pills */}
                      <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl border border-slate-100 dark:border-slate-700/60 text-xs">
                        <div className="flex-1 text-center border-r border-slate-200 dark:border-slate-700 pr-2">
                          <span className="text-[10px] font-bold text-slate-400 block">Lecture (L)</span>
                          <span className="font-black text-slate-900 dark:text-white text-sm">{sub.lecture_hours || 0} hrs</span>
                        </div>
                        <div className="flex-1 text-center border-r border-slate-200 dark:border-slate-700 px-2">
                          <span className="text-[10px] font-bold text-slate-400 block">Tutorial (T)</span>
                          <span className="font-black text-slate-900 dark:text-white text-sm">{sub.tutorial_hours || 0} hrs</span>
                        </div>
                        <div className="flex-1 text-center pl-2">
                          <span className="text-[10px] font-bold text-slate-400 block">Practical (P)</span>
                          <span className="font-black text-purple-600 dark:text-purple-400 text-sm">{sub.lab_hours || (isLab ? 2 : 0)} hrs</span>
                        </div>
                      </div>

                      {/* Room & Constraint Badges */}
                      <div className="flex flex-wrap gap-1.5">
                        {sub.gpu_required && (
                          <span className="px-2 py-0.5 rounded bg-purple-100 text-purple-800 text-[10px] font-extrabold">
                            ⚡ High-GPU Compute Required
                          </span>
                        )}
                        {isLab && (
                          <span className="px-2 py-0.5 rounded bg-teal-100 text-teal-800 text-[10px] font-extrabold">
                            🔒 {sub.requires_consecutive || 2} Consecutive Periods
                          </span>
                        )}
                      </div>
                    </div>

                    <button
                      onClick={() => setSelectedSubjectId(sub.id)}
                      className="w-full py-2 bg-slate-100 dark:bg-slate-800 hover:bg-purple-600 hover:text-white dark:hover:bg-purple-600 text-slate-700 dark:text-slate-300 font-bold text-xs rounded-xl transition-all inline-flex items-center justify-center gap-1.5"
                    >
                      <BookOpen className="w-3.5 h-3.5" /> View Full Course Dossier
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
                <table className="w-full min-w-[850px] border-collapse text-xs text-left">
                  <thead>
                    <tr className="bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-bold border-b border-slate-200 dark:border-slate-700">
                      <th className="p-3">Course Code</th>
                      <th className="p-3">Course Title</th>
                      <th className="p-3">L-T-P Hours</th>
                      <th className="p-3">Slot Type</th>
                      <th className="p-3">GPU / Lab Rule</th>
                      <th className="p-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {filteredSubjects.map((sub) => (
                      <tr key={sub.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                        <td className="p-3 font-mono font-extrabold text-purple-600 dark:text-purple-400 text-sm">{sub.code}</td>
                        <td className="p-3 font-extrabold text-slate-900 dark:text-slate-100">{sub.full_name}</td>
                        <td className="p-3 font-bold text-slate-700 dark:text-slate-300">
                          {sub.lecture_hours || 0}L - {sub.tutorial_hours || 0}T - {sub.lab_hours || (sub.is_lab ? 2 : 0)}P
                        </td>
                        <td className="p-3">
                          <span className="px-2.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 font-bold text-[10px]">
                            {sub.slot_type || "L"}
                          </span>
                        </td>
                        <td className="p-3">
                          {sub.gpu_required ? (
                            <span className="px-2 py-0.5 rounded bg-purple-100 text-purple-800 font-extrabold text-[10px]">High-GPU Lab</span>
                          ) : sub.is_lab ? (
                            <span className="px-2 py-0.5 rounded bg-teal-100 text-teal-800 font-bold text-[10px]">Computer Lab</span>
                          ) : (
                            <span className="text-slate-400 text-[10px]">Classroom</span>
                          )}
                        </td>
                        <td className="p-3 text-right">
                          <button
                            onClick={() => setSelectedSubjectId(sub.id)}
                            className="px-3 py-1 bg-purple-50 dark:bg-purple-950 text-purple-600 dark:text-purple-400 font-bold rounded-lg hover:bg-purple-100 text-[11px]"
                          >
                            Dossier
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* SUB-VIEW 2: PRACTICAL LABS & GPU REQUIREMENTS */}
      {activeSubTab === "labs" && (
        <div className="space-y-6">
          <div className="bg-teal-900/10 border border-teal-300 dark:border-teal-800 p-4 rounded-2xl flex items-center justify-between">
            <div>
              <h3 className="text-sm font-extrabold text-teal-900 dark:text-teal-200">Practical Labs & High-GPU Compute Course Catalog</h3>
              <p className="text-xs text-teal-700 dark:text-teal-300 mt-0.5">Courses requiring multi-period consecutive blocks (2–3 periods) and specialized lab venues</p>
            </div>
            <span className="px-3 py-1 bg-teal-600 text-white font-extrabold text-xs rounded-xl">{labSubjects.length} Lab Modules</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {labSubjects.map((sub) => (
              <div key={sub.id} className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-teal-200 dark:border-teal-900/60 shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <span className="px-2.5 py-0.5 rounded bg-teal-100 dark:bg-teal-950 text-teal-700 dark:text-teal-300 font-mono text-xs font-black">
                    {sub.code}
                  </span>
                  <Cpu className="w-5 h-5 text-teal-600" />
                </div>
                <div>
                  <h4 className="text-base font-extrabold text-slate-900 dark:text-white">{sub.full_name}</h4>
                  <p className="text-xs text-slate-500 mt-0.5">Requires {sub.requires_consecutive || 2} Consecutive Periods</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SUB-VIEW 3: CREDIT & SLOT RULES MANAGER */}
      {activeSubTab === "credits" && (
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <h3 className="text-base font-extrabold text-slate-900 dark:text-white">L-T-P Credit Distribution Audit</h3>
          <p className="text-xs text-slate-500">Overview of total weekly hours allocation per course across all semesters</p>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left text-xs">
              <thead>
                <tr className="bg-slate-100 dark:bg-slate-800 font-bold border-b border-slate-200 dark:border-slate-700">
                  <th className="p-3">Code</th>
                  <th className="p-3">Course Name</th>
                  <th className="p-3 text-center">Lecture (L)</th>
                  <th className="p-3 text-center">Tutorial (T)</th>
                  <th className="p-3 text-center">Practical (P)</th>
                  <th className="p-3 text-center">Total Weekly Hours</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {subjectList.map((s) => {
                  const tot = (s.lecture_hours || 0) + (s.tutorial_hours || 0) + (s.lab_hours || (s.is_lab ? 2 : 0));
                  return (
                    <tr key={s.id}>
                      <td className="p-3 font-mono font-bold text-purple-600">{s.code}</td>
                      <td className="p-3 font-bold text-slate-900 dark:text-white">{s.full_name}</td>
                      <td className="p-3 text-center font-bold">{s.lecture_hours || 0}h</td>
                      <td className="p-3 text-center font-bold">{s.tutorial_hours || 0}h</td>
                      <td className="p-3 text-center font-bold text-purple-600">{s.lab_hours || (s.is_lab ? 2 : 0)}h</td>
                      <td className="p-3 text-center font-black text-slate-900 dark:text-white">{tot} Hours/Wk</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ADD / EDIT SUBJECT FORM MODAL */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <h3 className="text-base font-extrabold text-slate-900 dark:text-white">
                {editingSubject ? "Edit Subject Curriculum" : "Add New Subject Course"}
              </h3>
              <button onClick={() => setShowEditModal(false)} className="text-slate-400 hover:text-white font-bold">
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveForm} className="space-y-3 text-xs">
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Subject Code:</label>
                  <input
                    type="text"
                    required
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    placeholder="e.g. 22CS406, DL"
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white font-mono font-bold"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Course Full Title:</label>
                  <input
                    type="text"
                    required
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    placeholder="e.g. Deep Learning & Neural Networks"
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white font-bold"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3 bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl border border-slate-100 dark:border-slate-700">
                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Lecture (L):</label>
                  <input
                    type="number"
                    min={0}
                    max={6}
                    value={formData.lecture_hours}
                    onChange={(e) => setFormData({ ...formData, lecture_hours: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl font-bold"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Tutorial (T):</label>
                  <input
                    type="number"
                    min={0}
                    max={3}
                    value={formData.tutorial_hours}
                    onChange={(e) => setFormData({ ...formData, tutorial_hours: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl font-bold"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Practical (P):</label>
                  <input
                    type="number"
                    min={0}
                    max={6}
                    value={formData.lab_hours}
                    onChange={(e) => setFormData({ ...formData, lab_hours: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl font-bold"
                  />
                </div>
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
                  className="px-5 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-bold shadow-md"
                >
                  Save Subject Course
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
