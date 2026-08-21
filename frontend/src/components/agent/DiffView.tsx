import React from 'react';

interface TimetableSlot {
  id?: string | number;
  section: string;
  day: string;
  period: number | string;
  subject: string;
  room: string;
  faculty?: string[] | string;
  type?: string;
}

interface DiffViewProps {
  originalEntries: TimetableSlot[];
  repairedEntries: TimetableSlot[];
  stabilityScore?: number;
  movedCount?: number;
  displacedSections?: string[];
  onRollback?: () => Promise<void>;
  loading?: boolean;
}

export const DiffView: React.FC<DiffViewProps> = ({
  originalEntries = [],
  repairedEntries = [],
  stabilityScore = 100,
  movedCount = 0,
  displacedSections = [],
  onRollback,
  loading = false,
}) => {
  const [showOnlyChanges, setShowOnlyChanges] = React.useState<boolean>(true);

  if (!repairedEntries || repairedEntries.length === 0) {
    return null;
  }

  // Find changed slots
  const origMap = new Map(originalEntries.map((e) => [String(e.id || `${e.section}_${e.day}_${e.period}`), e]));
  const changedSlots = repairedEntries.filter((rep) => {
    const key = String(rep.id || `${rep.section}_${rep.day}_${rep.period}`);
    const orig = origMap.get(key);
    if (!orig) return false;
    return orig.room !== rep.room || orig.day !== rep.day || orig.period !== rep.period;
  });

  const displaySlots = (showOnlyChanges ? changedSlots : repairedEntries).slice(0, 100);

  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4 pb-4 border-b border-slate-100 dark:border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">Minimal-Disruption Repair Inspector</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">Comparing pre-incident schedule vs. candidate CP-SAT local repair</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right font-mono">
            <div className="text-xs text-slate-400">Stability Score</div>
            <div className="text-base font-bold text-emerald-600 dark:text-emerald-400">{stabilityScore}%</div>
          </div>
          <div className="text-right font-mono border-l border-slate-200 dark:border-slate-800 pl-3">
            <div className="text-xs text-slate-400">Moved Slots</div>
            <div className="text-base font-bold text-indigo-600 dark:text-indigo-400">{movedCount}</div>
          </div>
          {onRollback && (
            <button
              type="button"
              disabled={loading}
              onClick={onRollback}
              className="ml-2 px-3 py-1.5 rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 text-xs font-semibold hover:bg-red-100 transition-all"
            >
              ↩ 1-Click Rollback
            </button>
          )}
        </div>
      </div>

      {changedSlots.length === 0 ? (
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 text-center text-xs text-slate-500">
          No entries required relocation. Schedule remains 100% stable.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-50 dark:bg-slate-800 text-slate-500 font-mono text-[11px] uppercase">
              <tr>
                <th className="p-2.5 rounded-l-lg">Section</th>
                <th className="p-2.5">Subject</th>
                <th className="p-2.5">Day / Period</th>
                <th className="p-2.5 text-red-600">Original Room</th>
                <th className="p-2.5 text-emerald-600 rounded-r-lg">Repaired Room</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {displaySlots.map((rep, idx) => {
                const key = String(rep.id || `${rep.section}_${rep.day}_${rep.period}`);
                const orig = origMap.get(key);
                return (
                  <tr key={idx} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 font-mono">
                    <td className="p-2.5 font-bold text-slate-800 dark:text-slate-200">{rep.section}</td>
                    <td className="p-2.5 text-slate-600 dark:text-slate-300">{rep.subject}</td>
                    <td className="p-2.5 text-slate-500">{rep.day} P{rep.period}</td>
                    <td className="p-2.5 text-red-600 bg-red-50/50 dark:bg-red-950/20 font-semibold">{orig ? orig.room : 'N/A'}</td>
                    <td className="p-2.5 text-emerald-600 bg-emerald-50/50 dark:bg-emerald-950/20 font-semibold">{rep.room}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
