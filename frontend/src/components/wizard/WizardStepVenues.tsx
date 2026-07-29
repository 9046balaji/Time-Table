import React from "react";
import { Building2, Lock, CheckCircle2, ShieldCheck, AlertCircle } from "lucide-react";

interface WizardStepVenuesProps {
  roomsPool: any[];
  preferredBlock: string;
}

export const WizardStepVenues: React.FC<WizardStepVenuesProps> = ({ roomsPool, preferredBlock }) => {
  const classrooms = roomsPool.filter((r) => r.room_type === "classroom" || !r.room_type);
  const computerLabs = roomsPool.filter((r) => r.room_type === "computer_lab");
  const gpuLabs = roomsPool.filter((r) => r.room_type === "gpu_lab");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <h3 className="flex items-center gap-2 text-sm font-bold text-slate-800">
          <Building2 className="h-4 w-4 text-purple-600" /> 3. Venue Pool Matrix & Global Synchronized Locks
        </h3>
        <span className="rounded-full bg-purple-100 px-3 py-1 text-xs font-extrabold text-purple-800">
          {roomsPool.length} Venues Active
        </span>
      </div>

      {/* Global Synchronized Locks Information Card */}
      <div className="rounded-2xl border border-amber-200 bg-amber-50/60 p-4">
        <h4 className="flex items-center gap-2 text-xs font-extrabold text-amber-900">
          <Lock className="h-4 w-4 text-amber-600" /> Global Synchronized Slot Constraints (Hard-Locked):
        </h4>
        <div className="mt-2 grid grid-cols-1 gap-2 text-xs font-semibold text-amber-800 sm:grid-cols-3">
          <div className="flex items-center gap-2 rounded-xl bg-white p-2.5 shadow-sm border border-amber-100">
            <CheckCircle2 className="h-4 w-4 text-amber-600 shrink-0" />
            <span><strong>Minors & Honors:</strong> Wed & Thu Periods 7–8</span>
          </div>
          <div className="flex items-center gap-2 rounded-xl bg-white p-2.5 shadow-sm border border-amber-100">
            <CheckCircle2 className="h-4 w-4 text-amber-600 shrink-0" />
            <span><strong>Open Electives (OE):</strong> Sat Periods 4–5</span>
          </div>
          <div className="flex items-center gap-2 rounded-xl bg-white p-2.5 shadow-sm border border-amber-100">
            <CheckCircle2 className="h-4 w-4 text-amber-600 shrink-0" />
            <span><strong>Blocked Windows:</strong> Lunch (12:40-13:40) & Short Break</span>
          </div>
        </div>
      </div>

      {/* Venues Categorized Display */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {/* Theory Classrooms */}
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <h4 className="mb-2 text-xs font-extrabold text-slate-800 flex items-center justify-between">
            <span>Theory Classrooms</span>
            <span className="rounded-md bg-slate-100 px-2 py-0.5 text-slate-600 font-bold">{classrooms.length} Rooms</span>
          </h4>
          <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto pr-1">
            {classrooms.map((r) => (
              <span key={r.id} className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1 text-[11px] font-bold text-slate-700">
                {r.id} ({r.capacity} Seats)
              </span>
            ))}
          </div>
        </div>

        {/* Computer Labs */}
        <div className="rounded-2xl border border-violet-200 bg-violet-50/40 p-4">
          <h4 className="mb-2 text-xs font-extrabold text-violet-900 flex items-center justify-between">
            <span>Computer Labs (P Slots)</span>
            <span className="rounded-md bg-violet-100 px-2 py-0.5 text-violet-700 font-bold">{computerLabs.length} Labs</span>
          </h4>
          <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto pr-1">
            {computerLabs.map((r) => (
              <span key={r.id} className="rounded-lg border border-violet-200 bg-white px-2 py-1 text-[11px] font-bold text-violet-900 shadow-sm">
                Lab {r.id} ({r.capacity} PCs)
              </span>
            ))}
          </div>
        </div>

        {/* GPU Labs */}
        <div className="rounded-2xl border border-indigo-200 bg-indigo-50/40 p-4">
          <h4 className="mb-2 text-xs font-extrabold text-indigo-900 flex items-center justify-between">
            <span>High-Cap GPU AI Labs</span>
            <span className="rounded-md bg-indigo-100 px-2 py-0.5 text-indigo-700 font-bold">{gpuLabs.length} GPU Labs</span>
          </h4>
          <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto pr-1">
            {gpuLabs.map((r) => (
              <span key={r.id} className="rounded-lg border border-indigo-300 bg-indigo-600 px-2 py-1 text-[11px] font-bold text-white shadow-sm">
                ⚡ {r.id} ({r.capacity} GPUs)
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
