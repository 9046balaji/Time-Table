"use client";

import React from "react";

export interface HourlySlotOccupancy {
  period: string; // "P1", "P2", ...
  occupancyRate: number; // 0-100
}

interface RoomUtilizationHeatmapProps {
  slots?: HourlySlotOccupancy[];
}

const DEFAULT_SLOTS: HourlySlotOccupancy[] = [
  { period: "P1 (08:15-09:05)", occupancyRate: 92 },
  { period: "P2 (09:05-09:55)", occupancyRate: 95 },
  { period: "P3 (10:10-11:00)", occupancyRate: 98 },
  { period: "P4 (11:00-11:50)", occupancyRate: 96 },
  { period: "P5 (11:50-12:40)", occupancyRate: 90 },
  { period: "P6 (13:40-14:30)", occupancyRate: 88 },
  { period: "P7 (14:30-15:20)", occupancyRate: 84 },
  { period: "P8 (15:20-16:05)", occupancyRate: 76 },
];

export const RoomUtilizationHeatmap: React.FC<RoomUtilizationHeatmapProps> = ({ slots = DEFAULT_SLOTS }) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-slate-900">Period-Wise Room Occupancy Matrix Heatmap</h3>
          <p className="text-xs text-slate-500">Hourly utilization rates across 45 venues (Periods 1 to 8)</p>
        </div>
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
          Peak Occupancy: 98% (P3)
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
        {slots.map((s, idx) => {
          const bgClass =
            s.occupancyRate >= 95
              ? "bg-red-50 border-red-200 text-red-900"
              : s.occupancyRate >= 90
              ? "bg-amber-50 border-amber-200 text-amber-900"
              : "bg-emerald-50 border-emerald-200 text-emerald-900";

          return (
            <div key={idx} className={`p-3 rounded-lg border space-y-1 ${bgClass}`}>
              <div className="text-[11px] font-semibold text-slate-700">{s.period}</div>
              <div className="flex items-baseline justify-between">
                <span className="text-lg font-bold">{s.occupancyRate}%</span>
                <span className="text-[10px] font-medium text-slate-500">Occupied</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
