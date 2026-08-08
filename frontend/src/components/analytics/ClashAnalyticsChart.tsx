"use client";

import React from "react";

export interface ClashDistribution {
  day: string;
  roomClashes: number;
  facultyClashes: number;
  sectionClashes: number;
  total: number;
}

interface ClashAnalyticsChartProps {
  data?: ClashDistribution[];
}

const DEFAULT_DATA: ClashDistribution[] = [
  { day: "MON", roomClashes: 9, facultyClashes: 0, sectionClashes: 0, total: 9 },
  { day: "TUE", roomClashes: 11, facultyClashes: 0, sectionClashes: 0, total: 11 },
  { day: "WED", roomClashes: 8, facultyClashes: 0, sectionClashes: 0, total: 8 },
  { day: "THU", roomClashes: 12, facultyClashes: 0, sectionClashes: 0, total: 12 },
  { day: "FRI", roomClashes: 7, facultyClashes: 0, sectionClashes: 0, total: 7 },
  { day: "SAT", roomClashes: 4, facultyClashes: 0, sectionClashes: 0, total: 4 },
];

export const ClashAnalyticsChart: React.FC<ClashAnalyticsChartProps> = ({ data = DEFAULT_DATA }) => {
  const maxClash = Math.max(...data.map((d) => d.total), 1);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-slate-900">Day-Wise Hard Violation Breakdown (V5 Ground Truth)</h3>
          <p className="text-xs text-slate-500">Distribution of 51 baseline room clashes across Monday–Saturday</p>
        </div>
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
          51 Room Clashes Detected
        </span>
      </div>

      <div className="pt-2 grid grid-cols-6 gap-3 text-center">
        {data.map((d, idx) => {
          const heightPercent = (d.total / maxClash) * 100;
          return (
            <div key={idx} className="flex flex-col items-center gap-2">
              <span className="text-xs font-bold text-red-600">{d.total}</span>
              <div className="w-full bg-slate-100 rounded-lg h-32 flex items-end p-1">
                <div
                  className="w-full bg-red-500 rounded-md transition-all duration-500 hover:bg-red-600"
                  style={{ height: `${heightPercent}%` }}
                />
              </div>
              <span className="text-xs font-semibold text-slate-700">{d.day}</span>
            </div>
          );
        })}
      </div>

      <div className="flex items-center justify-between text-xs text-slate-500 border-t border-slate-100 pt-3">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-red-500 inline-block"/> HC-01 Room Conflicts (51)</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-amber-500 inline-block"/> HC-02 Faculty Conflicts (0)</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-blue-500 inline-block"/> HC-03 Section Conflicts (0)</span>
        </div>
        <span className="font-semibold text-slate-800">Peak Conflict Day: THU (12 clashes)</span>
      </div>
    </div>
  );
};
