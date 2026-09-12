'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { Activity, AlertTriangle, CheckCircle2, RefreshCw, ShieldCheck, RotateCcw } from 'lucide-react';
import { getApiBaseUrl, getWsBaseUrl } from '@/lib/api';
import { DecisionTrace } from '@/components/agent/DecisionTrace';
import { MissionSimulator } from '@/components/agent/MissionSimulator';
import { DiffView } from '@/components/agent/DiffView';
import { MultiAgentSynthesisWorkspace } from '@/components/agent/MultiAgentSynthesisWorkspace';

type AgentEvent = {
  id: number;
  event_type: string;
  source: string;
  severity: string;
  room_code?: string;
  affected_sections?: string[];
  summary?: string;
  created_at?: string;
  payload?: any;
};

type AgentSession = {
  id: number;
  goal: string;
  status: string;
  current_step: string;
  priority: string[];
  summary?: string;
  context?: any;
  events?: AgentEvent[];
};

export default function AgentConsolePage() {
  const [session, setSession] = useState<AgentSession | null>(null);
  const [originalEntries, setOriginalEntries] = useState<any[]>([]);
  const [repairedEntries, setRepairedEntries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const apiBase = getApiBaseUrl();

  const loadSession = useCallback(async (sessionId?: number) => {
    if (sessionId) {
      const res = await fetch(`${apiBase}/api/v1/agent/sessions/${sessionId}`);
      if (!res.ok) {
        throw new Error('Unable to load agent session');
      }
      const data = await res.json();
      setSession(data);
      if (data.context?.candidate_entries) {
        setRepairedEntries(data.context.candidate_entries);
      }
      return data;
    }
    return null;
  }, [apiBase]);

  const createSession = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/agent/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          goal: 'Autonomous adaptive timetable scheduling & minimal disruption repair',
          priority: ['hard_constraints', 'minimal_disruption', 'final_year_priority'],
        }),
      });
      if (!res.ok) {
        throw new Error('Could not create agent session');
      }
      const sessionData = await res.json();
      setSession(sessionData);
      setError(null);

      // Load initial baseline entries for diff view
      const ttRes = await fetch(`${apiBase}/api/v1/timetable?version_id=5&section_name=ALL`);
      if (ttRes.ok) {
        const ttData = await ttRes.json();
        setOriginalEntries(ttData.entries || []);
      }

      return sessionData;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [apiBase]);

  const triggerScenario = async (scenarioType: string, targetCode?: string, affectedSections?: string[]) => {
    if (!session?.id) return;
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/agent/simulate/${scenarioType}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: session.id,
          target_code: targetCode,
          affected_sections: affectedSections || [],
        }),
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        const msg = errJson.detail || `Simulation failed for ${scenarioType}`;
        throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
      }
      const result = await res.json();
      if (result.repair_recommendation?.entries) {
        setRepairedEntries(result.repair_recommendation.entries);
      }
      const reloaded = await loadSession(session.id);
      setSession(reloaded ?? session);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Simulation request failed');
    } finally {
      setLoading(false);
    }
  };

  const observeState = async () => {
    if (!session?.id) return;
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/agent/sessions/${session.id}/observe`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Observe state failed');
      const reloaded = await loadSession(session.id);
      setSession(reloaded ?? session);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Observe state failed');
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
            ? 'Approved from agent console: minimal disruption repair confirmed.'
            : 'Rejected: rollback requested to preserve pre-disruption snapshot.',
        }),
      });
      if (!res.ok) throw new Error('Repair decision failed');
      const reloaded = await loadSession(session.id);
      setSession(reloaded ?? session);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Decision failed');
    } finally {
      setLoading(false);
    }
  };

  const validateRepair = async () => {
    if (!session?.id) return;
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/agent/sessions/${session.id}/repair-validation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_code: session.context?.last_room || '604',
          affected_sections: session.context?.affected_sections || [],
          check_type: 'full_constraint_validation',
        }),
      });
      if (!res.ok) throw new Error('Validation failed');
      const reloaded = await loadSession(session.id);
      setSession(reloaded ?? session);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Validation failed');
    } finally {
      setLoading(false);
    }
  };

  const executeRollback = async () => {
    if (!session?.id) return;
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/agent/sessions/${session.id}/rollback`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Rollback failed');
      setRepairedEntries([]);
      const reloaded = await loadSession(session.id);
      setSession(reloaded ?? session);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Rollback failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    createSession();
  }, [createSession]);

  useEffect(() => {
    if (!session?.id) return;
    const wsUrl = `${getWsBaseUrl()}/api/v1/agent/stream/${session.id}`;
    let socket: WebSocket | null = null;
    try {
      socket = new WebSocket(wsUrl);
      socket.onmessage = (evt) => {
        try {
          const data = JSON.parse(evt.data);
          if (data.type === 'AGENT_EVENT' || data.type === 'SESSION_UPDATE') {
            loadSession(session.id);
          }
        } catch {}
      };
    } catch {}

    return () => {
      if (socket) socket.close();
    };
  }, [session?.id, loadSession]);

  const eventList = (session?.events || []) as any[];

  return (
    <div className="space-y-6 w-full max-w-7xl mx-auto px-4 pb-16 font-sans">
      {/* Console Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pt-4 border-b border-slate-100 dark:border-slate-800 pb-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 text-xs font-bold border border-indigo-200 dark:border-indigo-800">
            <Activity className="w-3.5 h-3.5" />
            VFSTR Adaptive Academic Scheduling Agent
          </div>
          <h1 className="mt-2 text-2xl md:text-3xl font-black text-slate-900 dark:text-white">Agent Mission Console</h1>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            disabled={loading}
            onClick={() => createSession()}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 font-semibold text-xs hover:bg-slate-50 transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            New Mission Session
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={observeState}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-indigo-200 dark:border-indigo-800 bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 font-semibold text-xs hover:bg-indigo-100 transition-all"
          >
            <Activity className="w-3.5 h-3.5" />
            Observe State
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={executeRollback}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/50 text-red-600 dark:text-red-400 font-semibold text-xs hover:bg-red-100 transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            1-Click Rollback
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 dark:bg-red-950/40 p-4 text-xs font-semibold text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Autonomous Collaborative Multi-Agent Synthesis Section */}
      <MultiAgentSynthesisWorkspace
        versionId={12}
        onSynthesisComplete={(entries) => {
          if (entries && entries.length > 0) {
            setRepairedEntries(entries);
          }
        }}
      />

      {/* Disruption Simulator Section */}
      <MissionSimulator onTriggerScenario={triggerScenario} loading={loading} />

      {/* Main Grid Layout */}
      {session && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Decision Trace Log */}
          <div className="lg:col-span-2 space-y-6">
            <DecisionTrace events={eventList} currentStep={session.current_step} status={session.status} />
            {repairedEntries.length > 0 && (
              <DiffView
                originalEntries={originalEntries}
                repairedEntries={repairedEntries}
                stabilityScore={session.context?.repair_metrics?.stability_score || 95}
                movedCount={session.context?.repair_metrics?.moved_count || repairedEntries.length}
                displacedSections={session.context?.repair_metrics?.displaced_sections || []}
                onRollback={executeRollback}
                loading={loading}
              />
            )}
          </div>

          {/* Action & Approval Controls */}
          <div className="space-y-6">
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-bold text-slate-900 dark:text-white">Active Session Telemetry</h3>
                <span className="text-xs font-mono font-bold text-slate-400">#{session.id}</span>
              </div>

              <div className="space-y-2.5 text-xs">
                <div className="flex justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800">
                  <span className="text-slate-500">Current Step:</span>
                  <span className="font-bold text-indigo-600 dark:text-indigo-400 font-mono">{session.current_step.toUpperCase()}</span>
                </div>
                <div className="flex justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800">
                  <span className="text-slate-500">Session Status:</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400 font-mono">{session.status.toUpperCase()}</span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800">
                  <span className="text-slate-500 block mb-1">Active Summary:</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200 leading-relaxed block">{session.summary || 'Ready for disruption simulation.'}</span>
                </div>
              </div>
            </div>

            {/* Approval Workflow Box */}
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
              <div className="flex items-center gap-2 mb-3">
                <ShieldCheck className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                <h3 className="text-base font-bold text-slate-900 dark:text-white">Human Approval Gate</h3>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-4 leading-relaxed">
                High-impact local repairs require explicit human approval before schedule publication.
              </p>

              <div className="space-y-2">
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => decideRepair('approved')}
                  className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all shadow-sm flex items-center justify-center gap-2"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  Approve Local Repair
                </button>
                <button
                  type="button"
                  disabled={loading}
                  onClick={validateRepair}
                  className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-all shadow-sm flex items-center justify-center gap-2"
                >
                  <ShieldCheck className="w-4 h-4" />
                  Run Validation Gate Check
                </button>
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => decideRepair('rejected')}
                  className="w-full py-2.5 px-4 rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 text-xs font-bold hover:bg-red-100 transition-all flex items-center justify-center gap-2"
                >
                  <AlertTriangle className="w-4 h-4" />
                  Reject & Request Rollback
                </button>
                <Link
                  href="/schedule"
                  className="w-full block text-center py-2.5 px-4 rounded-xl border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 text-xs font-semibold hover:bg-slate-50 dark:hover:bg-slate-800 transition-all mt-2"
                >
                  View Full Timetable Grid &rarr;
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
