import React, { useState } from 'react';
import { AlertSummary } from '../types';

interface AlertCentreViewProps {
  alerts: AlertSummary[];
  selectedAlertId: string | null;
  onSelectAlert: (alertId: string) => void;
  onOpenInvestigation: () => void;
}

export const AlertCentreView: React.FC<AlertCentreViewProps> = ({
  alerts,
  selectedAlertId,
  onSelectAlert,
  onOpenInvestigation,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const filteredAlerts = alerts.filter((a) => {
    const matchSearch =
      a.alert_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.ticker.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.anomaly_category.toLowerCase().includes(searchTerm.toLowerCase());
    const matchPriority = priorityFilter ? a.priority_level === priorityFilter : true;
    return matchSearch && matchPriority;
  });

  const highCount = alerts.filter(
    (a) => a.priority_level === 'CRITICAL' || a.priority_level === 'HIGH'
  ).length;
  const mediumCount = alerts.filter((a) => a.priority_level === 'MEDIUM').length;
  const lowCount = alerts.filter((a) => a.priority_level === 'LOW').length;

  const handleExportCsv = () => {
    const headers = ['alert_id', 'ticker', 'priority_level', 'composite_risk_score', 'anomaly_category', 'event_timestamp', 'summary_explanation'];
    const rows = filteredAlerts.map((a) => [
      a.alert_id,
      a.ticker,
      a.priority_level,
      a.composite_risk_score.toFixed(2),
      a.anomaly_category,
      a.event_timestamp,
      `"${(a.summary_explanation || '').replace(/"/g, '""')}"`,
    ]);
    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `market_sentinel_alerts_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="text-[#50d5d0] text-[10px] tracking-widest uppercase font-bold">
            Triage & prioritisation
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Alert Centre
          </h1>
          <p className="text-xs text-[#91a0b5] mt-0.5">
            Review, filter and route surveillance alerts for analyst investigation.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCsv}
            className="border border-[#243247] bg-[#172437] hover:bg-[#1f314a] text-slate-200 px-3 py-1.5 rounded-lg text-xs transition"
          >
            Export current view ({filteredAlerts.length})
          </button>
          <button
            onClick={onOpenInvestigation}
            className="border border-[#269b96] bg-[#1b7776] hover:bg-[#208887] text-white font-semibold px-3 py-1.5 rounded-lg text-xs transition"
          >
            Open selected alert →
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">All alerts</div>
          <div className="text-2xl font-bold tracking-tight text-slate-100 my-1">
            {alerts.length}
          </div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">High / Critical</div>
          <div className="text-2xl font-bold tracking-tight text-[#ff777d] my-1">
            {highCount}
          </div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Medium priority</div>
          <div className="text-2xl font-bold tracking-tight text-[#f4bd62] my-1">
            {String(mediumCount).padStart(2, '0')}
          </div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Low priority</div>
          <div className="text-2xl font-bold tracking-tight text-slate-100 my-1">
            {String(lowCount).padStart(2, '0')}
          </div>
        </div>
      </div>

      {/* Alert Table */}
      <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
        {/* Filters */}
        <div className="flex flex-wrap gap-2.5 mb-4">
          <input
            type="text"
            placeholder="Search alert / symbol…"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-[#0d1724] text-slate-100 border border-[#243247] rounded-lg px-3 py-1.5 text-xs outline-none min-w-[200px]"
          />
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="bg-[#0d1724] text-slate-100 border border-[#243247] rounded-lg px-3 py-1.5 text-xs outline-none"
          >
            <option value="">All priorities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-[#0d1724] text-slate-100 border border-[#243247] rounded-lg px-3 py-1.5 text-xs outline-none"
          >
            <option value="">All statuses</option>
            <option value="New">New</option>
            <option value="Under review">Under review</option>
            <option value="Escalated">Escalated</option>
            <option value="Closed">Closed</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs whitespace-nowrap">
            <thead>
              <tr className="border-b border-[#243247] text-[10px] uppercase text-[#8293a9]">
                <th className="py-2.5 px-3 w-6"></th>
                <th className="py-2.5 px-3">Alert ID</th>
                <th className="py-2.5 px-3">Time</th>
                <th className="py-2.5 px-3">Security</th>
                <th className="py-2.5 px-3">Trigger</th>
                <th className="py-2.5 px-3">Score</th>
                <th className="py-2.5 px-3">Priority</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Owner</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#202d3d]">
              {filteredAlerts.map((a) => {
                const isSelected = selectedAlertId === a.alert_id;
                return (
                  <tr
                    key={a.alert_id}
                    onClick={() => onSelectAlert(a.alert_id)}
                    className={`cursor-pointer transition text-[#d2dce9] ${
                      isSelected ? 'bg-[#1a2b40]' : 'hover:bg-[#172437]'
                    }`}
                  >
                    <td className="py-2.5 px-3 text-[#50d5d0]">
                      {isSelected ? '◉' : '○'}
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-slate-100">
                      {a.alert_id}
                    </td>
                    <td className="py-2.5 px-3 text-[#91a0b5]">
                      {new Date(a.event_timestamp).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="py-2.5 px-3 font-bold text-slate-100">{a.ticker}</td>
                    <td className="py-2.5 px-3">{a.anomaly_category}</td>
                    <td className="py-2.5 px-3 font-bold">{Math.round(a.composite_risk_score)}</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${
                          a.priority_level === 'CRITICAL' || a.priority_level === 'HIGH'
                            ? 'bg-[#49262d] text-[#ff9ca1]'
                            : a.priority_level === 'MEDIUM'
                            ? 'bg-[#49391f] text-[#ffd18a]'
                            : 'bg-[#173b39] text-[#81e2c4]'
                        }`}
                      >
                        {a.priority_level}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-[#91a0b5]">New</td>
                    <td className="py-2.5 px-3 text-[#91a0b5]">Unassigned</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="text-[10px] text-[#91a0b5] mt-3 pt-2 border-t border-[#202d3d]">
          Select an alert row to load its detailed evidence in the investigation workspace.
        </div>
      </div>
    </div>
  );
};
