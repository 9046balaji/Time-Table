'use client';

import React, { useState, useEffect } from 'react';
import { Sliders, CheckCircle2, Award, Zap, Compass, Activity } from 'lucide-react';
import { getApiBaseUrl } from '@/lib/api';

export const ParetoExplorerPanel: React.FC = () => {
  const [versionId, setVersionId] = useState(5);
  const [loading, setLoading] = useState(false);
  const [paretoData, setParetoData] = useState<any | null>(null);
  const [selectedProfile, setSelectedProfile] = useState<string>('BALANCED_CONSENSUS');
  const [error, setError] = useState<string | null>(null);

  const apiBase = getApiBaseUrl();

  const handleEvaluate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/api/v1/agent/pareto/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ version_id: Number(versionId) })
      });
      if (!res.ok) {
        throw new Error('Failed to evaluate Pareto trade-offs');
      }
      const data = await res.json();
      setParetoData(data);
    } catch (err: any) {
      setError(err.message || 'Error evaluating Pareto frontier');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleEvaluate();
  }, [versionId]);

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2.5 bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 rounded-lg">
          <Compass className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">Multi-Objective Pareto Frontier Explorer</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Systematically balance competing trade-offs: Faculty Fatigue, Student Free Gaps, and Campus Cross-Block Transit.
          </p>
        </div>
      </div>

      {paretoData && (
        <div className="space-y-6">
          {/* Sub-Objective Scores */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700">
              <span className="text-xs text-slate-500 font-semibold">Faculty Fatigue Rating</span>
              <div className="flex items-baseline justify-between mt-1">
                <span className="text-2xl font-black text-blue-600 dark:text-blue-400">
                  {paretoData.objectives.faculty_fatigue_score}
                </span>
                <span className="text-xs text-slate-400">/ 100</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                {paretoData.objectives.raw_metrics.heavy_faculty_days} heavy faculty days (&ge;5h)
              </p>
            </div>

            <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700">
              <span className="text-xs text-slate-500 font-semibold">Student Schedule Pacing</span>
              <div className="flex items-baseline justify-between mt-1">
                <span className="text-2xl font-black text-emerald-600 dark:text-emerald-400">
                  {paretoData.objectives.student_gap_score}
                </span>
                <span className="text-xs text-slate-400">/ 100</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                {paretoData.objectives.raw_metrics.isolated_student_gaps} isolated free downtime gaps
              </p>
            </div>

            <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700">
              <span className="text-xs text-slate-500 font-semibold">Campus Block Locality</span>
              <div className="flex items-baseline justify-between mt-1">
                <span className="text-2xl font-black text-purple-600 dark:text-purple-400">
                  {paretoData.objectives.campus_transit_score}
                </span>
                <span className="text-xs text-slate-400">/ 100</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                {paretoData.objectives.raw_metrics.cross_block_sprints} cross-block student sprints
              </p>
            </div>

            <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700">
              <span className="text-xs text-slate-500 font-semibold">Afternoon Load Balance</span>
              <div className="flex items-baseline justify-between mt-1">
                <span className="text-2xl font-black text-amber-600 dark:text-amber-400">
                  {paretoData.objectives.afternoon_load_score}
                </span>
                <span className="text-xs text-slate-400">/ 100</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                {paretoData.objectives.raw_metrics.late_afternoon_pct}% classes in P7-P8
              </p>
            </div>
          </div>

          {/* Pareto Profiles Grid */}
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-3">Institutional Policy Profiles</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(paretoData.profile_scores).map(([pKey, pVal]: any) => (
                <div
                  key={pKey}
                  onClick={() => setSelectedProfile(pKey)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    selectedProfile === pKey
                      ? 'border-amber-500 bg-amber-50/40 dark:bg-amber-950/20 shadow-sm ring-1 ring-amber-500'
                      : 'border-slate-200 dark:border-slate-800 bg-slate-50/40 dark:bg-slate-800/20 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-1.5">
                      <Award className="w-4 h-4 text-amber-600" />
                      {pVal.name}
                    </h4>
                    <span className="text-xs font-black px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300">
                      Score: {pVal.composite_score}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">{pVal.description}</p>
                  <div className="w-full bg-slate-200 dark:bg-slate-700 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-amber-500 h-full rounded-full transition-all duration-500"
                      style={{ width: `${pVal.composite_score}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
