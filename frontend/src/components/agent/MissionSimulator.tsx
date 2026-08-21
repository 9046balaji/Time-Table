import React from 'react';

interface MissionSimulatorProps {
  onTriggerScenario: (scenarioType: string, targetCode?: string, affectedSections?: string[]) => Promise<void>;
  loading: boolean;
}

export const MissionSimulator: React.FC<MissionSimulatorProps> = ({ onTriggerScenario, loading }) => {
  const scenarios = [
    {
      id: 'room_failure',
      name: 'Room Failure',
      target: '604',
      sections: ['III AIML-A', 'III AIML-B'],
      desc: 'Simulate emergency maintenance in Lab 604.',
      icon: '🔴',
      color: 'bg-red-50 hover:bg-red-100 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800'
    },
    {
      id: 'gpu_lab_failure',
      name: 'M7 GPU Lab Outage',
      target: 'AFTF-12',
      sections: ['IV AIML-A', 'IV AIML-B'],
      desc: 'Simulate High-Performance GPU Lab hardware failure.',
      icon: '💻',
      color: 'bg-rose-50 hover:bg-rose-100 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800'
    },
    {
      id: 'faculty_absence',
      name: 'Faculty Absence',
      target: 'Dr. S. Srikantha Reddy',
      sections: ['II AIML-A'],
      desc: 'Report unplanned instructor absence for the day.',
      icon: '👤',
      color: 'bg-amber-50 hover:bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800'
    },
    {
      id: 'capacity_surge',
      name: 'Capacity Surge',
      target: '601',
      sections: ['II AIML-C'],
      desc: 'Simulate section size surge exceeding venue capacity.',
      icon: '📈',
      color: 'bg-purple-50 hover:bg-purple-100 text-purple-700 border-purple-200 dark:bg-purple-950/40 dark:text-purple-300 dark:border-purple-800'
    },
    {
      id: 'priority_reroute',
      name: 'Priority Reroute',
      target: 'IV AIML-A',
      sections: ['IV AIML-A'],
      desc: 'Grant morning slot priority to 4th Year cohort.',
      icon: '⚡',
      color: 'bg-blue-50 hover:bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-800'
    },
    {
      id: 'constraint_adjustment',
      name: 'Constraint Shift',
      target: 'HC-08',
      sections: ['ALL'],
      desc: 'Enforce strict lab consecutiveness rules.',
      icon: '⚙️',
      color: 'bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800'
    }
  ];

  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm font-sans">
      <div className="mb-4">
        <h2 className="text-lg font-bold text-slate-900 dark:text-white">Campus Disruption Simulator</h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">Trigger real-world events to evaluate agent perception & local repair speed</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
        {scenarios.map((sc) => (
          <button
            key={sc.id}
            type="button"
            disabled={loading}
            onClick={() => onTriggerScenario(sc.id, sc.target, sc.sections)}
            className={`p-3.5 rounded-xl border text-left flex flex-col justify-between transition-all ${sc.color} ${loading ? 'opacity-50 cursor-not-allowed' : 'hover:scale-[1.02]'}`}
          >
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-base">{sc.icon}</span>
                <span className="font-bold text-xs">{sc.name}</span>
              </div>
              <p className="text-[11px] opacity-80 leading-snug">{sc.desc}</p>
            </div>
            <div className="mt-3 pt-2 border-t border-current/10 flex items-center justify-between text-[10px] font-mono font-semibold">
              <span>Target: {sc.target}</span>
              <span>Trigger &rarr;</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
