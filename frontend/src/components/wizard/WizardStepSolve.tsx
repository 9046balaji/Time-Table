"use client";

import React, { useState } from "react";
import { Sparkles, Loader2, CheckCircle2, RefreshCw, Wand2, ShieldAlert, Cpu, Sliders, Zap } from "lucide-react";
import { WizardGenerationResponse } from "@/lib/types";

interface WizardStepSolveProps {
  loading: boolean;
  onGenerate: (algorithm?: string, timeout?: number) => void;
  generatedResult: WizardGenerationResponse | null;
  selectedSections: string[];
  maxDailyHours: number;
}

export const WizardStepSolve: React.FC<WizardStepSolveProps> = ({
  loading,
  onGenerate,
  generatedResult,
  selectedSections,
  maxDailyHours,
}) => {
  const [algorithm, setAlgorithm] = useState<string>("CP-SAT");
  const [timeoutSeconds, setTimeoutSeconds] = useState<number>(120);

  return (
    <div className="space-y-6 text-center py-4">
      {/* Solver Engine Config Card */}
      <div className="mx-auto max-w-xl rounded-3xl border border-blue-100 dark:border-slate-800 bg-gradient-to-b from-blue-50/50 to-white dark:from-slate-900 dark:to-slate-900 p-6 shadow-sm space-y-5">
        <div className="mx-auto mb-2 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-md">
          {loading ? (
            <Loader2 className="h-8 w-8 animate-spin" />
          ) : generatedResult ? (
            <CheckCircle2 className="h-8 w-8 text-emerald-300" />
          ) : (
            <Cpu className="h-8 w-8" />
          )}
        </div>

        <div>
          <h3 className="text-lg font-black text-slate-900 dark:text-white">
            {loading
              ? `${algorithm} Optimization Engine Solving...`
              : generatedResult
              ? "100% Clash-Free Master Timetable Generated!"
              : "Ready for High-Speed AI Generation"}
          </h3>
          <p className="mt-1 text-xs font-medium text-slate-500">
            {loading
              ? `Running parallel constraint propagation across ${selectedSections.length} sections, rooms, and multi-instructor lab teams.`
              : generatedResult
              ? `Successfully generated timetable for ${selectedSections.length} sections (${generatedResult.entries_count} slots) in ${generatedResult.runtime_seconds} seconds!`
              : `Configured for ${selectedSections.length} target sections with <= ${maxDailyHours}h daily faculty cap.`}
          </p>
        </div>

        {/* Algorithm & Timeout Controls */}
        {!loading && !generatedResult && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left bg-slate-50 dark:bg-slate-800/60 p-4 rounded-2xl border border-slate-200 dark:border-slate-700 text-xs">
            <div>
              <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Solver Algorithm:</label>
              <select
                value={algorithm}
                onChange={(e) => setAlgorithm(e.target.value)}
                className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl font-bold text-slate-900 dark:text-white"
              >
                <option value="CP-SAT">OR-Tools CP-SAT (Recommended)</option>
                <option value="GA">Genetic Algorithm (Population Search)</option>
                <option value="Hybrid">Hybrid CP-SAT + GA (Refinement)</option>
              </select>
            </div>

            <div>
              <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                Max Timeout: <span className="text-blue-600">{timeoutSeconds}s</span>
              </label>
              <input
                type="range"
                min={15}
                max={300}
                step={15}
                value={timeoutSeconds}
                onChange={(e) => setTimeoutSeconds(Number(e.target.value))}
                className="w-full mt-2 accent-blue-600 cursor-pointer"
              />
            </div>
          </div>
        )}

        {/* Generate Action Button */}
        <div>
          <button
            onClick={() => onGenerate(algorithm, timeoutSeconds)}
            disabled={loading}
            className="w-full inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-3.5 text-xs font-black text-white shadow-lg hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-all uppercase tracking-wider"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Solving Timetable ({algorithm} 8 Parallel Workers)...
              </>
            ) : generatedResult ? (
              <>
                <RefreshCw className="h-4 w-4" />
                Re-Run AI Solver Engine
              </>
            ) : (
              <>
                <Zap className="h-4 w-4 text-amber-300" />
                Execute AI Solver Engine ({selectedSections.length} Sections)
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
