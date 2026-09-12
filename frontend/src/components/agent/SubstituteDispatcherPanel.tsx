'use client';

import React, { useState } from 'react';
import { UserCheck, AlertTriangle, ShieldCheck, UserX, Clock, BookOpen, CheckCircle, ArrowRight } from 'lucide-react';
import { getApiBaseUrl } from '@/lib/api';

export const SubstituteDispatcherPanel: React.FC = () => {
  const [facultyName, setFacultyName] = useState('Dr. S. Srikantha Reddy');
  const [day, setDay] = useState('MON');
  const [period, setPeriod] = useState(1);
  const [subject, setSubject] = useState('DS');
  const [loading, setLoading] = useState(false);
  const [dispatching, setDispatching] = useState<number | null>(null);
  const [candidatesData, setCandidatesData] = useState<any | null>(null);
  const [dispatchSuccess, setDispatchSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const apiBase = getApiBaseUrl();

  const handleSearch = async () => {
    setLoading(true);
    setError(null);
    setDispatchSuccess(null);
    try {
      const res = await fetch(`${apiBase}/api/v1/agent/substitute/find-candidates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          faculty_name: facultyName,
          day,
          period: Number(period),
          subject,
          version_id: 5
        })
      });
      if (!res.ok) {
        throw new Error('Failed to fetch substitute candidates');
      }
      const data = await res.json();
      setCandidatesData(data);
    } catch (err: any) {
      setError(err.message || 'Error searching candidates');
    } finally {
      setLoading(false);
    }
  };

  const handleDispatch = async (substituteId: number, substituteName: string) => {
    setDispatching(substituteId);
    setError(null);
    setDispatchSuccess(null);
    try {
      const targetEntryId = candidatesData?.impacted_slot?.id || 1;
      const res = await fetch(`${apiBase}/api/v1/agent/substitute/dispatch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: 1,
          entry_id: targetEntryId,
          substitute_faculty_id: substituteId,
          original_faculty_name: facultyName,
          reason: `Emergency absence coverage for ${facultyName}`
        })
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Dispatch failed');
      }
      const result = await res.json();
      setDispatchSuccess(`Successfully dispatched ${substituteName} to cover ${facultyName}'s class!`);
    } catch (err: any) {
      setError(err.message || 'Dispatch error');
    } finally {
      setDispatching(null);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2.5 bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-400 rounded-lg">
          <UserCheck className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">Autonomous Substitute Faculty Dispatcher</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Intelligent candidate ranking adhering to AICTE weekly hours, daily fatigue caps, and subject competency.
          </p>
        </div>
      </div>

      {/* Query Form */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg mb-6 border border-slate-200 dark:border-slate-700">
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Absent Faculty</label>
          <input
            type="text"
            className="w-full text-sm px-3 py-2 border rounded-md dark:bg-slate-800 dark:border-slate-700 text-slate-900 dark:text-white"
            value={facultyName}
            onChange={(e) => setFacultyName(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Day</label>
          <select
            className="w-full text-sm px-3 py-2 border rounded-md dark:bg-slate-800 dark:border-slate-700 text-slate-900 dark:text-white"
            value={day}
            onChange={(e) => setDay(e.target.value)}
          >
            {['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'].map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Period</label>
          <select
            className="w-full text-sm px-3 py-2 border rounded-md dark:bg-slate-800 dark:border-slate-700 text-slate-900 dark:text-white"
            value={period}
            onChange={(e) => setPeriod(Number(e.target.value))}
          >
            {[1, 2, 3, 4, 5, 6, 7, 8].map((p) => (
              <option key={p} value={p}>Period {p}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Subject</label>
          <div className="flex gap-2">
            <input
              type="text"
              className="w-full text-sm px-3 py-2 border rounded-md dark:bg-slate-800 dark:border-slate-700 text-slate-900 dark:text-white"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            />
            <button
              onClick={handleSearch}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-semibold transition-colors disabled:opacity-50"
            >
              {loading ? 'Searching...' : 'Find'}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-3 mb-4 rounded-md bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 text-sm border border-red-200 dark:border-red-800 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          {error}
        </div>
      )}

      {dispatchSuccess && (
        <div className="p-3 mb-4 rounded-md bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 text-sm border border-emerald-200 dark:border-emerald-800 flex items-center gap-2">
          <CheckCircle className="w-4 h-4" />
          {dispatchSuccess}
        </div>
      )}

      {/* Candidates List */}
      {candidatesData && (
        <div>
          {candidatesData.impacted_slot && (
            <div className="mb-4 p-3 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 flex flex-wrap items-center justify-between gap-2 text-xs">
              <div className="flex items-center gap-2">
                <span className="font-bold text-indigo-700 dark:text-indigo-300">Target Class:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {candidatesData.impacted_slot.section || 'N/A'} • {candidatesData.impacted_slot.subject || subject} • Room {candidatesData.impacted_slot.room || 'N/A'}
                </span>
              </div>
              <span className="px-2 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300 font-mono text-[10px] font-bold">
                Entry #{candidatesData.impacted_slot.id}
              </span>
            </div>
          )}

          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">
              Ranked Candidates for {day} Period {period} ({candidatesData.eligible_candidates_count} eligible of {candidatesData.total_candidates})
            </h3>
            <span className="text-xs text-slate-500">Evaluated in {candidatesData.execution_time_ms}ms</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {candidatesData.candidates.slice(0, 6).map((c: any) => (
              <div
                key={c.id}
                className={`p-4 rounded-lg border transition-all ${
                  c.is_eligible
                    ? 'border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-800/30'
                    : 'border-slate-200 dark:border-slate-800 opacity-60 bg-slate-100/50 dark:bg-slate-900'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h4 className="font-semibold text-slate-900 dark:text-white text-sm">{c.name}</h4>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{c.designation}</p>
                  </div>
                  <span
                    className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                      c.status === 'RECOMMENDED'
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                        : c.status === 'ELIGIBLE'
                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300'
                        : 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300'
                    }`}
                  >
                    {c.status}
                  </span>
                </div>

                <div className="space-y-1.5 my-3 text-xs text-slate-600 dark:text-slate-300">
                  <div className="flex justify-between">
                    <span>Weekly Load:</span>
                    <span className="font-semibold">{c.current_weekly_hours} / {c.max_weekly_hours}h</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Daily Load on {day}:</span>
                    <span className="font-semibold">{c.daily_hours_at_target_day} classes</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Suitability Rating:</span>
                    <span className="font-bold text-blue-600 dark:text-blue-400">{c.suitability_score}%</span>
                  </div>
                </div>

                {c.rejection_reasons.length > 0 && (
                  <p className="text-xs text-red-600 dark:text-red-400 mb-3">
                    Conflicts: {c.rejection_reasons.join(', ')}
                  </p>
                )}

                {c.is_eligible && (
                  <button
                    onClick={() => handleDispatch(c.id, c.name)}
                    disabled={dispatching === c.id}
                    className="w-full mt-2 py-1.5 px-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
                  >
                    {dispatching === c.id ? 'Dispatching...' : 'Dispatch as Substitute'}
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
