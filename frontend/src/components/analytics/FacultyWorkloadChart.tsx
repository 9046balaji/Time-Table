"use client";

import React from "react";

export interface RankWorkloadSummary {
  rank: string;
  totalFaculty: number;
  maxCapHours: number;
  avgAssignedHours: number;
  utilizationRate: number; // 0-100
}

interface FacultyWorkloadChartProps {
  ranks?: RankWorkloadSummary[];
}

const DEFAULT_RANKS: RankWorkloadSummary[] = [
  { rank: "Professor", totalFaculty: 28, maxCapHours: 12, avgAssignedHours: 11.2, utilizationRate: 93 },
  { rank: "Associate Professor", totalFaculty: 42, maxCapHours: 14, avgAssignedHours: 13.1, utilizationRate: 94 },
  { rank: "Assistant Professor", totalFaculty: 92, maxCapHours: 16, avgAssignedHours: 14.8, utilizationRate: 92.5 },
];

export const FacultyWorkloadChart: React.FC<FacultyWorkloadChartProps> = ({ ranks = DEFAULT_RANKS }) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-slate-900">Faculty Rank & Teaching Workload Distribution</h3>
          <p className="text-xs text-slate-500">Compliance with rank workload caps (HC-11 enforcement)</p>
        </div>
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-50 text-purple-700 border border-purple-200">
          162 Faculty Monitored
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
        {ranks.map((r, idx) => {
          const colorClass =
            r.rank === "Professor"
              ? "bg-purple-600"
              : r.rank === "Associate Professor"
              ? "bg-blue-600"
              : "bg-emerald-600";

          return (
            <div key={idx} className="p-4 bg-slate-50 rounded-xl border border-slate-100 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900">{r.rank}</span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-700">
                  {r.totalFaculty} Faculty
                </span>
              </div>

              <div className="space-y-1">
                <div className="flex items-baseline justify-between text-xs">
                  <span className="text-slate-500">Avg Assigned</span>
                  <span className="font-semibold text-slate-900">
                    {r.avgAssignedHours}h / {r.maxCapHours}h
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-full ${colorClass} transition-all duration-500`}
                    style={{ width: `${r.utilizationRate}%` }}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                <span>Max Cap: {r.maxCapHours} hrs/wk</span>
                <span className="text-emerald-600 font-medium">0 Violations</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
