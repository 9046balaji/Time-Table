'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Activity, AlertTriangle, RefreshCw, Radio, CheckCircle, ShieldAlert, Cpu } from 'lucide-react';
import { getApiBaseUrl } from '@/lib/api';

export const RoomTelemetryHeatmap: React.FC = () => {
  const [day, setDay] = useState('MON');
  const [period, setPeriod] = useState(3);
  const [telemetryAudit, setTelemetryAudit] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [reclaiming, setReclaiming] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const apiBase = getApiBaseUrl();

  const fetchTelemetry = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/agent/telemetry/audit?day=${day}&period=${period}&version_id=5`);
      if (res.ok) {
        const data = await res.json();
        setTelemetryAudit(data);
      }
    } catch {
    } finally {
      setLoading(false);
    }
  }, [apiBase, day, period]);

  useEffect(() => {
    fetchTelemetry();
  }, [fetchTelemetry]);

  const handleSimulateGhost = async (roomCode: string) => {
    try {
      await fetch(`${apiBase}/api/v1/agent/telemetry/occupancy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_code: roomCode,
          detected_headcount: 0,
          sensor_type: 'EDGE_VISION_CAMERA'
        })
      });
      fetchTelemetry();
    } catch {}
  };

  const handleReclaim = async (roomCode: string) => {
    setReclaiming(roomCode);
    try {
      const res = await fetch(`${apiBase}/api/v1/agent/telemetry/reclaim`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: 1,
          room_code: roomCode,
          day,
          period,
          purpose: 'Reclaimed for AI Lab Remedial Session'
        })
      });
      if (res.ok) {
        setMessage(`Successfully reclaimed room ${roomCode} for remedial classes!`);
        fetchTelemetry();
      }
    } catch {
    } finally {
      setReclaiming(null);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-400 rounded-lg">
            <Radio className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">SmartClass IoT Edge Telemetry & Ghost Booking Monitor</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Live classroom sensor fusion comparing real camera headcounts vs. timetable reservations.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={day}
            onChange={(e) => setDay(e.target.value)}
            className="text-xs px-2.5 py-1.5 border rounded-md dark:bg-slate-800 dark:border-slate-700"
          >
            {['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'].map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
          <select
            value={period}
            onChange={(e) => setPeriod(Number(e.target.value))}
            className="text-xs px-2.5 py-1.5 border rounded-md dark:bg-slate-800 dark:border-slate-700"
          >
            {[1, 2, 3, 4, 5, 6, 7, 8].map((p) => (
              <option key={p} value={p}>Period {p}</option>
            ))}
          </select>
          <button
            onClick={fetchTelemetry}
            disabled={loading}
            className="p-1.5 text-slate-600 hover:text-slate-900 dark:text-slate-400 border rounded-md"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {message && (
        <div className="p-3 mb-4 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 text-sm rounded-md border border-emerald-200 dark:border-emerald-800 flex items-center gap-2">
          <CheckCircle className="w-4 h-4" />
          {message}
        </div>
      )}

      {/* Ghost Bookings Alert Banner */}
      {telemetryAudit && telemetryAudit.ghost_bookings_detected > 0 && (
        <div className="p-4 mb-6 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800">
          <h3 className="text-sm font-bold text-amber-900 dark:text-amber-200 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-600" />
            {telemetryAudit.ghost_bookings_detected} Ghost Booking(s) Detected at {day} Period {period}!
          </h3>
          <p className="text-xs text-amber-700 dark:text-amber-400 mt-1">
            These rooms are reserved on the official schedule, but edge sensors confirmed &lt; 5 students 15 minutes past the bell.
          </p>
        </div>
      )}

      {/* Rooms Telemetry Grid */}
      {telemetryAudit && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {telemetryAudit.all_monitored_rooms.map((rm: any, idx: number) => {
            const isGhost = rm.anomaly_type === 'GHOST_BOOKING';
            const isOvercrowded = rm.anomaly_type === 'OVERCROWDING';

            return (
              <div
                key={idx}
                className={`p-3 rounded-lg border text-center transition-all ${
                  isGhost
                    ? 'border-red-400 bg-red-50/70 dark:bg-red-950/30 text-red-900 dark:text-red-200'
                    : isOvercrowded
                    ? 'border-purple-400 bg-purple-50/70 dark:bg-purple-950/30 text-purple-900 dark:text-purple-200'
                    : rm.is_occupied
                    ? 'border-slate-200 dark:border-slate-800 bg-blue-50/40 dark:bg-slate-800/40 text-slate-800 dark:text-slate-200'
                    : 'border-slate-100 dark:border-slate-800/50 bg-slate-50/30 dark:bg-slate-900/30 text-slate-400'
                }`}
              >
                <div className="font-bold text-sm">{rm.room_code}</div>
                <div className="text-[11px] font-medium my-1 truncate">
                  {rm.scheduled_subject || 'FREE'}
                </div>
                <div className="text-[10px] text-slate-500 dark:text-slate-400">
                  Headcount: <span className="font-bold text-slate-900 dark:text-white">{rm.detected_headcount}</span> / {rm.room_capacity}
                </div>

                {isGhost && (
                  <button
                    onClick={() => handleReclaim(rm.room_code)}
                    disabled={reclaiming === rm.room_code}
                    className="mt-2 w-full py-1 px-2 bg-red-600 hover:bg-red-700 text-white rounded text-[10px] font-bold transition-colors"
                  >
                    {reclaiming === rm.room_code ? 'Reclaiming...' : 'Reclaim Room'}
                  </button>
                )}

                {!isGhost && rm.is_occupied && (
                  <button
                    onClick={() => handleSimulateGhost(rm.room_code)}
                    className="mt-2 w-full py-0.5 px-1.5 bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded text-[9px]"
                  >
                    Test Ghost
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
