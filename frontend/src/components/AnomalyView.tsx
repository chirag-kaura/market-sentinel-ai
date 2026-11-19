import React, { useState } from 'react';
import { AlertSummary } from '../types';

interface AnomalyViewProps {
  alerts: AlertSummary[];
  onSelectSecurity: (symbol: string) => void;
}

export const AnomalyView: React.FC<AnomalyViewProps> = ({ alerts, onSelectSecurity }) => {
  const [methodFilter, setMethodFilter] = useState<'ALL' | 'VOLATILITY' | 'UNEXPLAINED'>('ALL');
  const [showModelDetails, setShowModelDetails] = useState(false);

  const filteredAlerts = alerts.filter((a) => {
    if (methodFilter === 'VOLATILITY') {
      return a.anomaly_category.toUpperCase().includes('VOLATILITY');
    }
    if (methodFilter === 'UNEXPLAINED') {
      return a.anomaly_category.toUpperCase().includes('UNEXPLAINED');
    }
    return true;
  });

  // Deduplicate top securities by highest composite_risk_score
  const topBySymbolMap = new Map<string, AlertSummary>();
  for (const a of filteredAlerts) {
    const existing = topBySymbolMap.get(a.ticker);
    if (!existing || a.composite_risk_score > existing.composite_risk_score) {
      topBySymbolMap.set(a.ticker, a);
    }
  }
  const topSecurities = Array.from(topBySymbolMap.values())
    .sort((a, b) => b.composite_risk_score - a.composite_risk_score)
    .slice(0, 6);

  const highConfidenceCount = filteredAlerts.filter((a) => a.composite_risk_score >= 43.0).length;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="text-[#50d5d0] text-[10px] tracking-widest uppercase font-bold">
            Machine learning signals
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Anomaly Detection
          </h1>
          <p className="text-xs text-[#91a0b5] mt-0.5">
            Explainable statistical and ML signals highlight observations that deviate from expected behaviour.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={methodFilter}
            onChange={(e) => setMethodFilter(e.target.value as 'ALL' | 'VOLATILITY' | 'UNEXPLAINED')}
            className="bg-[#0d1724] text-slate-200 border border-[#243247] rounded-lg px-3 py-1.5 text-xs outline-none"
          >
            <option value="ALL">All detection methods ({alerts.length})</option>
            <option value="VOLATILITY">Volatility Band Breach (EWMA ±3σ)</option>
            <option value="UNEXPLAINED">Unexplained Statistical/ML Anomaly</option>
          </select>
          <button
            onClick={() => setShowModelDetails((prev) => !prev)}
            className="border border-[#243247] bg-[#172437] hover:bg-[#1f314a] text-slate-200 px-3 py-1.5 rounded-lg text-xs transition"
          >
            {showModelDetails ? 'Hide model details' : 'Model details'}
          </button>
        </div>
      </div>

      {/* Collapsible Model Details Panel */}
      {showModelDetails && (
        <div className="bg-[#0d1724] border border-[#2d4563] rounded-xl p-4 text-xs text-slate-300 space-y-2 shadow-lg">
          <div className="flex justify-between items-center">
            <span className="font-bold text-[#50d5d0] uppercase tracking-wider text-[11px]">
              SurveillanceEnsembleEngine v1.0.0 — Architecture & Weights
            </span>
            <span className="text-[10px] text-[#91a0b5]">CPU-Optimized · Zero Look-Ahead (.shift(1))</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
            <div className="bg-[#131e2d] p-3 rounded-lg border border-[#243247]">
              <div className="font-semibold text-slate-100">1. Statistical Baseline (40%)</div>
              <div className="text-[11px] text-[#91a0b5] mt-1">
                Rolling 20-day return & volume Z-scores, empirical P95/P99 cutoffs, and delivery divergence.
              </div>
            </div>
            <div className="bg-[#131e2d] p-3 rounded-lg border border-[#243247]">
              <div className="font-semibold text-slate-100">2. Isolation Forest ML (40%)</div>
              <div className="text-[11px] text-[#91a0b5] mt-1">
                100 trees on 7 stationary clues (RobustScaler + sigmoid scoring + dynamic 98th quantile).
              </div>
            </div>
            <div className="bg-[#131e2d] p-3 rounded-lg border border-[#243247]">
              <div className="font-semibold text-slate-100">3. EWMA Volatility Fence (20%)</div>
              <div className="text-[11px] text-[#91a0b5] mt-1">
                RiskMetrics EWMA (λ=0.94) ±3σ dynamic price bands with GARCH(1,1) & GJR-GARCH support.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Signals detected</div>
          <div className="text-2xl font-bold tracking-tight text-slate-100 my-1">
            {filteredAlerts.length}
          </div>
          <div className="text-[10px] text-[#91a0b5]">Persisted in PostgreSQL 16</div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">High-confidence outliers</div>
          <div className="text-2xl font-bold tracking-tight text-[#ff777d] my-1">
            {String(highConfidenceCount).padStart(2, '0')}
          </div>
          <div className="text-[10px] text-[#91a0b5]">Composite risk score ≥ 43.0</div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Detection model</div>
          <div className="text-lg font-bold tracking-tight text-slate-100 my-1">Ensemble v1.0.0</div>
          <div className="text-[10px] text-[#91a0b5]">Stats (40%) + IForest (40%) + EWMA (20%)</div>
        </div>
      </div>

      {/* Signal Strength & Why Flagged */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
        {/* Signal strength by security */}
        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-xs font-semibold text-slate-100">Signal strength by security</h3>
            <span className="text-[10px] text-[#91a0b5]">Top composite risk scores</span>
          </div>

          <div className="space-y-3.5 pt-1">
            {topSecurities.map((item) => {
              const barColor =
                item.composite_risk_score >= 45
                  ? 'bg-[#ff777d]'
                  : item.composite_risk_score >= 42
                  ? 'bg-[#f4bd62]'
                  : 'bg-[#50d5d0]';
              return (
                <div
                  key={item.alert_id}
                  onClick={() => onSelectSecurity(item.ticker)}
                  className="grid grid-cols-[100px_1fr_42px] items-center gap-3 text-xs cursor-pointer hover:opacity-80"
                >
                  <span className="font-bold text-slate-100">{item.ticker}</span>
                  <div className="h-2 bg-[#26364a] rounded-full overflow-hidden">
                    <div
                      className={`h-full ${barColor}`}
                      style={{ width: `${Math.min(100, Math.round(item.composite_risk_score))}%` }}
                    ></div>
                  </div>
                  <b className="text-right text-slate-200">{item.composite_risk_score.toFixed(1)}</b>
                </div>
              );
            })}
          </div>
        </div>

        {/* Why Flagged / Feature Attribution */}
        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-xs font-semibold text-slate-100">Why flagged (Feature attribution)</h3>
            <span className="text-[10px] text-[#91a0b5]">Latest anomaly drivers</span>
          </div>

          <div className="space-y-2.5">
            {topSecurities.slice(0, 4).map((item) => (
              <div
                key={item.alert_id}
                onClick={() => onSelectSecurity(item.ticker)}
                className="bg-[#0d1724] border border-[#243247] hover:border-[#50d5d0] rounded-lg p-3 cursor-pointer transition"
              >
                <div className="flex justify-between items-center text-xs">
                  <span className="font-bold text-slate-100">
                    {item.ticker} · <span className="text-[#50d5d0]">{item.anomaly_category}</span>
                  </span>
                  <span className="text-[10px] text-[#91a0b5]">
                    {new Date(item.event_timestamp).toLocaleDateString()}
                  </span>
                </div>
                <p className="text-[11px] text-[#91a0b5] mt-1 leading-relaxed">
                  {item.summary_explanation}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
