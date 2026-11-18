import React from 'react';
import { AlertDetail } from '../types';

interface DossierViewerProps {
  alert: AlertDetail | null;
  onInitiateCase?: (alertId: string) => void;
}

export const DossierViewer: React.FC<DossierViewerProps> = ({ alert, onInitiateCase }) => {
  if (!alert) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-slate-900 border border-slate-800 rounded-lg p-8 text-center">
        <p className="text-slate-400">Select an alert from the queue to inspect surveillance evidence and AI dossier.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-slate-900 border border-slate-800 rounded-lg overflow-y-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-100">{alert.ticker}</h1>
            <span className="text-sm font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              {alert.alert_id}
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Event Timestamp: {new Date(alert.event_timestamp).toUTCString()}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-xs text-slate-400">Risk Score</span>
            <div className="text-2xl font-black text-red-400">{alert.composite_risk_score.toFixed(1)}</div>
          </div>
          {onInitiateCase && (
            <button
              onClick={() => onInitiateCase(alert.alert_id)}
              className="ml-4 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded font-medium text-sm transition"
            >
              Open Case
            </button>
          )}
        </div>
      </div>

      {/* Quantitative Anomaly Indicators */}
      <div>
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
          Surveillance Feature Attribution
        </h3>
        <div className="grid grid-cols-4 gap-4">
          <div className="p-3 bg-slate-800 rounded border border-slate-700">
            <span className="text-xs text-slate-400">Abnormal Return</span>
            <p className="text-lg font-bold text-slate-100">{(alert.abnormal_return * 100).toFixed(2)}%</p>
          </div>
          <div className="p-3 bg-slate-800 rounded border border-slate-700">
            <span className="text-xs text-slate-400">Volume Ratio</span>
            <p className="text-lg font-bold text-amber-400">{alert.volume_ratio.toFixed(2)}x</p>
          </div>
          <div className="p-3 bg-slate-800 rounded border border-slate-700">
            <span className="text-xs text-slate-400">Sentiment Score</span>
            <p className="text-lg font-bold text-red-400">{alert.sentiment_score.toFixed(2)}</p>
          </div>
          <div className="p-3 bg-slate-800 rounded border border-slate-700">
            <span className="text-xs text-slate-400">Novelty Score</span>
            <p className="text-lg font-bold text-purple-400">{alert.novelty_score.toFixed(2)}</p>
          </div>
        </div>
      </div>

      {/* Grounded Explanation */}
      <div className="p-4 bg-slate-800/60 rounded border border-slate-700 space-y-2">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          Grounded Surveillance Explanation
        </h3>
        <p className="text-sm text-slate-200 leading-relaxed">{alert.summary_explanation}</p>
        <div className="text-xs text-slate-500 font-mono">
          Model Version: {alert.model_version} · Zero-Hallucination Policy Enforced
        </div>
      </div>

      {/* Document Citations */}
      <div>
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-2">
          Evidence Citations & Corroborating Disclosures
        </h3>
        <div className="space-y-2">
          {alert.citations.map((citation, idx) => (
            <div
              key={idx}
              className="p-3 bg-slate-800 rounded border border-slate-700 text-xs font-mono text-cyan-400 flex items-center gap-2"
            >
              <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
              <span>{citation}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
