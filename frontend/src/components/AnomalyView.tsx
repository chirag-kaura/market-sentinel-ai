import React from 'react';

interface AnomalyViewProps {
  onSelectSecurity: (symbol: string) => void;
}

export const AnomalyView: React.FC<AnomalyViewProps> = ({ onSelectSecurity }) => {
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
          <select className="bg-[#0d1724] text-slate-200 border border-[#243247] rounded-lg px-3 py-1.5 text-xs outline-none">
            <option>All detection methods</option>
            <option>Rolling z-score</option>
            <option>Isolation Forest</option>
          </select>
          <button className="border border-[#243247] bg-[#172437] hover:bg-[#1f314a] text-slate-200 px-3 py-1.5 rounded-lg text-xs transition">
            Model details
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Signals detected</div>
          <div className="text-2xl font-bold tracking-tight text-slate-100 my-1">34</div>
          <div className="text-[10px] text-[#91a0b5]">Active surveillance session</div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">High-confidence outliers</div>
          <div className="text-2xl font-bold tracking-tight text-[#ff777d] my-1">09</div>
          <div className="text-[10px] text-[#91a0b5]">Multiple features corroborate</div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Detection model</div>
          <div className="text-lg font-bold tracking-tight text-slate-100 my-1">IForest v0.3.1</div>
          <div className="text-[10px] text-[#91a0b5]">Registered MLflow baseline</div>
        </div>
      </div>

      {/* Signal Strength & Why Flagged */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
        {/* Signal strength by security */}
        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-xs font-semibold text-slate-100">Signal strength by security</h3>
            <span className="text-[10px] text-[#91a0b5]">ML Anomaly score</span>
          </div>

          <div className="space-y-3.5 pt-1">
            <div
              onClick={() => onSelectSecurity('RELIANCE')}
              className="grid grid-cols-[100px_1fr_32px] items-center gap-3 text-xs cursor-pointer hover:opacity-80"
            >
              <span className="font-bold text-slate-100">RELIANCE</span>
              <div className="h-2 bg-[#26364a] rounded-full overflow-hidden">
                <div className="h-full bg-[#ff777d]" style={{ width: '91%' }}></div>
              </div>
              <b className="text-right text-slate-200">91</b>
            </div>

            <div
              onClick={() => onSelectSecurity('INFY')}
              className="grid grid-cols-[100px_1fr_32px] items-center gap-3 text-xs cursor-pointer hover:opacity-80"
            >
              <span className="font-bold text-slate-100">INFY</span>
              <div className="h-2 bg-[#26364a] rounded-full overflow-hidden">
                <div className="h-full bg-[#ff9b7a]" style={{ width: '86%' }}></div>
              </div>
              <b className="text-right text-slate-200">86</b>
            </div>

            <div
              onClick={() => onSelectSecurity('HDFCBANK')}
              className="grid grid-cols-[100px_1fr_32px] items-center gap-3 text-xs cursor-pointer hover:opacity-80"
            >
              <span className="font-bold text-slate-100">HDFCBANK</span>
              <div className="h-2 bg-[#26364a] rounded-full overflow-hidden">
                <div className="h-full bg-[#f4bd62]" style={{ width: '72%' }}></div>
              </div>
              <b className="text-right text-slate-200">72</b>
            </div>

            <div
              onClick={() => onSelectSecurity('ICICIBANK')}
              className="grid grid-cols-[100px_1fr_32px] items-center gap-3 text-xs cursor-pointer hover:opacity-80"
            >
              <span className="font-bold text-slate-100">ICICIBANK</span>
              <div className="h-2 bg-[#26364a] rounded-full overflow-hidden">
                <div className="h-full bg-[#f4bd62]" style={{ width: '64%' }}></div>
              </div>
              <b className="text-right text-slate-200">64</b>
            </div>

            <div
              onClick={() => onSelectSecurity('LT')}
              className="grid grid-cols-[100px_1fr_32px] items-center gap-3 text-xs cursor-pointer hover:opacity-80"
            >
              <span className="font-bold text-slate-100">LT</span>
              <div className="h-2 bg-[#26364a] rounded-full overflow-hidden">
                <div className="h-full bg-[#50d5d0]" style={{ width: '43%' }}></div>
              </div>
              <b className="text-right text-slate-200">43</b>
            </div>
          </div>
        </div>

        {/* Why was this flagged? */}
        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-xs font-semibold text-slate-100">Why was this flagged?</h3>
              <span className="text-[10px] text-[#91a0b5]">Example · RELIANCE</span>
            </div>

            <div className="divide-y divide-[#202d3d] space-y-2">
              <div className="pt-2 flex justify-between items-center text-xs">
                <div>
                  <strong className="text-slate-100">Volume deviation</strong>
                  <p className="text-[10px] text-[#91a0b5]">
                    Current volume is materially above its rolling baseline.
                  </p>
                </div>
                <b className="text-[#ff777d] font-bold">+3.4×</b>
              </div>

              <div className="pt-2 flex justify-between items-center text-xs">
                <div>
                  <strong className="text-slate-100">Price movement</strong>
                  <p className="text-[10px] text-[#91a0b5]">
                    Absolute return exceeds the selected historical percentile.
                  </p>
                </div>
                <b className="text-[#f4bd62] font-bold">+3.82%</b>
              </div>

              <div className="pt-2 flex justify-between items-center text-xs">
                <div>
                  <strong className="text-slate-100">Model outlier score</strong>
                  <p className="text-[10px] text-[#91a0b5]">
                    Feature combination is unusual relative to reference observations.
                  </p>
                </div>
                <b className="text-[#50d5d0] font-bold">0.91</b>
              </div>
            </div>
          </div>

          <p className="text-[10px] text-[#91a0b5] mt-4 border-t border-[#202d3d] pt-3">
            An anomaly score is a screening signal, not a probability of misconduct or a finding of wrongdoing.
          </p>
        </div>
      </div>

      {/* Detection methodology */}
      <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
        <div className="flex justify-between items-center mb-2">
          <h3 className="text-xs font-semibold text-slate-100">Detection methodology</h3>
          <span className="text-[10px] text-[#91a0b5]">Model transparency</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
          <div className="border border-[#243247] rounded-lg p-3 bg-[#0d1724]">
            <b className="text-xs text-slate-100 block">Statistical baseline</b>
            <p className="text-[11px] text-[#91a0b5] mt-1 leading-relaxed">
              Rolling z-scores, robust percentiles and volume ratios compare current observations against a historical reference window (20–60 sessions).
            </p>
          </div>
          <div className="border border-[#243247] rounded-lg p-3 bg-[#0d1724]">
            <b className="text-xs text-slate-100 block">Unsupervised machine learning</b>
            <p className="text-[11px] text-[#91a0b5] mt-1 leading-relaxed">
              Isolation Forest identifies multivariate observations that differ from the learned feature distribution. No labelled misconduct outcome is assumed.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
