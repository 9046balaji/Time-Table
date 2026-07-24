'use client';

import React from 'react';
import { Bot, CheckCircle2, Loader2, Sparkles, AlertCircle, RefreshCw } from 'lucide-react';
import { SolverProgressState } from '@/hooks/useSolver';

interface SolverProgressProps {
  state: SolverProgressState;
  onRunSolver: () => void;
}

export function SolverProgress({ state, onRunSolver }: SolverProgressProps) {
  const { isSolving, isComplete, hardViolations, generation, runtimeSeconds, message } = state;

  const progressPercentage = isComplete
    ? 100
    : isSolving
    ? Math.min(95, Math.max(10, Math.round(((51 - hardViolations) / 51) * 100)))
    : 0;

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-3 rounded-xl text-white ${isComplete ? 'bg-emerald-600' : isSolving ? 'bg-purple-600' : 'bg-blue-600'}`}>
            {isSolving ? <Loader2 className="w-6 h-6 animate-spin" /> : isComplete ? <CheckCircle2 className="w-6 h-6" /> : <Bot className="w-6 h-6" />}
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-lg">Google OR-Tools CP-SAT Solver Engine</h3>
            <p className="text-xs text-slate-500">Formulating 591,360 binary variables for 44 ACSE sections</p>
          </div>
        </div>

        <button
          onClick={onRunSolver}
          disabled={isSolving}
          className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm transition-all shadow-md ${
            isSolving
              ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 text-white cursor-pointer'
          }`}
        >
          {isSolving ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" /> Solving...
            </>
          ) : isComplete ? (
            <>
              <RefreshCw className="w-4 h-4" /> Re-Run Solver
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" /> Run CP-SAT Engine
            </>
          )}
        </button>
      </div>

      {/* Progress Bar & Countdown */}
      {(isSolving || isComplete) && (
        <div className="space-y-3 bg-slate-50 border border-slate-200 p-5 rounded-xl">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="text-slate-700">{message}</span>
            <span className="text-slate-500">{runtimeSeconds}s elapsed • Gen {generation}</span>
          </div>

          {/* Progress Bar */}
          <div className="w-full h-3 bg-slate-200 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${isComplete ? 'bg-emerald-500' : 'bg-gradient-to-r from-blue-600 to-purple-600'}`}
              style={{ width: `${progressPercentage}%` }}
            />
          </div>

          <div className="flex items-center justify-between pt-2">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Hard Violations:</span>
              <span className={`text-sm font-extrabold px-2.5 py-0.5 rounded-md ${hardViolations === 0 ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
                {hardViolations} Clashes
              </span>
            </div>

            {isComplete && (
              <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>100% Clash-Free Timetable Generated!</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
