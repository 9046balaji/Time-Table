'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Activity, AlertTriangle, CheckCircle2, RefreshCw, ShieldCheck } from 'lucide-react';
import { getApiBaseUrl } from '@/lib/api';

type AgentEvent = {
  id: number;
  event_type: string;
  source: string;
  severity: string;
  room_code?: string;
  affected_sections?: string[];
  summary?: string;
  created_at?: string;
};

type AgentSession = {
  id: number;
  goal: string;
  status: string;
  current_step: string;
  priority: string[];
  summary?: string;
  events?: AgentEvent[];
};

export default function AgentConsolePage() {
  const [session, setSession] = useState<AgentSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const apiBase = getApiBaseUrl();

  const loadSession = async (sessionId?: number) => {
    if (sessionId) {
      const res = await fetch(`${apiBase}/api/v1/agent/sessions/${sessionId}`);
      if (!res.ok) {
        throw new Error('Unable to load agent session');
      }
      const data = await res.json();
      setSession(data);
      return data;
    }
    return null;
  };

  const createSession = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/agent/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          goal: 'Repair timetable after room outage',
          priority: ['final_year', 'hard_constraints', 'minimal_disruption'],
        }),
      });
      if (!res.ok) {
        throw new Error('Could not create agent session');
      }
      const sessionData = await res.json();
      setSession(sessionData);
      setError(null);
      return sessionData;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const triggerRoomFailure = async () => {
    if (!session?.id) return;
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/agent/simulate-room-failure`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: session.id,
          room_code: 'AFTF-12',
          severity: 'high',
          affected_sections: ['III AIML-A', 'III AIML-B', 'III AIML-C'],
        }),
      });
      if (!res.ok) {
        throw new Error('Room failure simulation failed');
      }
      const event = await res.json();
      const reloaded = await loadSession(session.id);
      setSession(reloaded ?? session);
      setError(null);
      return event;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Room failure simulation failed');
    } finally {
      setLoading(false);
    }
  };

  const recommendLocalRepair = async () => {
    if (!session?.id) return;
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/agent/sessions/${session.id}/repair-suggestion`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_code: 'AFTF-12',
          affected_sections: ['III AIML-A', 'III AIML-B', 'III AIML-C'],
          proposed_room: '604',
          risk_level: 'medium',
          reason: 'Shift the impacted labs to the nearest compatible room block and freeze unaffected slots.',
        }),
      });
      if (!res.ok) {
        throw new Error('Repair recommendation failed');
      }
      const result = await res.json();
      const reloaded = await loadSession(session.id);
      setSession(reloaded ?? session);
      setError(null);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Repair recommendation failed');
    } finally {
      setLoading(false);
    }
  };

  const decideRepair = async (decision: 'approved' | 'rejected') => {
    if (!session?.id) return;
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/agent/sessions/${session.id}/repair-decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision,
          rationale: decision === 'approved'
            ? 'Approved from the agent console to maintain continuity without changing unrelated sections.'
            : 'Rejected to keep the current timetable stable until a lower-risk repair is identified.',
        }),
      });
      if (!res.ok) {
        throw new Error('Repair decision failed');
      }
      const result = await res.json();
      const reloaded = await loadSession(session.id);
      setSession(reloaded ?? session);
      setError(null);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Repair decision failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    createSession();
  }, []);

  const eventList = session?.events ?? [];

  return (
    <div className="space-y-6 w-full max-w-6xl mx-auto px-2 pb-12">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-[11px] font-bold border border-blue-200">
            <Activity className="w-3.5 h-3.5" />
            Adaptive Scheduling Agent
          </div>
          <h1 className="mt-3 text-2xl md:text-3xl font-black text-slate-900">Agent Console</h1>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => createSession()}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-700 font-semibold"
          >
            <RefreshCw className="w-4 h-4" />
            New mission
          </button>
          <button
            type="button"
            onClick={triggerRoomFailure}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 text-white font-semibold shadow-sm"
          >
            <AlertTriangle className="w-4 h-4" />
            Simulate room failure
          </button>
        </div>
      </div>

      {error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      ) : null}

      {loading && !session ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500">Starting agent session...</div>
      ) : null}

      {session ? (
        <div className="grid grid-cols-1 xl:grid-cols-[1.5fr_1fr] gap-6">
          <div className="space-y-6">
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-400">Current mission</p>
                  <h2 className="mt-2 text-xl font-extrabold text-slate-900">{session.goal}</h2>
                </div>
                <div className="inline-flex items-center gap-2 rounded-full bg-emerald-50 border border-emerald-200 px-3 py-1.5 text-xs font-bold text-emerald-700">
                  <ShieldCheck className="w-4 h-4" />
                  {session.status}
                </div>
              </div>

              <div className="mt-5 grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm text-slate-600">
                <div className="rounded-xl bg-slate-50 border border-slate-200 p-3">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-slate-400">Step</div>
                  <div className="mt-1 font-bold text-slate-900">{session.current_step}</div>
                </div>
                <div className="rounded-xl bg-slate-50 border border-slate-200 p-3">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-slate-400">Priority</div>
                  <div className="mt-1 font-bold text-slate-900">{session.priority.join(', ') || 'default'}</div>
                </div>
                <div className="rounded-xl bg-slate-50 border border-slate-200 p-3">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-slate-400">Session</div>
                  <div className="mt-1 font-bold text-slate-900">#{session.id}</div>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-extrabold text-slate-900">Decision trace</h3>
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              </div>
              <div className="mt-4 space-y-3">
                {eventList.length ? (
                  eventList.map((event) => (
                    <div key={event.id} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-bold text-slate-900">{event.event_type}</span>
                        <span className="text-[10px] uppercase tracking-[0.18em] text-slate-500">{event.severity}</span>
                      </div>
                      <p className="mt-2 text-sm text-slate-600">{event.summary}</p>
                      {event.room_code ? (
                        <p className="mt-2 text-xs text-slate-500">Room: {event.room_code}</p>
                      ) : null}
                      {event.affected_sections?.length ? (
                        <p className="mt-1 text-xs text-slate-500">
                          Affected sections: {event.affected_sections.join(', ')}
                        </p>
                      ) : null}
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-slate-500">No events yet. Trigger a mission to begin.</p>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="text-base font-extrabold text-slate-900">Mission status</h3>
              <div className="mt-4 space-y-3 text-sm">
                <div className="flex items-center justify-between rounded-xl bg-slate-50 p-3">
                  <span className="text-slate-500">Status</span>
                  <span className="font-bold text-slate-900">{session.status}</span>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-slate-50 p-3">
                  <span className="text-slate-500">Current step</span>
                  <span className="font-bold text-slate-900">{session.current_step}</span>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-slate-50 p-3">
                  <span className="text-slate-500">Summary</span>
                  <span className="font-bold text-slate-900 text-right max-w-[60%]">{session.summary || 'No summary yet'}</span>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-2 text-base font-extrabold text-slate-900">
                <AlertTriangle className="w-5 h-5 text-amber-600" />
                Mission simulator
              </div>
              <p className="mt-3 text-sm text-slate-600">
                The agent will capture the incident, classify it, and recommend a repair strategy.
              </p>
              <div className="mt-4 grid gap-2">
                <button
                  type="button"
                  onClick={triggerRoomFailure}
                  className="w-full rounded-xl bg-amber-500 text-white font-semibold px-4 py-2.5"
                >
                  Room unavailable
                </button>
                <button
                  type="button"
                  onClick={recommendLocalRepair}
                  className="w-full rounded-xl bg-blue-600 text-white font-semibold px-4 py-2.5"
                >
                  Recommend local repair
                </button>
                <button
                  type="button"
                  onClick={() => decideRepair('approved')}
                  className="w-full rounded-xl bg-emerald-600 text-white font-semibold px-4 py-2.5"
                >
                  Approve repair
                </button>
                <button
                  type="button"
                  onClick={() => decideRepair('rejected')}
                  className="w-full rounded-xl border border-red-200 bg-red-50 text-red-700 font-semibold px-4 py-2.5"
                >
                  Reject repair
                </button>
                <Link
                  href="/schedule"
                  className="w-full rounded-xl border border-slate-200 text-slate-700 font-semibold px-4 py-2.5 text-center"
                >
                  View timetable
                </Link>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
