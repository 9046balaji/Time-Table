"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Sparkles, Calendar } from "lucide-react";
import { ScheduleSetupWizard } from "@/components/wizard/ScheduleSetupWizard";
import { WizardGenerationResponse } from "@/lib/types";

export default function AISchedulerPage() {
  const [, setLastGenerated] = useState<WizardGenerationResponse | null>(null);

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-100 dark:bg-blue-950/60 border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300 text-[11px] font-bold">
              <Sparkles className="w-3 h-3 animate-pulse" />
              OR-Tools CP-SAT · 0-Clash Guarantee
            </span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">AI Timetable Generator</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Pick sections, hit Generate — all 10 hard constraints enforced automatically.
          </p>
        </div>
        <Link
          href="/schedule"
          className="shrink-0 inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs font-bold hover:border-blue-400 dark:hover:border-blue-600 transition-colors shadow-sm"
        >
          <Calendar className="w-4 h-4 text-blue-500" />
          View Timetable Grid
        </Link>
      </div>

      {/* Main Wizard */}
      <ScheduleSetupWizard onSuccess={setLastGenerated} />
    </div>
  );
}
