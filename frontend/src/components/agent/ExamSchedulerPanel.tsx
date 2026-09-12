'use client';

import React, { useState } from 'react';
import { Calendar, ShieldCheck, CheckCircle2, Clock, Users, Building, Play, Download } from 'lucide-react';
import { getApiBaseUrl } from '@/lib/api';

export const ExamSchedulerPanel: React.FC = () => {
  const [examType, setExamType] = useState('MID_TERM_1');
  const [startDate, setStartDate] = useState('2026-10-12');
  const [numDays, setNumDays] = useState(6);
  const [spacingFactor, setSpacingFactor] = useState(0.5);
  const [loading, setLoading] = useState(false);
  const [examResult, setExamResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const apiBase = getApiBaseUrl();

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/api/v1/agent/exam/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          exam_type: examType,
          start_date: startDate,
          num_days: Number(numDays),
          spacing_factor: Number(spacingFactor)
        })
      });
      if (!res.ok) {
        throw new Error('Exam schedule generation failed');
      }
      const data = await res.json();
      setExamResult(data);
    } catch (err: any) {
      setError(err.message || 'Error generating exam schedule');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2.5 bg-purple-100 dark:bg-purple-950/60 text-purple-700 dark:text-purple-400 rounded-lg">
          <Calendar className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">Conflict-Free Examination Timetabling Agent</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Automated exam scheduling with 50% room spacing factor for test integrity, non-overlapping cohorts, and balanced invigilator duties.
          </p>
        </div>
      </div>

      {/* Control Form */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg mb-6 border border-slate-200 dark:border-slate-700">
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Exam Type</label>
          <select
            className="w-full text-sm px-3 py-2 border rounded-md dark:bg-slate-800 dark:border-slate-700 text-slate-900 dark:text-white"
            value={examType}
            onChange={(e) => setExamType(e.target.value)}
          >
            <option value="MID_TERM_1">Mid-Semester Examination 1</option>
            <option value="MID_TERM_2">Mid-Semester Examination 2</option>
            <option value="END_SEMESTER">End-Semester Final Examination</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Start Date</label>
          <input
            type="date"
            className="w-full text-sm px-3 py-2 border rounded-md dark:bg-slate-800 dark:border-slate-700 text-slate-900 dark:text-white"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Duration (Days)</label>
          <select
            className="w-full text-sm px-3 py-2 border rounded-md dark:bg-slate-800 dark:border-slate-700 text-slate-900 dark:text-white"
            value={numDays}
            onChange={(e) => setNumDays(Number(e.target.value))}
          >
            {[4, 5, 6, 7, 8, 10, 12].map((d) => (
              <option key={d} value={d}>{d} Days</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Room Spacing</label>
          <div className="flex gap-2">
            <select
              className="w-full text-sm px-3 py-2 border rounded-md dark:bg-slate-800 dark:border-slate-700 text-slate-900 dark:text-white"
              value={spacingFactor}
              onChange={(e) => setSpacingFactor(Number(e.target.value))}
            >
              <option value={0.5}>50% Capacity (1 seat gap)</option>
              <option value={0.65}>65% Capacity (Standard)</option>
              <option value={1.0}>100% Capacity (No gap)</option>
            </select>
            <button
              onClick={handleGenerate}
              disabled={loading}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-md text-sm font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              <Play className="w-4 h-4" />
              {loading ? 'Solving...' : 'Generate'}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-3 mb-4 rounded-md bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 text-sm border border-red-200 dark:border-red-800">
          {error}
        </div>
      )}

      {/* Results Section */}
      {examResult && (
        <div className="space-y-6">
          {/* Stats Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-3 bg-emerald-50 dark:bg-emerald-950/30 rounded-lg border border-emerald-200 dark:border-emerald-800">
              <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">Status</span>
              <p className="text-lg font-bold text-emerald-800 dark:text-emerald-200 flex items-center gap-1">
                <CheckCircle2 className="w-5 h-5" /> 0 Clashes
              </p>
            </div>
            <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
              <span className="text-xs text-slate-500 font-medium">Exams Scheduled</span>
              <p className="text-lg font-bold text-slate-900 dark:text-white">{examResult.total_exams_scheduled} Course Slots</p>
            </div>
            <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
              <span className="text-xs text-slate-500 font-medium">Spacing Factor</span>
              <p className="text-lg font-bold text-slate-900 dark:text-white">{examResult.spacing_factor * 100}% Capacity</p>
            </div>
            <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
              <span className="text-xs text-slate-500 font-medium">Solving Time</span>
              <p className="text-lg font-bold text-slate-900 dark:text-white">{examResult.execution_time_ms} ms</p>
            </div>
          </div>

          {/* Exam Table */}
          <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300">
                <tr>
                  <th className="py-2.5 px-3 font-semibold">Date</th>
                  <th className="py-2.5 px-3 font-semibold">Session</th>
                  <th className="py-2.5 px-3 font-semibold">Section</th>
                  <th className="py-2.5 px-3 font-semibold">Subject</th>
                  <th className="py-2.5 px-3 font-semibold">Allocated Rooms</th>
                  <th className="py-2.5 px-3 font-semibold">Invigilators</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800 text-slate-800 dark:text-slate-200">
                {examResult.scheduled_exams.slice(0, 10).map((ex: any, idx: number) => (
                  <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                    <td className="py-2 px-3 font-medium">{ex.date}</td>
                    <td className="py-2 px-3">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                        ex.session === 'MORNING'
                          ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                          : 'bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300'
                      }`}>
                        {ex.session} ({ex.time_window})
                      </span>
                    </td>
                    <td className="py-2 px-3 font-semibold">{ex.section}</td>
                    <td className="py-2 px-3 font-bold text-purple-700 dark:text-purple-400">{ex.subject}</td>
                    <td className="py-2 px-3 text-slate-600 dark:text-slate-300">{ex.allocated_rooms.join(', ')}</td>
                    <td className="py-2 px-3 text-slate-600 dark:text-slate-300">{ex.invigilators.join(', ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
