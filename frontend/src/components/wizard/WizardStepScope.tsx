import React from "react";
import { Users, Building2, Layers, CheckSquare, Square } from "lucide-react";

interface WizardStepScopeProps {
  branch: string;
  setBranch: (v: string) => void;
  yearLevel: string;
  setYearLevel: (v: string) => void;
  selectedSections: string[];
  setSelectedSections: React.Dispatch<React.SetStateAction<string[]>>;
  availableSections: string[];
  preferredBlock: string;
  setPreferredBlock: (v: string) => void;
  maxDailyHours: number;
  setMaxDailyHours: (v: number) => void;
}

export const WizardStepScope: React.FC<WizardStepScopeProps> = ({
  branch,
  setBranch,
  yearLevel,
  setYearLevel,
  selectedSections,
  setSelectedSections,
  availableSections,
  preferredBlock,
  setPreferredBlock,
  maxDailyHours,
  setMaxDailyHours,
}) => {
  const toggleSection = (sec: string) => {
    setSelectedSections((prev) =>
      prev.includes(sec) ? prev.filter((s) => s !== sec) : [...prev, sec]
    );
  };

  const selectAllSections = () => {
    setSelectedSections(availableSections);
  };

  const clearAllSections = () => {
    setSelectedSections([]);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <h3 className="flex items-center gap-2 text-sm font-bold text-slate-800">
          <Users className="h-4 w-4 text-blue-600" /> 1. Scope, Cohort & Faculty Workload Limits
        </h3>
        <span className="text-xs font-semibold text-slate-500">
          {selectedSections.length} of {availableSections.length} Sections Selected
        </span>
      </div>

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
            <option value="ALL">Entire ACSE Department (All Branches & Years)</option>
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-bold text-slate-700">Academic Year / Cohort Scope:</label>
          <select
            value={yearLevel}
            onChange={(e) => setYearLevel(e.target.value)}
            className="w-full rounded-xl border border-slate-300 bg-slate-50 p-2.5 text-xs font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="Entire Department">⚡ Entire Department (All 44 Sections Simultaneously)</option>
            <option value="II Year">B.Tech II Year (12 AIML + CS, DS, CSBS, IOT)</option>
            <option value="III Year">B.Tech III Year (7 AIML + CS, DS, CSBS, IOT)</option>
            <option value="IV Year">B.Tech IV Year (5 AIML + CS, DS, CSBS)</option>
          </select>
        </div>
      </div>

      {/* Target Sections Selection */}
      <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-4">
        <div className="mb-3 flex items-center justify-between">
          <label className="text-xs font-bold text-slate-800">Target Section Cohorts:</label>
          <div className="flex items-center gap-2">
            <button
              onClick={selectAllSections}
              className="text-[11px] font-bold text-blue-700 hover:underline cursor-pointer"
            >
              Select All ({availableSections.length})
            </button>
            <span className="text-slate-300">|</span>
            <button
              onClick={clearAllSections}
              className="text-[11px] font-bold text-slate-500 hover:underline cursor-pointer"
            >
              Clear All
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
          {availableSections.map((sec) => {
            const isSelected = selectedSections.includes(sec);
            return (
              <button
                key={sec}
                onClick={() => toggleSection(sec)}
                className={`flex items-center gap-2 rounded-lg border p-2 text-left text-xs font-bold transition-all cursor-pointer ${
                  isSelected
                    ? "border-blue-600 bg-blue-50 text-blue-900 shadow-sm"
                    : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                }`}
              >
                {isSelected ? (
                  <CheckSquare className="h-3.5 w-3.5 shrink-0 text-blue-600" />
                ) : (
                  <Square className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                )}
                <span className="truncate">{sec}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Constraints & Preferences */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <label className="mb-1.5 flex items-center gap-2 text-xs font-bold text-slate-800">
            <Building2 className="h-4 w-4 text-purple-600" /> Primary Building / Venue Block:
          </label>
          <select
            value={preferredBlock}
            onChange={(e) => setPreferredBlock(e.target.value)}
            className="w-full rounded-xl border border-slate-300 bg-slate-50 p-2.5 text-xs font-bold text-slate-900 focus:outline-none"
          >
            <option value="Block-VI (601-619)">Aryabhatta Bhavan (Block-VI Classrooms 601-619)</option>
            <option value="AFTF Floor (GPU Labs)">AFTF Series High-GPU Labs (AFTF-12, AFTF-13, AFTF-14)</option>
            <option value="Divisional Block (514-518)">U-Block 5th Floor (514-A, 514-B, 518)</option>
          </select>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <label className="mb-1.5 flex items-center justify-between text-xs font-bold text-slate-800">
            <span className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-emerald-600" /> Daily Faculty Workload Limit:
            </span>
            <span className="rounded-md bg-emerald-100 px-2 py-0.5 text-emerald-800 font-extrabold">{maxDailyHours} Hours / Day</span>
          </label>
          <input
            type="range"
            min="3"
            max="6"
            step="1"
            value={maxDailyHours}
            onChange={(e) => setMaxDailyHours(Number(e.target.value))}
            className="w-full cursor-pointer accent-emerald-600"
          />
          <div className="mt-1 flex justify-between text-[10px] font-semibold text-slate-400">
            <span>3 Hours (Strict)</span>
            <span>4 Hours (AICTE Standard)</span>
            <span>6 Hours (Max)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
