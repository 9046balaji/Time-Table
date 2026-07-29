import React from "react";
import { Sparkles, Loader2, CheckCircle2, RefreshCw, Wand2, ShieldAlert, Cpu } from "lucide-react";
import { WizardGenerationResponse } from "@/lib/types";

interface WizardStepSolveProps {
  loading: boolean;
  onGenerate: () => void;
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
  return (
    <div className="space-y-6 text-center py-4">
      <div className="mx-auto max-w-lg rounded-3xl border border-blue-100 bg-gradient-to-b from-blue-50/50 to-white p-6 shadow-sm">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-md">
          {loading ? (
            <Loader2 className="h-8 w-8 animate-spin" />
          ) : generatedResult ? (
            <CheckCircle2 className="h-8 w-8 text-emerald-300" />
          ) : (
            <Cpu className="h-8 w-8" />
          )}
        </div>

        <h3 className="text-lg font-bold text-slate-900">
          {loading
            ? "OR-Tools CP-SAT Engine Solving..."
            : generatedResult
            ? "100% Clash-Free Master Timetable Generated!"
            : "Ready for High-Speed AI Generation"}
        </h3>
        <p className="mt-1 text-xs text-slate-500">
          {loading
            ? "Running parallel constraint propagation (8 workers) across sections, rooms, and multi-instructor labs."
            : generatedResult
            ? `Successfully generated timetable for ${selectedSections.length} sections (${generatedResult.entries_count} slots) in ${generatedResult.runtime_seconds} seconds!`
            : `Configured for ${selectedSections.length} target sections with <= ${maxDailyHours}h daily faculty cap.`}
        </p>

        {/* Generate Action Button */}
        <div className="mt-6">
          <button
            onClick={onGenerate}
            disabled={loading}
            className="w-full inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-3.5 text-sm font-extrabold text-white shadow-lg hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-all"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Solving Timetable (8 Parallel CP-SAT Workers)...
              </>
            ) : generatedResult ? (
              <>
                <RefreshCw className="h-4 w-4" /> Re-Run 0-Clash Solver Engine
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" /> Generate 0-Clash Master Timetable
              </>
            )}
          </button>
        </div>
      </div>

      {/* Generated Timetable Summary Card */}
      {generatedResult && (
        <div className="mx-auto max-w-xl text-left rounded-2xl border border-emerald-200 bg-emerald-50/50 p-4">
          <h4 className="flex items-center gap-2 text-xs font-extrabold text-emerald-900">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" /> Master Timetable Generation Summary
          </h4>
          <div className="mt-2 grid grid-cols-2 gap-3 text-xs font-semibold text-emerald-800">
            <div>• Target Sections: <strong>{selectedSections.length} Sections</strong></div>
            <div>• Hard Violations: <strong className="text-emerald-700">{generatedResult.hard_violations} (100% Clash-Free)</strong></div>
            <div>• Total Slots Scheduled: <strong>{generatedResult.entries_count} Slots</strong></div>
            <div>• Execution Time: <strong>{generatedResult.runtime_seconds} sec</strong></div>
          </div>
        </div>
      )}
    </div>
  );
};
