import React, { useState } from 'react';
import { AuditLogEntry } from '../types';

interface AnalystReviewViewProps {
  auditLogs: AuditLogEntry[];
  onAddAuditLog: (entry: AuditLogEntry) => void;
  onSelectCase: (caseId: string) => void;
}

export const AnalystReviewView: React.FC<AnalystReviewViewProps> = ({
  auditLogs,
  onAddAuditLog,
  onSelectCase,
}) => {
  const [selectedCase, setSelectedCase] = useState('MS-26018 · RELIANCE');
  const [disposition, setDisposition] = useState('Requires further investigation');
  const [rationale, setRationale] = useState('');
  const [feedbackMsg, setFeedbackMsg] = useState('');

  const handleSaveReview = () => {
    if (!rationale.trim()) {
      setFeedbackMsg('Please add a rationale before saving the review decision.');
      return;
    }

    const caseId = selectedCase.split(' · ')[0];
    const newEntry: AuditLogEntry = {
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      case_id: caseId,
      action: disposition,
      analyst: 'A. Rao (Compliance)',
      rationale: rationale.trim(),
    };

    onAddAuditLog(newEntry);
    setRationale('');
    setFeedbackMsg('Review decision added to the auditable review trail.');
    setTimeout(() => setFeedbackMsg(''), 4000);
  };

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="text-[#50d5d0] text-[10px] tracking-widest uppercase font-bold">
            Human-in-the-loop controls
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Analyst Review
          </h1>
          <p className="text-xs text-[#91a0b5] mt-0.5">
            Capture analyst decisions, rationale and escalation outcomes for a defensible review trail.
          </p>
        </div>
        <button className="border border-[#243247] bg-[#172437] hover:bg-[#1f314a] text-slate-200 px-3 py-1.5 rounded-lg text-xs transition">
          Review guidelines
        </button>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Pending review</div>
          <div className="text-2xl font-bold tracking-tight text-[#f4bd62] my-1">08</div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Reviewed today</div>
          <div className="text-2xl font-bold tracking-tight text-slate-100 my-1">21</div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Escalated</div>
          <div className="text-2xl font-bold tracking-tight text-[#ff777d] my-1">03</div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Median review time</div>
          <div className="text-2xl font-bold tracking-tight text-slate-100 my-1">
            18 <small className="text-xs font-normal text-[#91a0b5]">min</small>
          </div>
        </div>
      </div>

      {/* Review Queue & Outcome Record Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
        {/* Review Queue */}
        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-xs font-semibold text-slate-100">Review queue</h3>
              <span className="text-[10px] text-[#91a0b5]">Click a case to inspect</span>
            </div>

            <div className="divide-y divide-[#202d3d]">
              <div
                onClick={() => onSelectCase('MS-26018')}
                className="py-3 flex justify-between items-center cursor-pointer hover:bg-[#172437] px-2 rounded transition"
              >
                <div>
                  <strong className="text-xs text-slate-100 block">
                    MS-26018 · RELIANCE
                  </strong>
                  <p className="text-[10px] text-[#91a0b5] mt-0.5">
                    Price + volume anomaly · New
                  </p>
                </div>
                <span className="bg-[#49262d] text-[#ff9ca1] text-[9px] font-bold px-2 py-0.5 rounded-full">
                  HIGH
                </span>
              </div>

              <div
                onClick={() => onSelectCase('MS-26017')}
                className="py-3 flex justify-between items-center cursor-pointer hover:bg-[#172437] px-2 rounded transition"
              >
                <div>
                  <strong className="text-xs text-slate-100 block">MS-26017 · INFY</strong>
                  <p className="text-[10px] text-[#91a0b5] mt-0.5">
                    Volume + event correlation · Under review
                  </p>
                </div>
                <span className="bg-[#49262d] text-[#ff9ca1] text-[9px] font-bold px-2 py-0.5 rounded-full">
                  HIGH
                </span>
              </div>

              <div
                onClick={() => onSelectCase('MS-26016')}
                className="py-3 flex justify-between items-center cursor-pointer hover:bg-[#172437] px-2 rounded transition"
              >
                <div>
                  <strong className="text-xs text-slate-100 block">
                    MS-26016 · HDFCBANK
                  </strong>
                  <p className="text-[10px] text-[#91a0b5] mt-0.5">
                    Volatility expansion · Assigned
                  </p>
                </div>
                <span className="bg-[#49391f] text-[#ffd18a] text-[9px] font-bold px-2 py-0.5 rounded-full">
                  MEDIUM
                </span>
              </div>
            </div>
          </div>

          <div className="text-[10px] text-[#91a0b5] border-t border-[#202d3d] pt-3 mt-4">
            Defensible audit trails must record human validation before case closure or formal exchange inquiry.
          </div>
        </div>

        {/* Record Review Outcome */}
        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-xs font-semibold text-slate-100">Record review outcome</h3>
            <span className="text-[10px] text-[#91a0b5]">Human decision required</span>
          </div>

          <label className="text-[10px] text-[#91a0b5] uppercase tracking-wider block font-semibold mb-1">
            Selected case
          </label>
          <select
            value={selectedCase}
            onChange={(e) => setSelectedCase(e.target.value)}
            className="w-full bg-[#0d1724] text-slate-100 border border-[#243247] rounded-lg px-3 py-2 text-xs outline-none mb-3"
          >
            <option>MS-26018 · RELIANCE</option>
            <option>MS-26017 · INFY</option>
            <option>MS-26016 · HDFCBANK</option>
          </select>

          <label className="text-[10px] text-[#91a0b5] uppercase tracking-wider block font-semibold mb-1">
            Analyst disposition
          </label>
          <select
            value={disposition}
            onChange={(e) => setDisposition(e.target.value)}
            className="w-full bg-[#0d1724] text-slate-100 border border-[#243247] rounded-lg px-3 py-2 text-xs outline-none mb-3"
          >
            <option>Requires further investigation</option>
            <option>Escalate to compliance</option>
            <option>Monitor — no immediate action</option>
            <option>Close — explainable activity</option>
          </select>

          <label className="text-[10px] text-[#91a0b5] uppercase tracking-wider block font-semibold mb-1">
            Review rationale (required for audit compliance)
          </label>
          <textarea
            rows={3}
            value={rationale}
            onChange={(e) => setRationale(e.target.value)}
            placeholder="Summarise evidence, cross-checks performed and justification…"
            className="w-full bg-[#0d1724] text-slate-100 border border-[#243247] rounded-lg p-2.5 text-xs outline-none resize-y mb-3"
          ></textarea>

          <button
            onClick={handleSaveReview}
            className="w-full bg-[#1b7776] hover:bg-[#208887] text-white font-semibold py-2 rounded-lg text-xs transition"
          >
            Save review decision
          </button>

          {feedbackMsg && (
            <div className="mt-2 text-[11px] text-[#50d5d0] bg-[#11242d] border border-[#1b4e54] p-2 rounded-lg">
              ✓ {feedbackMsg}
            </div>
          )}
        </div>
      </div>

      {/* Audit Trail Table */}
      <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-xs font-semibold text-slate-100">Audit trail</h3>
          <span className="text-[10px] text-[#91a0b5]">Defensible activity log</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs whitespace-nowrap">
            <thead>
              <tr className="border-b border-[#243247] text-[10px] uppercase text-[#8293a9]">
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Case ID</th>
                <th className="py-2.5 px-3">Disposition / Action</th>
                <th className="py-2.5 px-3">Analyst</th>
                <th className="py-2.5 px-3">Rationale</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#202d3d]">
              {auditLogs.map((entry, idx) => (
                <tr key={idx} className="hover:bg-[#172437] transition text-[#d2dce9]">
                  <td className="py-2.5 px-3 text-[#91a0b5]">{entry.timestamp}</td>
                  <td className="py-2.5 px-3 font-bold text-slate-100">{entry.case_id}</td>
                  <td className="py-2.5 px-3 font-semibold text-[#50d5d0]">
                    {entry.action}
                  </td>
                  <td className="py-2.5 px-3 text-[#91a0b5]">{entry.analyst}</td>
                  <td className="py-2.5 px-3 text-slate-200">{entry.rationale}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
