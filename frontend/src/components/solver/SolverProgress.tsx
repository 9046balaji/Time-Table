'use client';

import React, { useState } from 'react';
import { Bot, CheckCircle2, Loader2, Sparkles, AlertCircle, RefreshCw, Cpu, Layers } from 'lucide-react';
import { SolverProgressState } from '@/hooks/useSolver';

interface SolverProgressProps {
  state: SolverProgressState;
  onRunSolver: (algorithm: string) => void;
}

export function SolverProgress({ state, onRunSolver }: SolverProgressProps) {
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<string>('CP-SAT');
  const { isSolving, isComplete, hardViolations, softViolations, generation, runtimeSeconds, message, error } = state;

  const progressPercentage = isComplete
    ? 100
    : isSolving
    ? Math.min(95, Math.max(10, Math.round(((51 - hardViolations) / 51) * 100)))
    : 0;

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-6 transition-colors">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className={`p-3 rounded-xl text-white shadow-md ${isComplete ? 'bg-emerald-600' : isSolving ? 'bg-purple-600 animate-pulse' : 'bg-blue-600'}`}>
            {isSolving ? <Loader2 className="w-6 h-6 animate-spin" /> : isComplete ? <CheckCircle2 className="w-6 h-6" /> : <Bot className="w-6 h-6" />}
          </div>
          <div>
            <h3 className="font-bold text-slate-900 dark:text-slate-100 text-lg leading-tight">
              Google OR-Tools CP-SAT Solver Engine
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Formulating 591,360 binary variables for 44 ACSE sections
            </p>
          </div>
        </div>

        {/* Algorithm Picker & Run Trigger */}
        <div className="flex items-center gap-2">
          <select
            value={selectedAlgorithm}
            onChange={(e) => setSelectedAlgorithm(e.target.value)}
            disabled={isSolving}
            className="bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 text-xs font-semibold px-3 py-2.5 rounded-xl focus:outline-none cursor-pointer"
          >
            <option value="CP-SAT">CP-SAT (Constraint Programming)</option>
            <option value="GeneticAlgorithm">Genetic Algorithm</option>
            <option value="Hybrid">Hybrid CP-SAT + GA</option>
          </select>

          <button
            onClick={() => onRunSolver(selectedAlgorithm)}
            disabled={isSolving}
            className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs transition-all shadow-md cursor-pointer ${
              isSolving
                ? 'bg-slate-200 dark:bg-slate-800 text-slate-400 cursor-not-allowed'
                : isComplete
                ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
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
      </div>

      {/* Progress Bar & Real-time Live State */}
      {(isSolving || isComplete) && (
        <div className="space-y-3 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 p-5 rounded-xl">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="text-slate-700 dark:text-slate-200">{message}</span>
            <span className="text-slate-500 dark:text-slate-400 font-mono">
              {runtimeSeconds}s elapsed • Iteration {generation}
            </span>
          </div>

          {/* Progress Bar */}
          <div className="w-full h-3 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${isComplete ? 'bg-emerald-500' : 'bg-gradient-to-r from-blue-600 to-purple-600'}`}
              style={{ width: `${progressPercentage}%` }}
            />
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-2">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5">
                <span className="text-xs text-slate-500 dark:text-slate-400">Hard Violations:</span>
                <span className={`text-xs font-extrabold px-2.5 py-0.5 rounded-md ${hardViolations === 0 ? 'bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300' : 'bg-red-100 dark:bg-red-950/80 text-red-800 dark:text-red-300'}`}>
                  {hardViolations} Clashes
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-xs text-slate-500 dark:text-slate-400">Soft Violations:</span>
                <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-amber-100 dark:bg-amber-950/80 text-amber-800 dark:text-amber-300">
                  {softViolations} Penalty
                </span>
              </div>
            </div>

            {isComplete && (
              <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/60 px-3 py-1 rounded-full border border-emerald-200 dark:border-emerald-800">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                <span>100% Clash-Free Timetable Generated!</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error Message Display */}
      {error && (
        <div className="flex items-center gap-2 p-3 text-xs font-semibold text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-800 rounded-xl">
          <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
