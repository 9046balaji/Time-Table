"use client";

import React, { useState, useMemo } from "react";
import {
  BookOpen,
  Search,
  Plus,
  Edit,
  Trash2,
  X,
  Cpu,
  Clock,
  Zap,
  Award,
  Bookmark,
  CheckCircle2
} from "lucide-react";
import { Subject } from "@/lib/types";

interface CurriculumMasterProfileProps {
  subjectList: Subject[];
  onAddSubject?: (newSub: Partial<Subject>) => void;
  onUpdateSubject?: (id: number, updatedSub: Partial<Subject>) => void;
  onDeleteSubject?: (id: number) => void;
}

export const CurriculumMasterProfile: React.FC<CurriculumMasterProfileProps> = ({
  subjectList,
  onAddSubject,
  onUpdateSubject,
  onDeleteSubject
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [quickFilter, setQuickFilter] = useState<"ALL" | "LEC" | "LAB" | "GPU">("ALL");

  // Selected Subject for Slide-Over Drawer
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);

  // Edit Modal State
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingSubject, setEditingSubject] = useState<Partial<Subject> | null>(null);

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
      lecture_hours: sub.lecture_hours ?? 3,
      tutorial_hours: sub.tutorial_hours ?? 0,
      lab_hours: sub.lab_hours ?? 0,
      slot_type: sub.slot_type || (sub.is_lab ? "P" : "L"),
      requires_consecutive: sub.requires_consecutive ?? 2,
      gpu_required: sub.gpu_required ?? false
    });
    setShowEditModal(true);
  };

  const handleSaveForm = (e: React.FormEvent) => {
    e.preventDefault();
    const isLab = formData.slot_type === "P" || formData.lab_hours > 0;
    const payload: Partial<Subject> = {
      code: formData.code,
      full_name: formData.full_name,
      lecture_hours: Number(formData.lecture_hours),
      tutorial_hours: Number(formData.tutorial_hours),
      lab_hours: Number(formData.lab_hours),
      slot_type: formData.slot_type,
      is_lab: isLab,
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

  // Filtered Subjects
  const filteredSubjects = useMemo(() => {
    return subjectList.filter((sub) => {
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const matchCode = sub.code.toLowerCase().includes(q);
        const matchName = sub.full_name.toLowerCase().includes(q);
        if (!matchCode && !matchName) return false;
      }

      const isLab = sub.is_lab || sub.slot_type === "P" || sub.lab_hours > 0;
      const isGpu = sub.gpu_required;

      if (quickFilter === "LEC" && isLab) return false;
      if (quickFilter === "LAB" && !isLab) return false;
      if (quickFilter === "GPU" && !isGpu) return false;

      return true;
    });
  }, [subjectList, searchQuery, quickFilter]);

  return (
    <div className="space-y-6">

      {/* 1. Header Action Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Curriculum Subjects & Course Registry</h2>
            <span className="px-2.5 py-0.5 bg-purple-50 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 text-xs font-bold rounded-full border border-purple-200 dark:border-purple-800">
              {subjectList.length} Active Courses
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Click any course card to inspect credit slot breakdown (L-T-P), practical lab span rules, and hardware requirements.
          </p>
        </div>

        <button
          onClick={handleOpenAddModal}
          className="inline-flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2.5 rounded-xl font-bold text-xs shadow-sm transition-all cursor-pointer"
        >
          <Plus className="w-4 h-4" /> Add Subject
        </button>
      </div>

      {/* 2. Search & Quick Filters Bar */}
      <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search by course code or full name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500/20"
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
            All Courses ({subjectList.length})
          </button>

          <button
            onClick={() => setQuickFilter("LEC")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 cursor-pointer ${
              quickFilter === "LEC"
                ? "bg-blue-600 text-white shadow-sm"
                : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
            }`}
          >
            Lectures Only
          </button>

          <button
            onClick={() => setQuickFilter("LAB")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 cursor-pointer ${
              quickFilter === "LAB"
                ? "bg-purple-600 text-white shadow-sm"
                : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
            }`}
          >
            Practical Labs
          </button>

          <button
            onClick={() => setQuickFilter("GPU")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 cursor-pointer ${
              quickFilter === "GPU"
                ? "bg-amber-600 text-white shadow-sm"
                : "bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800"
            }`}
          >
            Requires GPU Rig
          </button>
        </div>
      </div>

      {/* 3. Card Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredSubjects.map((sub) => {
          const isLab = sub.is_lab || sub.slot_type === "P" || sub.lab_hours > 0;
          const totalHours = (sub.lecture_hours || 0) + (sub.tutorial_hours || 0) + (sub.lab_hours || 0);

          return (
            <div
              key={sub.id || sub.code}
              onClick={() => setSelectedSubject(sub)}
              className="group bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 hover:border-purple-400 dark:hover:border-purple-500 hover:shadow-lg transition-all cursor-pointer relative flex flex-col justify-between"
            >
              <div>
                {/* Header Tag */}
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[11px] font-bold text-purple-700 dark:text-purple-300 bg-purple-50 dark:bg-purple-950/80 px-2.5 py-0.5 rounded-lg border border-purple-200 dark:border-purple-800">
                    {sub.code}
                  </span>

                  {sub.gpu_required ? (
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/60 px-2 py-0.5 rounded-md border border-amber-200 dark:border-amber-800">
                      <Cpu className="w-3 h-3 text-amber-600" /> GPU Required
                    </span>
                  ) : (
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                      {isLab ? "Practical Lab" : "Lecture Subject"}
                    </span>
                  )}
                </div>

                <h3 className="font-bold text-slate-900 dark:text-white text-base group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors">
                  {sub.full_name}
                </h3>

                {/* Credit Breakdown Bar */}
                <div className="mt-4 flex items-center gap-2 text-xs font-bold">
                  <span className="px-2.5 py-1 bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 rounded-lg border border-blue-200 dark:border-blue-800">
                    L: {sub.lecture_hours || 0}h
                  </span>
                  <span className="px-2.5 py-1 bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 rounded-lg border border-emerald-200 dark:border-emerald-800">
                    T: {sub.tutorial_hours || 0}h
                  </span>
                  <span className="px-2.5 py-1 bg-purple-50 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 rounded-lg border border-purple-200 dark:border-purple-800">
                    P: {sub.lab_hours || 0}h
                  </span>
                  <span className="text-slate-500 dark:text-slate-400 text-xs ml-auto">
                    Total {totalHours} hrs/wk
                  </span>
                </div>
              </div>

              {/* Action Hint */}
              <div className="mt-5 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-purple-600 dark:text-purple-400 font-bold group-hover:translate-x-0.5 transition-transform">
                <span>Inspect Syllabus & Lab Rules</span>
                <span>→</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* 4. Slide-Over Curriculum Course Dossier Drawer */}
      {selectedSubject && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 backdrop-blur-sm flex justify-end animate-in fade-in">
          <div className="w-full max-w-xl bg-white dark:bg-slate-900 h-full shadow-2xl p-6 flex flex-col justify-between overflow-y-auto animate-in slide-in-from-right duration-200 border-l border-slate-200 dark:border-slate-800">
            <div className="space-y-6">

              {/* Drawer Top Header */}
              <div className="flex justify-between items-start pb-4 border-b border-slate-200 dark:border-slate-800">
                <div>
                  <span className="text-xs text-purple-600 dark:text-purple-400 font-bold">COURSE CODE {selectedSubject.code}</span>
                  <h2 className="text-xl font-bold text-slate-900 dark:text-white">{selectedSubject.full_name}</h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Department of ACSE • Academic Curriculum</p>
                </div>

                <button
                  onClick={() => setSelectedSubject(null)}
                  className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* L-T-P Hours Grid */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-4 bg-blue-50 dark:bg-blue-950/40 rounded-2xl border border-blue-100 dark:border-blue-800/60 text-center">
                  <span className="text-[11px] text-blue-700 dark:text-blue-300 font-bold uppercase">Lecture (L)</span>
                  <p className="text-xl font-extrabold text-blue-950 dark:text-blue-100 mt-1">
                    {selectedSubject.lecture_hours || 0} Hours
                  </p>
                </div>

                <div className="p-4 bg-emerald-50 dark:bg-emerald-950/40 rounded-2xl border border-emerald-100 dark:border-emerald-800/60 text-center">
                  <span className="text-[11px] text-emerald-700 dark:text-emerald-300 font-bold uppercase">Tutorial (T)</span>
                  <p className="text-xl font-extrabold text-emerald-950 dark:text-emerald-100 mt-1">
                    {selectedSubject.tutorial_hours || 0} Hours
                  </p>
                </div>

                <div className="p-4 bg-purple-50 dark:bg-purple-950/40 rounded-2xl border border-purple-100 dark:border-purple-800/60 text-center">
                  <span className="text-[11px] text-purple-700 dark:text-purple-300 font-bold uppercase">Practical (P)</span>
                  <p className="text-xl font-extrabold text-purple-950 dark:text-purple-100 mt-1">
                    {selectedSubject.lab_hours || 0} Hours
                  </p>
                </div>
              </div>

              {/* Lab Span Rules & Hardware Requirements */}
              <div className="space-y-3 p-4 bg-slate-50 dark:bg-slate-800/60 rounded-2xl border border-slate-200 dark:border-slate-800">
                <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">Constraint Solver Rules</h4>
                
                <div className="flex items-center justify-between text-xs font-semibold">
                  <span className="text-slate-500 dark:text-slate-400">Consecutive Period Block Requirement:</span>
                  <span className="text-slate-900 dark:text-white font-bold">{selectedSubject.requires_consecutive || 2} Consecutive Periods</span>
                </div>

                <div className="flex items-center justify-between text-xs font-semibold">
                  <span className="text-slate-500 dark:text-slate-400">High-GPU Compute Venue Required:</span>
                  <span className={selectedSubject.gpu_required ? "text-amber-600 dark:text-amber-400 font-bold" : "text-slate-700 dark:text-slate-300 font-bold"}>
                    {selectedSubject.gpu_required ? "Yes (AFTF-12/13/14)" : "No"}
                  </span>
                </div>
              </div>
            </div>

            {/* Footer Buttons */}
            <div className="pt-6 mt-6 border-t border-slate-200 dark:border-slate-800 flex gap-3">
              <button
                onClick={() => setSelectedSubject(null)}
                className="flex-1 py-3 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
              >
                Close
              </button>

              <button
                onClick={() => {
                  const sub = selectedSubject;
                  setSelectedSubject(null);
                  handleOpenEditModal(sub);
                }}
                className="flex-1 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-bold shadow-md cursor-pointer inline-flex items-center justify-center gap-2"
              >
                <Edit className="w-4 h-4" /> Edit Course Specs
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
                {editingSubject ? "Edit Course Curriculum" : "Add New Course"}
              </h3>
              <button onClick={() => setShowEditModal(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveForm} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Course Code</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. DS, AI, DBMS"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-xs font-bold text-slate-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Slot Type</label>
                  <select
                    value={formData.slot_type}
                    onChange={(e) => setFormData({ ...formData, slot_type: e.target.value })}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-xs font-bold text-slate-900 dark:text-white"
                  >
                    <option value="L">L (Lecture)</option>
                    <option value="P">P (Practical Lab)</option>
                    <option value="T">T (Tutorial)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Full Course Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Data Structures & Algorithms"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-xs font-bold text-slate-900 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Lecture (L)</label>
                  <input
                    type="number"
                    min={0}
                    max={6}
                    value={formData.lecture_hours}
                    onChange={(e) => setFormData({ ...formData, lecture_hours: Number(e.target.value) })}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2 text-xs font-bold text-slate-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Tutorial (T)</label>
                  <input
                    type="number"
                    min={0}
                    max={4}
                    value={formData.tutorial_hours}
                    onChange={(e) => setFormData({ ...formData, tutorial_hours: Number(e.target.value) })}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2 text-xs font-bold text-slate-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Practical (P)</label>
                  <input
                    type="number"
                    min={0}
                    max={6}
                    value={formData.lab_hours}
                    onChange={(e) => setFormData({ ...formData, lab_hours: Number(e.target.value) })}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2 text-xs font-bold text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="gpu_sub_check"
                  checked={formData.gpu_required}
                  onChange={(e) => setFormData({ ...formData, gpu_required: e.target.checked })}
                  className="rounded border-slate-300 text-purple-600 focus:ring-purple-500 cursor-pointer"
                />
                <label htmlFor="gpu_sub_check" className="text-xs font-bold text-slate-700 dark:text-slate-300 cursor-pointer">
                  Requires High-GPU Compute Rigs (Deep Learning / Vision)
                </label>
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
                  className="px-5 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-bold shadow-md"
                >
                  Save Course Specs
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
