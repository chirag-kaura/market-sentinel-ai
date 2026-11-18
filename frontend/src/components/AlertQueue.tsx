import React from 'react';
import { AlertSummary, PriorityLevel } from '../types';

interface AlertQueueProps {
  alerts: AlertSummary[];
  selectedAlertId?: string;
  onSelectAlert: (alertId: string) => void;
}

const priorityColors: Record<PriorityLevel, string> = {
  CRITICAL: 'bg-red-900 text-red-200 border-red-700',
  HIGH: 'bg-orange-900 text-orange-200 border-orange-700',
  MEDIUM: 'bg-yellow-900 text-yellow-200 border-yellow-700',
  LOW: 'bg-blue-900 text-blue-200 border-blue-700',
};

export const AlertQueue: React.FC<AlertQueueProps> = ({
  alerts,
  selectedAlertId,
  onSelectAlert,
}) => {
  return (
    <div className="flex flex-col h-full bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
      <div className="p-4 bg-slate-800/80 border-b border-slate-700 flex justify-between items-center">
        <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
          <span>Surveillance Alert Queue</span>
          <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-slate-700 text-slate-300">
            {alerts.length}
          </span>
        </h2>
      </div>

      <div className="overflow-y-auto divide-y divide-slate-800">
        {alerts.map((alert) => {
          const isSelected = alert.alert_id === selectedAlertId;
          return (
            <div
              key={alert.alert_id}
              onClick={() => onSelectAlert(alert.alert_id)}
              className={`p-4 cursor-pointer transition-colors ${
                isSelected ? 'bg-slate-800 border-l-4 border-l-blue-500' : 'hover:bg-slate-800/60'
              }`}
            >
              <div className="flex justify-between items-start mb-1">
                <div className="flex items-center gap-2">
                  <span className="text-base font-bold text-slate-100">{alert.ticker}</span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded border font-semibold ${
                      priorityColors[alert.priority_level]
                    }`}
                  >
                    {alert.priority_level}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-xs font-mono text-slate-400">Score</span>
                  <p className="text-sm font-bold text-red-400">{alert.composite_risk_score.toFixed(1)}</p>
                </div>
              </div>
              <p className="text-xs text-slate-300 line-clamp-2 mt-1">{alert.summary_explanation}</p>
              <div className="mt-2 text-[10px] text-slate-500 font-mono">
                {new Date(alert.event_timestamp).toLocaleTimeString()} · {alert.anomaly_category}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
