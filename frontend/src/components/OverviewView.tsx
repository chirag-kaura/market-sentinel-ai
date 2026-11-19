import React from 'react';
import { AlertSummary } from '../types';

interface OverviewViewProps {
  alerts: AlertSummary[];
  watchlistCount?: number;
  openInvestigationsCount?: number;
  onNavigateToAlerts: () => void;
  onSelectAlert: (alertId: string) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  alerts,
  watchlistCount = 15,
  openInvestigationsCount = 0,
  onNavigateToAlerts,
  onSelectAlert,
}) => {
  const highPriorityCount = alerts.filter(
    (a) => a.priority_level === 'CRITICAL' || a.priority_level === 'HIGH'
  ).length;
  const mediumPriorityCount = alerts.filter(
    (a) => a.priority_level === 'MEDIUM'
  ).length;
  const lowPriorityCount = alerts.filter(
    (a) => a.priority_level === 'LOW'
  ).length;

  const totalAlerts = Math.max(1, alerts.length);
  const highPct = Math.round((highPriorityCount / totalAlerts) * 100);
  const medPct = Math.round((mediumPriorityCount / totalAlerts) * 100);
  const lowPct = Math.round((lowPriorityCount / totalAlerts) * 100);
  const uniqueSecuritiesWithAlerts = new Set(alerts.map((a) => a.ticker)).size;

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="text-[#50d5d0] text-[10px] tracking-widest uppercase font-bold">
            Command centre
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Executive Overview
          </h1>
          <p className="text-xs text-[#91a0b5] mt-0.5">
            A consolidated view of market activity, emerging risks and analyst workload.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select className="bg-[#0d1724] text-slate-200 border border-[#243247] rounded-lg px-3 py-1.5 text-xs outline-none">
            <option>NSE · Active Monitored Universe</option>
            <option>Watchlist · Large Cap 50</option>
          </select>
          <button
            onClick={() => window.location.reload()}
            className="border border-[#243247] bg-[#172437] hover:bg-[#1f314a] text-slate-200 px-3 py-1.5 rounded-lg text-xs transition"
          >
            ↻ Refresh view
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Securities monitored</div>
          <div className="text-2xl font-bold tracking-tight text-slate-100 my-1">
            {watchlistCount}
          </div>
          <div className="text-[10px] text-[#91a0b5]">
            <span className="text-[#65d6a4] font-medium">Top {watchlistCount} NSE</span> · PostgreSQL 16
          </div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Alerts in queue</div>
          <div className="text-2xl font-bold tracking-tight text-slate-100 my-1">
            {alerts.length}
          </div>
          <div className="text-[10px] text-[#91a0b5]">
            <span className="text-[#ff777d] font-medium">{highPriorityCount} high/critical</span> · {mediumPriorityCount} medium
          </div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Unusual activity signals</div>
          <div className="text-2xl font-bold tracking-tight text-[#f4bd62] my-1">
            {alerts.length}
          </div>
          <div className="text-[10px] text-[#91a0b5]">
            Across {uniqueSecuritiesWithAlerts} securities
          </div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Audit dispositions</div>
          <div className="text-2xl font-bold tracking-tight text-slate-100 my-1">
            {String(openInvestigationsCount).padStart(2, '0')}
          </div>
          <div className="text-[10px] text-[#91a0b5]">
            <span className="text-[#65d6a4] font-medium">Live DB</span> · persisted trail
          </div>
        </div>
      </div>

      {/* Main Charts & Risk Distribution Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3.5">
        {/* Intraday Index Chart */}
        <div className="lg:col-span-2 bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-xs font-semibold text-slate-100">
              Market activity · monitored universe
            </h3>
            <span className="text-[10px] text-[#91a0b5]">Real-time aggregated index</span>
          </div>

          <svg className="h-52 w-full block" viewBox="0 0 700 220" preserveAspectRatio="none">
            <defs>
              <linearGradient id="overviewArea" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0" stopColor="#50d5d0" stopOpacity="0.25" />
                <stop offset="1" stopColor="#50d5d0" stopOpacity="0" />
              </linearGradient>
            </defs>
            <g stroke="#26364a" strokeDasharray="3 5">
              <path d="M0 35H700M0 85H700M0 135H700M0 185H700" />
            </g>
            <path
              d="M0 151 L35 143 70 155 105 119 140 130 175 105 210 118 245 82 280 95 315 72 350 89 385 60 420 75 455 49 490 68 525 55 560 79 595 48 630 58 665 31 700 43 L700 210 L0 210Z"
              fill="url(#overviewArea)"
            />
            <path
              d="M0 151 L35 143 70 155 105 119 140 130 175 105 210 118 245 82 280 95 315 72 350 89 385 60 420 75 455 49 490 68 525 55 560 79 595 48 630 58 665 31 700 43"
              fill="none"
              stroke="#55d5cd"
              strokeWidth="2.5"
            />
            <path d="M0 170 L700 170" stroke="#f2bd65" strokeDasharray="5 5" opacity="0.7" />
          </svg>

          <div className="flex justify-between text-[#71839a] text-[9px] mt-1">
            <span>09:15</span>
            <span>10:00</span>
            <span>11:00</span>
            <span>12:00</span>
            <span>13:00</span>
            <span>14:00</span>
            <span>15:30</span>
          </div>

          <div className="flex gap-4 text-[#91a0b5] text-[10px] mt-2">
            <span className="flex items-center gap-1.5">
              <i className="w-2 h-2 rounded-full bg-[#55d5cd]"></i>
              Intraday activity movement
            </span>
            <span className="flex items-center gap-1.5">
              <i className="w-2 h-2 rounded-full bg-[#f2bd65]"></i>
              Historical baseline
            </span>
          </div>
        </div>

        {/* Risk Distribution & Top Signals */}
        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-xs font-semibold text-slate-100">Risk distribution</h3>
              <span className="text-[10px] text-[#91a0b5]">Today's active signals</span>
            </div>

            <div className="space-y-3">
              <div className="grid grid-cols-[80px_1fr_28px] items-center gap-2 text-[10px] text-[#91a0b5]">
                <span>High / Critical</span>
                <div className="h-1.5 bg-[#26364a] rounded-full overflow-hidden">
                  <div className="h-full bg-[#ff777d]" style={{ width: `${highPct}%` }}></div>
                </div>
                <b className="text-right text-slate-200">{String(highPriorityCount).padStart(2, '0')}</b>
              </div>

              <div className="grid grid-cols-[80px_1fr_28px] items-center gap-2 text-[10px] text-[#91a0b5]">
                <span>Medium</span>
                <div className="h-1.5 bg-[#26364a] rounded-full overflow-hidden">
                  <div className="h-full bg-[#f4bd62]" style={{ width: `${medPct}%` }}></div>
                </div>
                <b className="text-right text-slate-200">{String(mediumPriorityCount).padStart(2, '0')}</b>
              </div>

              <div className="grid grid-cols-[80px_1fr_28px] items-center gap-2 text-[10px] text-[#91a0b5]">
                <span>Low</span>
                <div className="h-1.5 bg-[#26364a] rounded-full overflow-hidden">
                  <div className="h-full bg-[#65d6a4]" style={{ width: `${lowPct}%` }}></div>
                </div>
                <b className="text-right text-slate-200">{String(lowPriorityCount).padStart(2, '0')}</b>
              </div>
            </div>

            <div className="flex justify-between items-center mt-6 mb-2">
              <h3 className="text-xs font-semibold text-slate-100">Top signals</h3>
              <span className="text-[10px] text-[#91a0b5]">By composite score</span>
            </div>

            <div className="divide-y divide-[#202d3d]">
              {alerts.slice(0, 3).map((a) => (
                <div
                  key={a.alert_id}
                  onClick={() => onSelectAlert(a.alert_id)}
                  className="py-2.5 flex justify-between items-center cursor-pointer hover:bg-[#172437] px-1 rounded transition"
                >
                  <div>
                    <strong className="text-xs text-slate-100">{a.ticker}</strong>
                    <p className="text-[10px] text-[#91a0b5] truncate max-w-[170px]">
                      {a.anomaly_category}
                    </p>
                  </div>
                  <span
                    className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${
                      a.priority_level === 'CRITICAL' || a.priority_level === 'HIGH'
                        ? 'bg-[#49262d] text-[#ff9ca1]'
                        : 'bg-[#49391f] text-[#ffd18a]'
                    }`}
                  >
                    {Math.round(a.composite_risk_score)} · {a.priority_level}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Priority Alerts Table */}
      <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-xs font-semibold text-slate-100">
            Priority alerts requiring attention
          </h3>
          <button
            onClick={onNavigateToAlerts}
            className="text-xs text-[#50d5d0] hover:underline font-medium"
          >
            Open alert centre →
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs whitespace-nowrap">
            <thead>
              <tr className="border-b border-[#243247] text-[10px] uppercase text-[#8293a9]">
                <th className="py-2.5 px-3">Time</th>
                <th className="py-2.5 px-3">Security</th>
                <th className="py-2.5 px-3">Signal</th>
                <th className="py-2.5 px-3">Risk score</th>
                <th className="py-2.5 px-3">Priority</th>
                <th className="py-2.5 px-3">Workflow</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#202d3d]">
              {alerts.slice(0, 5).map((a) => (
                <tr
                  key={a.alert_id}
                  onClick={() => onSelectAlert(a.alert_id)}
                  className="hover:bg-[#172437] cursor-pointer transition text-[#d2dce9]"
                >
                  <td className="py-2.5 px-3 text-[#91a0b5]">
                    {new Date(a.event_timestamp).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </td>
                  <td className="py-2.5 px-3 font-bold text-slate-100">{a.ticker}</td>
                  <td className="py-2.5 px-3">{a.anomaly_category}</td>
                  <td className="py-2.5 px-3 font-semibold">
                    {a.composite_risk_score.toFixed(1)} / 100
                  </td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${
                        a.priority_level === 'CRITICAL' || a.priority_level === 'HIGH'
                          ? 'bg-[#49262d] text-[#ff9ca1]'
                          : 'bg-[#49391f] text-[#ffd18a]'
                      }`}
                    >
                      {a.priority_level}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-[#91a0b5]">New</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
