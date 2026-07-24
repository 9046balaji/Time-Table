"use client";

import React, { useState } from "react";
import { Sparkles, CheckCircle2, ChevronRight, ChevronLeft, Building2, BookOpen, Users, Clock, Loader2, AlertCircle, Plus, X, ShieldAlert } from "lucide-react";
import { CourseAssignmentInput, TimetableGenerationRequest, WizardGenerationResponse } from "@/lib/types";
import { timetableApi } from "@/lib/api";

interface ScheduleSetupWizardProps {
  onSuccess?: (response: WizardGenerationResponse) => void;
}

const FACULTY_POOL = [
  "Dr. S. Srikantha Reddy",
  "DR. ANKAMMA RAO MALLELA",
  "DR. P. Kalpana",
  "Dr. B. Sudha Rani",
  "Ms. P. Seetha Lakshmi",
  "Ms. G. Mahalakshmi",
  "P. Girija",
  "K. Nikhitha",
  "Mr. Mahendra Varma",
  "V. Amarnath",
  "Dr. Eva Patel",
  "Dr. Chennapradaga Amarendra",
  "Mr. T. Krishna",
  "A. Hruday Raj",
  "Dr. M. Vasudeva",
  "Dr. K. Srinivas",
  "Dr. A.V. Nageswara Rao",
];

const YEAR_CURRICULA: Record<string, CourseAssignmentInput[]> = {
  "II Year": [
    {
      subject_code: "DS",
      subject_name: "Data Structures",
      subject_type: "L",
      faculty_name: "Dr. S. Srikantha Reddy",
      co_faculty: [],
      weekly_hours: 3,
      continuous_slots: 1,
    },
    {
      subject_code: "DS(P)",
      subject_name: "Data Structures Lab",
      subject_type: "P",
      faculty_name: "Dr. S. Srikantha Reddy",
      co_faculty: ["P. Girija", "K. Nikhitha", "Mr. Mahendra Varma"],
      weekly_hours: 2,
      continuous_slots: 2,
    },
    {
      subject_code: "AI",
      subject_name: "Artificial Intelligence",
      subject_type: "L",
      faculty_name: "Dr. B. Sudha Rani",
      co_faculty: [],
      weekly_hours: 3,
      continuous_slots: 1,
    },
    {
      subject_code: "AI(P)",
      subject_name: "AI Lab",
      subject_type: "P",
      faculty_name: "Dr. B. Sudha Rani",
      co_faculty: ["V. Amarnath"],
      weekly_hours: 2,
      continuous_slots: 2,
    },
    {
      subject_code: "DBMS",
      subject_name: "Database Management Systems",
      subject_type: "L",
      faculty_name: "Ms. P. Seetha Lakshmi",
      co_faculty: [],
      weekly_hours: 3,
      continuous_slots: 1,
    },
    {
      subject_code: "SFCDS",
      subject_name: "Statistical Foundations for Computing",
      subject_type: "L",
      faculty_name: "DR. P. Kalpana",
      co_faculty: [],
      weekly_hours: 3,
      continuous_slots: 1,
    },
  ],
  "III Year": [
    {
      subject_code: "DL(P)",
      subject_name: "Deep Learning Practical Lab",
      subject_type: "P",
      faculty_name: "Dr. Eva Patel",
      co_faculty: ["V. Amarnath", "P. Girija"],
      weekly_hours: 2,
      continuous_slots: 2,
    },
    {
      subject_code: "WT",
      subject_name: "Web Technologies",
      subject_type: "L",
      faculty_name: "Dr. Chennapradaga Amarendra",
      co_faculty: [],
      weekly_hours: 3,
      continuous_slots: 1,
    },
    {
      subject_code: "CV(P)",
      subject_name: "Computer Vision Lab",
      subject_type: "P",
      faculty_name: "Dr. Eva Patel",
      co_faculty: ["K. Nikhitha"],
      weekly_hours: 2,
      continuous_slots: 2,
    },
    {
      subject_code: "MINORHONOR",
      subject_name: "Synchronized Minors / Honors",
      subject_type: "P",
      faculty_name: "A. Hruday Raj",
      co_faculty: ["Mr. Mahendra Varma"],
      weekly_hours: 2,
      continuous_slots: 2,
    },
  ],
  "IV Year": [
    {
      subject_code: "CNS(P)",
      subject_name: "Cryptography & Network Security Lab",
      subject_type: "P",
      faculty_name: "Dr. M. Vasudeva",
      co_faculty: ["P. Girija"],
      weekly_hours: 2,
      continuous_slots: 2,
    },
    {
      subject_code: "GENAI(P)",
      subject_name: "Generative AI Practical Lab",
      subject_type: "P",
      faculty_name: "Dr. Eva Patel",
      co_faculty: ["V. Amarnath", "Mr. Mahendra Varma"],
      weekly_hours: 2,
      continuous_slots: 2,
    },
    {
      subject_code: "IOT",
      subject_name: "Internet of Things",
      subject_type: "L",
      faculty_name: "Dr. A.V. Nageswara Rao",
      co_faculty: [],
      weekly_hours: 3,
      continuous_slots: 1,
    },
  ],
};

const YEAR_SECTIONS: Record<string, string[]> = {
  "II Year": ["II AIML-A", "II AIML-B", "II AIML-C", "II CS-A", "II DS-A"],
  "III Year": ["III AIML-A", "III AIML-B", "III AIML-C", "III CS"],
  "IV Year": ["IV AIML-A", "IV AIML-B", "IV CS"],
};

export const ScheduleSetupWizard: React.FC<ScheduleSetupWizardProps> = ({ onSuccess }) => {
  const [step, setStep] = useState<number>(1);
  const [branch, setBranch] = useState<string>("AIML");
  const [yearLevel, setYearLevel] = useState<string>("II Year");
  const [selectedSections, setSelectedSections] = useState<string[]>(["II AIML-A", "II AIML-B"]);
  const [preferredBlock, setPreferredBlock] = useState<string>("Block-VI (601-619)");
  const [maxDailyHours, setMaxDailyHours] = useState<number>(5);
  const [assignments, setAssignments] = useState<CourseAssignmentInput[]>(YEAR_CURRICULA["II Year"]);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleYearChange = (newYear: string) => {
    setYearLevel(newYear);
    const secs = YEAR_SECTIONS[newYear] || [];
    setSelectedSections(secs.slice(0, 2));
    setAssignments(YEAR_CURRICULA[newYear] || YEAR_CURRICULA["II Year"]);
  };

  const toggleSection = (sec: string) => {
    setSelectedSections((prev) =>
      prev.includes(sec) ? prev.filter((s) => s !== sec) : [...prev, sec]
    );
  };

  const updateAssignment = (index: number, field: keyof CourseAssignmentInput, value: any) => {
    setAssignments((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], [field]: value };
      return copy;
    });
  };

  const toggleCoFaculty = (index: number, facName: string) => {
    setAssignments((prev) => {
      const copy = [...prev];
      const currentCo = copy[index].co_faculty || [];
      if (currentCo.includes(facName)) {
        copy[index] = { ...copy[index], co_faculty: currentCo.filter((f) => f !== facName) };
      } else {
        copy[index] = { ...copy[index], co_faculty: [...currentCo, facName] };
      }
      return copy;
    });
  };

  const addAssignmentRow = () => {
    setAssignments((prev) => [
      ...prev,
      {
        subject_code: "NEW_SUBJ",
        subject_name: "New Course",
        subject_type: "L",
        faculty_name: FACULTY_POOL[0],
        co_faculty: [],
        weekly_hours: 3,
        continuous_slots: 1,
      },
    ]);
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);

    const payload: TimetableGenerationRequest = {
      branch,
      year_level: yearLevel,
      sections: selectedSections,
      preferred_block: preferredBlock,
      max_daily_teaching_hours: maxDailyHours,
      max_classes_per_teacher_per_day: maxDailyHours,
      assignments,
    };

    try {
      const res = await timetableApi.generateFromWizard(payload);
      if (res.data.status === "INFEASIBLE") {
        setError("Generation Infeasible: Over-subscribed period quotas or tight teacher daily caps. Try increasing max daily teacher cap or selecting additional venue blocks.");
      } else {
        onSuccess?.(res.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to generate timetable. Please check backend solver server.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      {/* Wizard Header */}
      <div className="mb-6 border-b border-slate-200 pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-600 p-3 text-white shadow-sm">
              <Sparkles className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">Advanced AI Timetable Rule Configurator</h2>
              <p className="text-xs text-slate-500">Configure multi-faculty lab mappings, daily teacher class limits, and continuous period locks.</p>
            </div>
          </div>
          <span className="rounded-full border border-blue-200 bg-blue-50 px-3.5 py-1 text-xs font-bold text-blue-700">
            Step {step} of 4
          </span>
        </div>

        {/* Step Navigation Tabs */}
        <div className="mt-4 grid grid-cols-4 gap-2 text-center text-xs font-bold">
          <div className={`rounded-lg p-2.5 transition-all ${step >= 1 ? "bg-blue-700 text-white shadow-sm" : "bg-slate-100 text-slate-400"}`}>
            1. Scope & Teacher Caps
          </div>
          <div className={`rounded-lg p-2.5 transition-all ${step >= 2 ? "bg-blue-700 text-white shadow-sm" : "bg-slate-100 text-slate-400"}`}>
            2. Multi-Faculty & Labs
          </div>
          <div className={`rounded-lg p-2.5 transition-all ${step >= 3 ? "bg-blue-700 text-white shadow-sm" : "bg-slate-100 text-slate-400"}`}>
            3. Venue Matrix & Locks
          </div>
          <div className={`rounded-lg p-2.5 transition-all ${step >= 4 ? "bg-blue-700 text-white shadow-sm" : "bg-slate-100 text-slate-400"}`}>
            4. 0-Clash AI Solve
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-4 flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-xs font-semibold text-red-700">
          <AlertCircle className="h-4 w-4 shrink-0 text-red-600" />
          <span>{error}</span>
        </div>
      )}

      {/* STEP 1: Academic Scope & Daily Faculty Limits */}
      {step === 1 && (
        <div className="space-y-6">
          <h3 className="flex items-center gap-2 text-sm font-bold text-slate-800">
            <Users className="h-4 w-4 text-blue-600" /> Academic Scope & Faculty Workload Cap
          </h3>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">Department Branch:</label>
              <select
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-slate-50 p-2.5 text-xs font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="AIML">Artificial Intelligence & Machine Learning (AIML)</option>
                <option value="CS">Computer Science (CS)</option>
                <option value="DS">Data Science (DS)</option>
                <option value="CSBS">Computer Science & Business Systems (CSBS)</option>
                <option value="IOT">Internet of Things (IOT)</option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">Academic Year:</label>
              <select
                value={yearLevel}
                onChange={(e) => handleYearChange(e.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-slate-50 p-2.5 text-xs font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="II Year">II Year (Sem I)</option>
                <option value="III Year">III Year (Sem I)</option>
                <option value="IV Year">IV Year (Sem I)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="mb-2 block text-xs font-bold text-slate-700">Target Student Sections:</label>
            <div className="flex flex-wrap gap-2.5">
              {(YEAR_SECTIONS[yearLevel] || ["II AIML-A", "II AIML-B"]).map((sec) => {
                const isSelected = selectedSections.includes(sec);
                return (
                  <button
                    key={sec}
                    type="button"
                    onClick={() => toggleSection(sec)}
                    className={`cursor-pointer rounded-xl border px-4 py-2 text-xs font-bold transition-all ${
                      isSelected
                        ? "border-blue-600 bg-blue-600 text-white shadow-sm"
                        : "border-slate-300 bg-slate-50 text-slate-700 hover:bg-slate-100"
                    }`}
                  >
                    {isSelected ? "✓ " : "+ "} {sec}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Teacher Daily Max Cap Control */}
          <div className="rounded-xl border border-blue-100 bg-blue-50/60 p-4">
            <div className="mb-2 flex items-center justify-between">
              <label className="block text-xs font-bold text-slate-900">
                Teacher Max Classes Limit: <span className="font-extrabold text-blue-700 text-sm">{maxDailyHours} Classes / Day</span>
              </label>
              <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-[10px] font-bold text-blue-800">
                Burnout Protection Rule
              </span>
            </div>
            <input
              type="range"
              min={3}
              max={7}
              value={maxDailyHours}
              onChange={(e) => setMaxDailyHours(Number(e.target.value))}
              className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-slate-200 accent-blue-700"
            />
            <div className="mt-1 flex justify-between font-mono text-[10px] text-slate-500">
              <span>3 Classes/Day (Light)</span>
              <span className="font-bold text-blue-700">5 Classes/Day (Recommended)</span>
              <span>7 Classes/Day (Max Cap)</span>
            </div>
          </div>
        </div>
      )}

      {/* STEP 2: Subject & Multi-Faculty Mapping Table */}
      {step === 2 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-sm font-bold text-slate-800">
              <BookOpen className="h-4 w-4 text-purple-600" /> Subject & Multi-Instructor Mappings
            </h3>
            <button
              onClick={addAssignmentRow}
              className="rounded-lg border border-slate-300 bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-800 transition-colors hover:bg-slate-200"
            >
              + Add Subject Row
            </button>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-800 text-white font-bold">
                <tr>
                  <th className="p-3">Subject</th>
                  <th className="p-3">Type & Continuous Slots</th>
                  <th className="p-3">Weekly Hours</th>
                  <th className="p-3">Primary Faculty</th>
                  <th className="p-3">Co-Instructors / Lab Assistants (Multi-Faculty)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {assignments.map((sub, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                    <td className="p-3">
                      <div className="space-y-1">
                        <input
                          type="text"
                          value={sub.subject_code}
                          onChange={(e) => updateAssignment(idx, "subject_code", e.target.value)}
                          className="w-24 rounded border border-slate-300 bg-slate-50 p-1 font-bold text-blue-700 focus:outline-none"
                        />
                        <input
                          type="text"
                          value={sub.subject_name}
                          onChange={(e) => updateAssignment(idx, "subject_name", e.target.value)}
                          className="w-full rounded border border-slate-300 bg-slate-50 p-1 font-medium text-slate-800 focus:outline-none"
                        />
                      </div>
                    </td>
                    <td className="p-3">
                      <div className="space-y-1">
                        <select
                          value={sub.subject_type}
                          onChange={(e) => {
                            const newType = e.target.value as "L" | "P" | "T";
                            updateAssignment(idx, "subject_type", newType);
                            if (newType === "P") {
                              updateAssignment(idx, "continuous_slots", 2);
                            } else {
                              updateAssignment(idx, "continuous_slots", 1);
                            }
                          }}
                          className="rounded border border-slate-300 bg-slate-50 p-1 font-bold focus:outline-none"
                        >
                          <option value="L">Theory (L)</option>
                          <option value="P">Practical Lab (P)</option>
                          <option value="T">Tutorial (T)</option>
                        </select>

                        {sub.subject_type === "P" && (
                          <div className="mt-1">
                            <label className="block text-[10px] font-semibold text-purple-700">Consecutive Slots:</label>
                            <select
                              value={sub.continuous_slots || 2}
                              onChange={(e) => updateAssignment(idx, "continuous_slots", Number(e.target.value))}
                              className="rounded border border-purple-200 bg-purple-50 p-1 text-[11px] font-bold text-purple-900 focus:outline-none"
                            >
                              <option value={2}>2 Consecutive Periods</option>
                              <option value={3}>3 Consecutive Periods</option>
                            </select>
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="p-3">
                      <input
                        type="number"
                        min={1}
                        max={8}
                        value={sub.weekly_hours}
                        onChange={(e) => updateAssignment(idx, "weekly_hours", parseInt(e.target.value) || 1)}
                        className="w-16 rounded border border-slate-300 bg-slate-50 p-1 text-center font-mono font-bold focus:outline-none"
                      />
                      <span className="ml-1 text-[10px] text-slate-500 font-mono">hrs/wk</span>
                    </td>
                    <td className="p-3">
                      <select
                        value={sub.faculty_name}
                        onChange={(e) => updateAssignment(idx, "faculty_name", e.target.value)}
                        className="w-full rounded border border-slate-300 bg-slate-50 p-1 font-semibold text-slate-800 focus:outline-none"
                      >
                        {FACULTY_POOL.map((fac) => (
                          <option key={fac} value={fac}>
                            {fac}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="p-3">
                      <div className="space-y-1.5">
                        <div className="flex flex-wrap gap-1">
                          {(sub.co_faculty || []).map((co, cIdx) => (
                            <span
                              key={cIdx}
                              className="inline-flex items-center gap-1 rounded border border-purple-200 bg-purple-50 px-2 py-0.5 text-[10px] font-semibold text-purple-800"
                            >
                              {co}
                              <button
                                type="button"
                                onClick={() => toggleCoFaculty(idx, co)}
                                className="text-purple-600 hover:text-purple-900"
                              >
                                ×
                              </button>
                            </span>
                          ))}
                          {(sub.co_faculty || []).length === 0 && (
                            <span className="text-[11px] italic text-slate-400">Single Instructor</span>
                          )}
                        </div>

                        {/* Co-Faculty Quick Add Dropdown */}
                        <select
                          value=""
                          onChange={(e) => {
                            if (e.target.value) {
                              toggleCoFaculty(idx, e.target.value);
                            }
                          }}
                          className="w-full rounded border border-slate-200 bg-slate-50 p-1 text-[10px] text-slate-600 focus:outline-none"
                        >
                          <option value="">+ Add Co-Instructor / Lab Assistant...</option>
                          {FACULTY_POOL.filter(f => f !== sub.faculty_name && !(sub.co_faculty || []).includes(f)).map((fac) => (
                            <option key={fac} value={fac}>
                              + {fac}
                            </option>
                          ))}
                        </select>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* STEP 3: Venue Preferences & Lock Matrix */}
      {step === 3 && (
        <div className="space-y-5">
          <h3 className="flex items-center gap-2 text-sm font-bold text-slate-800">
            <Building2 className="h-4 w-4 text-emerald-600" /> Venue Matrix & Student Compactness
          </h3>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">Primary Building Block:</label>
              <select
                value={preferredBlock}
                onChange={(e) => setPreferredBlock(e.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-slate-50 p-2.5 text-xs font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="Block-VI (601-619)">Block-VI (Classrooms 601-619 & Computer Labs 604-606)</option>
                <option value="AFTF High-GPU Labs">AFTF High-GPU Labs (AFTF-12, AFTF-13, AFTF-14)</option>
                <option value="Block-V (514-A, 518)">Block-V (Rooms 514-A, 518)</option>
              </select>
            </div>

            <div className="rounded-xl border border-emerald-100 bg-emerald-50/50 p-3.5">
              <span className="block text-xs font-bold text-emerald-900">Student Daily Schedule Compactness Guard</span>
              <p className="mt-1 text-[11px] text-emerald-700">
                Automatically prevents idle gap hours between morning and afternoon lectures for all selected sections.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* STEP 4: AI Solve Trigger & Review */}
      {step === 4 && (
        <div className="space-y-5">
          <h3 className="flex items-center gap-2 text-sm font-bold text-slate-800">
            <Sparkles className="h-4 w-4 text-amber-500" /> Review Configured Rules & Trigger AI Solve Engine
          </h3>

          <div className="space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-4 font-mono text-xs">
            <div><strong>Scope:</strong> {branch} ({yearLevel}) — {selectedSections.join(", ")}</div>
            <div><strong>Teacher Daily Workload Limit:</strong> Max {maxDailyHours} classes/day per faculty</div>
            <div><strong>Configured Subjects:</strong> {assignments.length} Total ({assignments.filter(a => a.subject_type === 'P').length} Practical Labs)</div>
            <div>
              <strong>Multi-Faculty Lab Sessions:</strong>{" "}
              {assignments.filter(a => (a.co_faculty || []).length > 0).map(a => `${a.subject_code} (${1 + (a.co_faculty?.length || 0)} instructors)`).join(", ") || "None"}
            </div>
          </div>

          <div className="pt-2 text-center">
            <button
              onClick={handleGenerate}
              disabled={loading}
              className="inline-flex cursor-pointer items-center gap-2 rounded-xl bg-emerald-600 px-8 py-3.5 text-xs font-bold text-white shadow-md transition-all hover:bg-emerald-700 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" /> CP-SAT Solver Generating 0-Clash Timetable...
                </>
              ) : (
                <>
                  <Sparkles className="h-5 w-5" /> ⚡ Generate 0-Clash AI Timetable Now
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Footer Navigation */}
      <div className="mt-8 flex items-center justify-between border-t border-slate-200 pt-4">
        <button
          onClick={() => setStep((s) => Math.max(1, s - 1))}
          disabled={step === 1 || loading}
          className="inline-flex cursor-pointer items-center gap-1.5 rounded-xl bg-slate-100 px-4 py-2 text-xs font-bold text-slate-700 transition-colors hover:bg-slate-200 disabled:opacity-40"
        >
          <ChevronLeft className="h-4 w-4" /> Back
        </button>

        {step < 4 ? (
          <button
            onClick={() => setStep((s) => Math.min(4, s + 1))}
            className="inline-flex cursor-pointer items-center gap-1.5 rounded-xl bg-blue-700 px-5 py-2 text-xs font-bold text-white shadow-sm transition-colors hover:bg-blue-800"
          >
            Next Step <ChevronRight className="h-4 w-4" />
          </button>
        ) : null}
      </div>
    </div>
  );
};
