"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Sparkles, Cpu, ShieldCheck, Zap, Layers, ArrowRight, CheckCircle2, Clock, Calendar } from "lucide-react";
import { ScheduleSetupWizard } from "@/components/wizard/ScheduleSetupWizard";
import { WizardGenerationResponse } from "@/lib/types";

export default function AISchedulerPage() {
  const router = useRouter();
  const [lastGenerated, setLastGenerated] = useState<WizardGenerationResponse | null>(null);

  const handleWizardSuccess = (response: WizardGenerationResponse) => {
    setLastGenerated(response);
  };

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Executive Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 rounded-2xl p-6 text-white shadow-xl border border-blue-800/50">
        <div className="space-y-2">
          <div className="flex items-center gap-2.5">
            <span className="px-2.5 py-1 rounded-full bg-blue-500/20 border border-blue-400/30 text-blue-300 text-xs font-bold flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
              AI & Mathematical Solver Engine
            </span>
            <span className="px-2.5 py-1 rounded-full bg-emerald-500/20 border border-emerald-400/30 text-emerald-300 text-xs font-bold flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              CP-SAT Active
            </span>
          </div>

          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight">
            Autonomous AI Timetable Generator
          </h1>
          <p className="text-sm text-slate-300 max-w-2xl">
            Generate 0-clash, constraint-optimized master timetables across all 44 sections, 80 faculty, and 35 rooms using OR-Tools CP-SAT math engine.
          </p>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center gap-3 shrink-0">
          <Link
            href="/schedule"
            className="px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-bold border border-white/15 transition-all flex items-center gap-2 backdrop-blur-md cursor-pointer"
          >
            <Calendar className="w-4 h-4 text-blue-300" /> View Timetable Grid
          </Link>
        </div>
      </div>

      {/* KPI Feature Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm flex items-center gap-3">
          <div className="p-3 bg-blue-50 dark:bg-blue-950/60 rounded-xl text-blue-600 dark:text-blue-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Hard Constraints</div>
            <div className="text-sm font-bold text-slate-900 dark:text-white">100% Enforced (0 Clashes)</div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm flex items-center gap-3">
          <div className="p-3 bg-purple-50 dark:bg-purple-950/60 rounded-xl text-purple-600 dark:text-purple-400">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Solver Engine</div>
            <div className="text-sm font-bold text-slate-900 dark:text-white">Google OR-Tools CP-SAT</div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm flex items-center gap-3">
          <div className="p-3 bg-amber-50 dark:bg-amber-950/60 rounded-xl text-amber-600 dark:text-amber-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Scope Capacity</div>
            <div className="text-sm font-bold text-slate-900 dark:text-white">1,000 Slots / Week</div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm flex items-center gap-3">
          <div className="p-3 bg-emerald-50 dark:bg-emerald-950/60 rounded-xl text-emerald-600 dark:text-emerald-400">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Avg Solve Time</div>
            <div className="text-sm font-bold text-slate-900 dark:text-white">&lt; 15 Seconds</div>
          </div>
        </div>
      </div>

      {/* Success Banner if Timetable Generated */}
      {lastGenerated && (
        <div className="bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-2xl p-5 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-emerald-600 rounded-xl text-white">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-emerald-900 dark:text-emerald-200">
                AI Timetable Successfully Generated!
              </h3>
              <p className="text-xs text-emerald-700 dark:text-emerald-400">
                Generated {lastGenerated.entries_count || 0} slot entries with {lastGenerated.hard_violations || 0} hard clashes and soft penalty score {lastGenerated.soft_violations || 0}.
              </p>
            </div>
          </div>
          <Link
            href="/schedule"
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-sm transition-colors flex items-center gap-1.5 shrink-0 cursor-pointer"
          >
            Open Interactive Grid <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}

      {/* Main Multi-Step Setup Wizard Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between px-1">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Cpu className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              Interactive AI Rule Configurator
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Customize academic scope, teacher caps, venue pools, and continuous lab locks.
            </p>
          </div>
        </div>

        {/* Wizard Container */}
        <ScheduleSetupWizard onSuccess={handleWizardSuccess} />
      </div>
    </div>
  );
}
