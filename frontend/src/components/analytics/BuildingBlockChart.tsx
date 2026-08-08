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
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-slate-900">Building Block & Venue Capacity Distribution</h3>
          <p className="text-xs text-slate-500">Real-time room allocation across academic blocks</p>
        </div>
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
          5 Blocks Registered
        </span>
      </div>

      <div className="space-y-3.5 pt-2">
        {blocks.map((b, idx) => (
          <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-2 hover:border-blue-200 transition-colors">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-800">{b.name}</span>
              <div className="flex items-center gap-3 text-slate-600">
                <span>{b.classrooms} Classrooms</span>
                <span>•</span>
                <span>{b.computerLabs} Labs</span>
                {b.gpuLabs > 0 && (
                  <>
                    <span>•</span>
                    <span className="text-purple-700 font-medium">{b.gpuLabs} GPU Labs</span>
                  </>
                )}
                <span className="font-semibold text-slate-900 ml-2">{b.occupancyRate}% Occupied</span>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden flex">
              <div
                className="h-full bg-blue-600 rounded-full transition-all duration-500"
                style={{ width: `${b.occupancyRate}%` }}
              />
            </div>

            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span>Total Capacity: {b.totalCapacity} Students</span>
              <span>Available Slots: {Math.round(b.totalCapacity * (1 - b.occupancyRate / 100))}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
