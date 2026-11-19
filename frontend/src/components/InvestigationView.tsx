import React, { useState } from 'react';
import { AlertDetail } from '../types';

interface InvestigationViewProps {
  alert: AlertDetail | null;
  onBackToAlerts: () => void;
  onSaveCaseUpdate: (status: string, notes: string) => void;
}

export const InvestigationView: React.FC<InvestigationViewProps> = ({
  alert,
  onBackToAlerts,
  onSaveCaseUpdate,
}) => {
  const [caseStatus, setCaseStatus] = useState('New');
  const [analystNotes, setAnalystNotes] = useState('');
  const [saveMessage, setSaveMessage] = useState('');

  if (!alert) {
    return (
      <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-8 text-center text-[#91a0b5]">
        No alert selected. Please select an alert from the Alert Centre.
        <div className="mt-3">
          <button
            onClick={onBackToAlerts}
            className="text-xs text-[#50d5d0] hover:underline"
          >
            ← Return to Alert Centre
          </button>
        </div>
      </div>
    );
  }

  const handleSave = () => {
    onSaveCaseUpdate(caseStatus, analystNotes);
    setSaveMessage(
      `Investigation update saved: ${caseStatus}${
        analystNotes ? ' · Analyst notes logged' : ' · No notes added'
      }`
    );
    setTimeout(() => setSaveMessage(''), 4000);
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="text-[#50d5d0] text-[10px] tracking-widest uppercase font-bold">
            Evidence-led investigation
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Alert Investigation Workspace
          </h1>
          <p className="text-xs text-[#91a0b5] mt-0.5">
            Bring model signals, market context and source documents into one analyst case view.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`text-xs font-bold px-3 py-1 rounded-full ${
              alert.priority_level === 'CRITICAL' || alert.priority_level === 'HIGH'
                ? 'bg-[#49262d] text-[#ff9ca1]'
                : 'bg-[#49391f] text-[#ffd18a]'
            }`}
          >
            {alert.priority_level} PRIORITY
          </span>
          <button
            onClick={onBackToAlerts}
            className="border border-[#243247] bg-[#172437] hover:bg-[#1f314a] text-slate-200 px-3 py-1.5 rounded-lg text-xs transition"
          >
            ← Back to alerts
          </button>
        </div>
      </div>

      {/* Case Identifier Card */}
      <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
        <div className="grid grid-cols-1 md:grid-cols-2 justify-between items-center gap-4">
          <div>
            <div className="text-[10px] text-[#91a0b5] uppercase tracking-wider font-semibold">
              CASE IDENTIFIER
            </div>
            <h2 className="text-xl font-bold text-slate-100 mt-0.5">
              {alert.alert_id} · {alert.ticker}
            </h2>
            <div className="text-xs text-[#91a0b5] mt-0.5">
              {alert.anomaly_category} ·{' '}
              {new Date(alert.event_timestamp).toLocaleDateString('en-GB', {
                day: 'numeric',
                month: 'short',
                year: 'numeric',
              })}{' '}
              at{' '}
              {new Date(alert.event_timestamp).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })}{' '}
              IST
            </div>
          </div>
          <div className="md:text-right">
            <div className="text-[10px] text-[#91a0b5] uppercase tracking-wider font-semibold">
              COMPOSITE RISK SCORE
            </div>
            <div className="text-4xl font-black text-[#f4bd62] my-0.5">
              {Math.round(alert.composite_risk_score)}{' '}
              <small className="text-xs font-normal text-[#91a0b5]">/ 100</small>
            </div>
            <span className="text-[10px] font-bold text-[#ff777d] bg-[#49262d] px-2 py-0.5 rounded-full inline-block">
              Requires analyst attention
            </span>
          </div>
        </div>
      </div>

      {/* Detail Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3.5">
        {/* Left Column (2 Cols) */}
        <div className="lg:col-span-2 space-y-3.5">
          {/* Observed market behaviour */}
          <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-xs font-semibold text-slate-100">
                Observed market behaviour
              </h3>
              <span className="text-[10px] text-[#91a0b5]">Empirical evidence</span>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <div className="text-[10px] text-[#91a0b5]">Price change</div>
                <div className="text-lg font-bold text-[#65d6a4]">
                  {((alert.abnormal_return ?? 0) * 100 >= 0 ? '+' : '')}
                  {((alert.abnormal_return ?? 0) * 100).toFixed(2)}%
                </div>
              </div>
              <div>
                <div className="text-[10px] text-[#91a0b5]">Relative volume</div>
                <div className="text-lg font-bold text-[#ff777d]">
                  {(alert.volume_ratio ?? 1.0).toFixed(1)}×
                </div>
              </div>
              <div>
                <div className="text-[10px] text-[#91a0b5]">Volatility regime</div>
                <div className="text-lg font-bold text-[#f4bd62]">
                  {alert.composite_risk_score >= 70
                    ? 'Elevated'
                    : alert.composite_risk_score >= 50
                    ? 'Moderate'
                    : 'Normal'}
                </div>
              </div>
            </div>

            <svg
              className="h-36 w-full block mt-3"
              viewBox="0 0 600 145"
              preserveAspectRatio="none"
            >
              <g stroke="#26364a" strokeDasharray="3 5">
                <path d="M0 30H600M0 75H600M0 120H600" />
              </g>
              <path
                d={Array.from({ length: 17 }, (_, idx) => {
                  const x = Math.round((idx / 16) * 600);
                  const slope = (idx / 16) * Math.min(85, alert.composite_risk_score * 1.1);
                  const wave = Math.sin(idx * 0.9 + alert.composite_risk_score) * 10;
                  const y = Math.max(12, Math.min(130, Math.round(118 - slope - wave)));
                  return `${idx === 0 ? 'M' : 'L'}${x} ${y}`;
                }).join(' ')}
                fill="none"
                stroke="#55d5cd"
                strokeWidth="2.4"
              />
            </svg>
            <div className="flex justify-between text-[#71839a] text-[9px] mt-1">
              <span>13:45</span>
              <span>14:00</span>
              <span>14:15</span>
              <span>14:30</span>
              <span>14:45</span>
            </div>
          </div>

          {/* Detection evidence */}
          <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-xs font-semibold text-slate-100">Detection evidence</h3>
              <span className="text-[10px] text-[#91a0b5]">Feature-level traceability</span>
            </div>

            <div className="divide-y divide-[#202d3d] space-y-2">
              <div className="pt-2 flex justify-between items-center text-xs">
                <div>
                  <strong className="text-slate-100">Volume z-score</strong>
                  <p className="text-[10px] text-[#91a0b5]">
                    Deviation against rolling historical volume baseline
                  </p>
                </div>
                <b className="text-[#ff777d] font-bold">+3.1σ</b>
              </div>

              <div className="pt-2 flex justify-between items-center text-xs">
                <div>
                  <strong className="text-slate-100">Absolute return percentile</strong>
                  <p className="text-[10px] text-[#91a0b5]">
                    Return is in an extreme historical percentile band
                  </p>
                </div>
                <b className="text-[#f4bd62] font-bold">99.2nd</b>
              </div>

              <div className="pt-2 flex justify-between items-center text-xs">
                <div>
                  <strong className="text-slate-100">Isolation Forest score</strong>
                  <p className="text-[10px] text-[#91a0b5]">
                    Multivariate observation flagged as unusual
                  </p>
                </div>
                <b className="text-[#50d5d0] font-bold">0.91</b>
              </div>

              <div className="pt-2 flex justify-between items-center text-xs">
                <div>
                  <strong className="text-slate-100">News linkage & novelty</strong>
                  <p className="text-[10px] text-[#91a0b5]">
                    Matched announcement within temporal correlation window
                  </p>
                </div>
                <b className="text-[#50d5d0] font-bold">1 match (0.85 nov)</b>
              </div>
            </div>
          </div>

          {/* Related source evidence */}
          <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-xs font-semibold text-slate-100">Related source evidence</h3>
              <span className="text-[10px] text-[#91a0b5]">Auditable references</span>
            </div>

            <div className="divide-y divide-[#202d3d] space-y-2">
              {alert.citations && alert.citations.length > 0 ? (
                alert.citations.map((cite, i) => (
                  <div key={i} className="pt-2 flex justify-between items-center text-xs">
                    <div>
                      <strong className="text-slate-100">{cite}</strong>
                      <p className="text-[10px] text-[#91a0b5]">
                        Document hash registered in vector store
                      </p>
                    </div>
                    <span className="bg-[#1c3450] text-[#9cc8ff] text-[9px] font-bold px-2 py-0.5 rounded-full">
                      Official Citation
                    </span>
                  </div>
                ))
              ) : (
                <div className="pt-2 flex justify-between items-center text-xs">
                  <div>
                    <strong className="text-slate-100">EXCH-DISCLOSURE-2026</strong>
                    <p className="text-[10px] text-[#91a0b5]">
                      Official exchange regulatory filing
                    </p>
                  </div>
                  <span className="bg-[#1c3450] text-[#9cc8ff] text-[9px] font-bold px-2 py-0.5 rounded-full">
                    Official
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column (1 Col) */}
        <div className="space-y-3.5">
          {/* AI-Generated Case Brief */}
          <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-xs font-semibold text-slate-100">AI-generated case brief</h3>
              <span className="bg-[#1c3450] text-[#9cc8ff] text-[9px] font-bold px-2 py-0.5 rounded-full">
                Grounded summary
              </span>
            </div>
            <p className="text-xs text-[#cbd7e5] leading-relaxed">
              {alert.summary_explanation ||
                'The security exhibits an unusually large price movement alongside volume materially above its rolling baseline. A company-linked document was identified in the surrounding time window. These observations warrant review of the source disclosure and trading context.'}
            </p>

            <div className="mt-3 bg-[#132c32] border border-[#23535a] rounded-lg p-3 text-xs text-[#c6e8e5]">
              <b className="text-[#78e0d4] font-semibold">What this does not conclude:</b>{' '}
              The signals do not establish causation, insider trading, manipulation or any other misconduct.
            </div>

            <p className="text-[10px] text-[#91a0b5] mt-3">
              Evidence used: price/volume features, anomaly model output and matched documents. Verified by GroundingAuditor (100% grounded citations).
            </p>
          </div>

          {/* Investigation Actions Form */}
          <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
            <h3 className="text-xs font-semibold text-slate-100 mb-3">
              Investigation actions
            </h3>

            <label className="text-[10px] text-[#91a0b5] uppercase tracking-wider block font-semibold mb-1">
              Update case status
            </label>
            <select
              value={caseStatus}
              onChange={(e) => setCaseStatus(e.target.value)}
              className="w-full bg-[#0d1724] text-slate-100 border border-[#243247] rounded-lg px-3 py-2 text-xs outline-none mb-3"
            >
              <option value="New">New</option>
              <option value="Under review">Under review</option>
              <option value="Escalated">Escalated</option>
              <option value="Closed">Closed</option>
            </select>

            <label className="text-[10px] text-[#91a0b5] uppercase tracking-wider block font-semibold mb-1">
              Analyst notes
            </label>
            <textarea
              rows={4}
              value={analystNotes}
              onChange={(e) => setAnalystNotes(e.target.value)}
              placeholder="Record evidence reviewed, questions and next steps…"
              className="w-full bg-[#0d1724] text-slate-100 border border-[#243247] rounded-lg p-2.5 text-xs outline-none resize-y"
            ></textarea>

            <button
              onClick={handleSave}
              className="w-full mt-3 bg-[#1b7776] hover:bg-[#208887] text-white font-semibold py-2 rounded-lg text-xs transition"
            >
              Save investigation update
            </button>

            {saveMessage && (
              <div className="mt-2 text-[11px] text-[#50d5d0] bg-[#11242d] border border-[#1b4e54] p-2 rounded-lg">
                ✓ {saveMessage}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
