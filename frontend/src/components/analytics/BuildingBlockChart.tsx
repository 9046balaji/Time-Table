"use client";

import React from "react";

export interface BuildingBlockData {
  name: string;
  classrooms: number;
  computerLabs: number;
  gpuLabs: number;
  totalCapacity: number;
  occupancyRate: number; // 0-100
}

interface BuildingBlockChartProps {
  blocks?: BuildingBlockData[];
}

const DEFAULT_BLOCKS: BuildingBlockData[] = [
  { name: "Aryabhatta Bhavan (U-Block)", classrooms: 18, computerLabs: 9, gpuLabs: 3, totalCapacity: 1680, occupancyRate: 84 },
  { name: "Divisional Bhavan (H-Block)", classrooms: 4, computerLabs: 0, gpuLabs: 0, totalCapacity: 240, occupancyRate: 92 },
  { name: "A-Block Activity Center", classrooms: 2, computerLabs: 0, gpuLabs: 0, totalCapacity: 110, occupancyRate: 65 },
  { name: "Central Library Complex", classrooms: 0, computerLabs: 1, gpuLabs: 0, totalCapacity: 100, occupancyRate: 78 },
  { name: "Special Department Labs", classrooms: 0, computerLabs: 5, gpuLabs: 0, totalCapacity: 300, occupancyRate: 88 },
];

export const BuildingBlockChart: React.FC<BuildingBlockChartProps> = ({ blocks = DEFAULT_BLOCKS }) => {
  const totalClassrooms = blocks.reduce((acc, b) => acc + b.classrooms, 0);
  const totalLabs = blocks.reduce((acc, b) => acc + b.computerLabs, 0);
  const totalGpuLabs = blocks.reduce((acc, b) => acc + b.gpuLabs, 0);
  const totalCapacity = blocks.reduce((acc, b) => acc + b.totalCapacity, 0);
  const avgOccupancy = blocks.length
    ? Math.round(blocks.reduce((acc, b) => acc + b.occupancyRate, 0) / blocks.length)
    : 0;

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">
            Building Block & Venue Capacity
          </h3>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">
            Real-time block occupancy & seat distribution
          </p>
        </div>
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
          {blocks.length} Blocks • {totalCapacity.toLocaleString()} Seats
        </span>
      </div>

      {/* Compact Block List */}
      <div className="space-y-1 pt-1">
        {blocks.map((b, idx) => (
          <div
            key={idx}
            className="flex items-center justify-between gap-3 py-1.5 px-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors border border-transparent hover:border-slate-200 dark:hover:border-slate-700/60"
          >
            {/* Block Info */}
            <div className="flex items-center gap-2 min-w-0 flex-1">
              <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate max-w-[170px]" title={b.name}>
                {b.name}
              </span>
              <div className="hidden sm:flex items-center gap-1 text-[10px] text-slate-400 dark:text-slate-500 font-medium shrink-0">
                <span>{b.classrooms} CR</span>
                <span>•</span>
                <span>{b.computerLabs} Lab</span>
                {b.gpuLabs > 0 && (
                  <>
                    <span>•</span>
                    <span className="text-purple-600 dark:text-purple-400 font-semibold">{b.gpuLabs} GPU</span>
                  </>
                )}
              </div>
            </div>

            {/* Progress Bar & Rate */}
            <div className="flex items-center gap-2.5 shrink-0">
              <div className="w-24 sm:w-32 bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden flex">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    b.occupancyRate >= 90
                      ? "bg-amber-500"
                      : b.occupancyRate >= 75
                      ? "bg-blue-600 dark:bg-blue-500"
                      : "bg-emerald-500"
                  }`}
                  style={{ width: `${b.occupancyRate}%` }}
                />
              </div>

              <div className="flex items-center gap-2 text-[11px]">
                <span className="font-bold text-slate-800 dark:text-slate-200 w-8 text-right">
                  {b.occupancyRate}%
                </span>
                <span className="text-slate-400 dark:text-slate-500 w-14 text-right hidden sm:inline">
                  {b.totalCapacity} seats
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer Summary */}
      <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 border-t border-slate-100 dark:border-slate-800/80 pt-2.5 px-1">
        <span className="truncate">
          Total: <strong className="text-slate-700 dark:text-slate-300 font-semibold">{totalClassrooms}</strong> CR •{" "}
          <strong className="text-slate-700 dark:text-slate-300 font-semibold">{totalLabs}</strong> Labs •{" "}
          <strong className="text-slate-700 dark:text-slate-300 font-semibold">{totalGpuLabs}</strong> GPU
        </span>
        <span className="font-semibold text-slate-700 dark:text-slate-300 shrink-0 ml-2">
          Avg Occupancy: {avgOccupancy}%
        </span>
      </div>
    </div>
  );
};

