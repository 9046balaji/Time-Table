import React from "react";
import { BookOpen, Users, Plus, Trash2, Eye } from "lucide-react";
import { CourseAssignmentInput } from "@/lib/types";

interface WizardStepCurriculumProps {
  assignments: CourseAssignmentInput[];
  setAssignments: React.Dispatch<React.SetStateAction<CourseAssignmentInput[]>>;
  facultyPool: string[];
  openFacultySchedule: (facName: string) => void;
}

export const WizardStepCurriculum: React.FC<WizardStepCurriculumProps> = ({
  assignments,
  setAssignments,
  facultyPool,
  openFacultySchedule,
}) => {
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
        subject_name: "New Department Course",
        subject_type: "L",
        faculty_name: facultyPool[0] || "Faculty Member",
        co_faculty: [],
        weekly_hours: 3,
        continuous_slots: 1,
      },
    ]);
  };

  const removeAssignmentRow = (index: number) => {
    setAssignments((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <h3 className="flex items-center gap-2 text-sm font-bold text-slate-800">
          <BookOpen className="h-4 w-4 text-blue-600" /> 2. Auto-Loaded Department Curriculum & Multi-Faculty Lab Assignments
        </h3>
        <button
          onClick={addAssignmentRow}
          className="flex items-center gap-1 rounded-xl bg-blue-50 border border-blue-200 px-3 py-1.5 text-xs font-bold text-blue-700 hover:bg-blue-100 cursor-pointer transition-all"
        >
          <Plus className="h-3.5 w-3.5" /> Add Course Row
        </button>
      </div>

      <div className="space-y-4 max-h-[480px] overflow-y-auto pr-1">
        {assignments.map((item, idx) => {
          const isLab = item.subject_type === "P";
          return (
            <div
              key={idx}
              className={`rounded-2xl border p-4 transition-all ${
                isLab
                  ? "border-purple-200 bg-purple-50/30 dark:bg-purple-950/10"
                  : "border-slate-200 bg-white"
              }`}
            >
              <div className="grid grid-cols-1 gap-3 md:grid-cols-12 items-center">
                {/* Code & Name */}
                <div className="md:col-span-3">
                  <label className="text-[10px] font-bold text-slate-400 block uppercase">Course Code & Title</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={item.subject_code}
                      onChange={(e) => updateAssignment(idx, "subject_code", e.target.value)}
                      className="w-24 rounded-lg border border-slate-300 bg-white p-1.5 text-xs font-bold text-slate-900 focus:outline-none"
                    />
                    <input
                      type="text"
                      value={item.subject_name}
                      onChange={(e) => updateAssignment(idx, "subject_name", e.target.value)}
                      className="w-full rounded-lg border border-slate-300 bg-white p-1.5 text-xs font-semibold text-slate-700 focus:outline-none"
                    />
                  </div>
                </div>

                {/* Type & Hours */}
                <div className="md:col-span-3">
                  <label className="text-[10px] font-bold text-slate-400 block uppercase">Type & Weekly Periods</label>
                  <div className="flex items-center gap-2">
                    <select
                      value={item.subject_type}
                      onChange={(e) => {
                        const newType = e.target.value as any;
                        updateAssignment(idx, "subject_type", newType);
                        if (newType === "P") {
                          updateAssignment(idx, "continuous_slots", 2);
                          updateAssignment(idx, "weekly_hours", 2);
                        }
                      }}
                      className="rounded-lg border border-slate-300 bg-white p-1.5 text-xs font-bold text-slate-900 focus:outline-none cursor-pointer"
                    >
                      <option value="L">Theory (L)</option>
                      <option value="T">Tutorial (T)</option>
                      <option value="P">Practical Lab (P)</option>
                    </select>

                    <div className="flex items-center gap-1">
                      <span className="text-xs font-bold text-slate-600">Hours:</span>
                      <input
                        type="number"
                        min="1"
                        max="6"
                        value={item.weekly_hours}
                        onChange={(e) => updateAssignment(idx, "weekly_hours", Number(e.target.value))}
                        className="w-12 rounded-lg border border-slate-300 bg-white p-1.5 text-center text-xs font-bold text-slate-900"
                      />
                    </div>
                  </div>
                </div>

                {/* Primary Faculty */}
                <div className="md:col-span-5">
                  <label className="text-[10px] font-bold text-slate-400 block uppercase">Primary Instructor</label>
                  <div className="flex items-center gap-2">
                    <select
                      value={item.faculty_name}
                      onChange={(e) => updateAssignment(idx, "faculty_name", e.target.value)}
                      className="w-full rounded-lg border border-slate-300 bg-white p-1.5 text-xs font-bold text-slate-900 focus:outline-none cursor-pointer"
                    >
                      {facultyPool.map((fName) => (
                        <option key={fName} value={fName}>
                          {fName}
                        </option>
                      ))}
                    </select>

                    <button
                      onClick={() => openFacultySchedule(item.faculty_name)}
                      className="flex items-center gap-1 rounded-lg border border-purple-200 bg-purple-50 px-2 py-1.5 text-[11px] font-bold text-purple-700 hover:bg-purple-100 cursor-pointer shrink-0"
                      title="Inspect full weekly schedule for this faculty member"
                    >
                      <Eye className="h-3.5 w-3.5" /> Inspect
                    </button>
                  </div>
                </div>

                {/* Delete button */}
                <div className="md:col-span-1 text-right">
                  <button
                    onClick={() => removeAssignmentRow(idx)}
                    className="p-1 text-slate-400 hover:text-red-600 transition-colors cursor-pointer"
                    title="Remove assignment row"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* Multi-Faculty Lab Assistants selection */}
              {isLab && (
                <div className="mt-3 border-t border-purple-100 pt-2">
                  <label className="mb-1 text-[11px] font-extrabold text-purple-900 flex items-center gap-1">
                    <Users className="h-3.5 w-3.5 text-purple-600" /> Lab Co-Instructors & Assistants (Simultaneous Teaching):
                  </label>
                  <div className="flex flex-wrap gap-1.5">
                    {facultyPool.slice(0, 15).map((fName) => {
                      if (fName === item.faculty_name) return null;
                      const isSelected = (item.co_faculty || []).includes(fName);
                      return (
                        <button
                          key={fName}
                          onClick={() => toggleCoFaculty(idx, fName)}
                          className={`rounded-full px-2.5 py-0.5 text-[11px] font-bold transition-all cursor-pointer ${
                            isSelected
                              ? "bg-purple-700 text-white shadow-sm"
                              : "bg-purple-50 text-purple-700 hover:bg-purple-100"
                          }`}
                        >
                          {isSelected ? `✓ ${fName}` : `+ ${fName}`}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
