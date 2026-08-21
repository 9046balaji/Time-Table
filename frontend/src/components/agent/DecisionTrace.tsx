import React from 'react';

export interface DecisionTraceEvent {
  id: number;
  event_type: string;
  source: string;
  severity: string;
  room_code?: string;
  affected_sections: string[];
  summary: string;
  created_at: string;
  payload?: any;
}

interface DecisionTraceProps {
  events: DecisionTraceEvent[];
  currentStep: string;
  status: string;
}

export const DecisionTrace: React.FC<DecisionTraceProps> = ({ events, currentStep, status }) => {
  const getBadgeColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high':
        return 'bg-red-500/10 text-red-600 border-red-500/20';
      case 'medium':
        return 'bg-amber-500/10 text-amber-600 border-amber-500/20';
      default:
        return 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20';
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">Agent Decision Trace</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">Structured audit feed & execution step telemetry</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 font-semibold border border-indigo-200 dark:border-indigo-800">
            Step: {currentStep.toUpperCase()}
          </span>
          <span className={`text-xs font-mono px-3 py-1 rounded-full font-semibold border ${status === 'active' ? 'bg-emerald-50 text-emerald-600 border-emerald-200' : 'bg-amber-50 text-amber-600 border-amber-200'}`}>
            {status.toUpperCase()}
          </span>
        </div>
      </div>

      <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
        {events.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-sm">No agent events logged yet. Trigger a scenario to start.</div>
        ) : (
          events.map((evt) => (
            <div key={evt.id} className="p-3.5 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-850 flex flex-col gap-1.5 transition-all hover:border-slate-300">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-800 dark:text-slate-200">{evt.event_type}</span>
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${getBadgeColor(evt.severity)}`}>
                    {evt.severity.toUpperCase()}
                  </span>
                </div>
                <span className="text-[11px] font-mono text-slate-400">{evt.created_at ? new Date(evt.created_at).toLocaleTimeString() : 'Just now'}</span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">{evt.summary}</p>

              {evt.affected_sections && evt.affected_sections.length > 0 && (
                <div className="flex flex-wrap items-center gap-1 mt-1">
                  <span className="text-[10px] font-semibold text-slate-400">Impacted:</span>
                  {evt.affected_sections.map((sec, idx) => (
                    <span key={idx} className="text-[10px] bg-slate-200/60 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-1.5 py-0.5 rounded font-mono">
                      {sec}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
