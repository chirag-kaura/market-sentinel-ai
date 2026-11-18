import React from 'react';

export const VolatilityView: React.FC = () => {
  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="text-[#50d5d0] text-[10px] tracking-widest uppercase font-bold">
            Forward-looking risk
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Volatility Intelligence
          </h1>
          <p className="text-xs text-[#91a0b5] mt-0.5">
            Monitor realised volatility and model-based risk estimates to identify changing market conditions.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select className="bg-[#0d1724] text-slate-200 border border-[#243247] rounded-lg px-3 py-1.5 text-xs outline-none">
            <option>RELIANCE</option>
            <option>INFY</option>
            <option>HDFCBANK</option>
          </select>
          <select className="bg-[#0d1724] text-slate-200 border border-[#243247] rounded-lg px-3 py-1.5 text-xs outline-none">
            <option>20-session window</option>
            <option>60-session window</option>
          </select>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Annualised realised volatility</div>
          <div className="text-2xl font-bold tracking-tight text-[#f4bd62] my-1">28.4%</div>
          <div className="text-[10px] text-[#91a0b5]">GARCH estimated rolling parameter</div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Forecast volatility</div>
          <div className="text-2xl font-bold tracking-tight text-slate-100 my-1">31.7%</div>
          <div className="text-[10px] text-[#91a0b5]">Next-period model estimate</div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Volatility regime</div>
          <div className="text-xl font-bold tracking-tight text-[#f4bd62] my-1">Elevated</div>
          <div className="text-[10px] text-[#91a0b5]">Relative to historical distribution</div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Forecast horizon</div>
          <div className="text-xl font-bold tracking-tight text-slate-100 my-1">5 sessions</div>
          <div className="text-[10px] text-[#91a0b5]">Conditional volatility projection</div>
        </div>
      </div>

      {/* Realised vs Forecast Volatility SVG Chart */}
      <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-xs font-semibold text-slate-100">
            Realised vs forecast volatility
          </h3>
          <span className="text-[10px] text-[#91a0b5]">Percentage series (% per annum)</span>
        </div>

        <svg className="h-56 w-full block" viewBox="0 0 700 230" preserveAspectRatio="none">
          <g stroke="#26364a" strokeDasharray="3 5">
            <path d="M0 30H700M0 80H700M0 130H700M0 180H700" />
          </g>
          {/* Realised Volatility Curve */}
          <path
            d="M0 155 L40 148 80 160 120 135 160 142 200 116 240 125 280 103 320 114 360 82 400 91 440 70 480 86 520 58 560 72 600 48 640 59 700 39"
            fill="none"
            stroke="#55d5cd"
            strokeWidth="2.5"
          />
          {/* Forecast Volatility Curve */}
          <path
            d="M0 170 L40 165 80 169 120 151 160 156 200 140 240 144 280 128 320 133 360 113 400 119 440 103 480 111 520 94 560 99 600 84 640 90 700 72"
            fill="none"
            stroke="#8ca9ff"
            strokeWidth="2"
            strokeDasharray="6 4"
          />
        </svg>

        <div className="flex justify-between text-[#71839a] text-[9px] mt-1">
          <span>−20 sessions</span>
          <span>−15</span>
          <span>−10</span>
          <span>−5</span>
          <span>Today</span>
          <span>+5 forecast</span>
        </div>

        <div className="flex gap-4 text-[#91a0b5] text-[10px] mt-2">
          <span className="flex items-center gap-1.5">
            <i className="w-2 h-2 rounded-full bg-[#55d5cd]"></i>
            Realised volatility (GARCH fitted)
          </span>
          <span className="flex items-center gap-1.5">
            <i className="w-2 h-2 rounded-full bg-[#8ca9ff]"></i>
            Forecast conditional volatility
          </span>
        </div>
      </div>

      {/* Forecast Interpretation & Governance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-xs font-semibold text-slate-100">Forecast interpretation</h3>
              <span className="text-[10px] text-[#91a0b5]">Model Output</span>
            </div>
            <p className="text-xs text-[#cbd7e5] leading-relaxed">
              The forecast indicates a possible increase in near-term volatility relative to the recent realised baseline. This suggests closer monitoring of options order book depth may be appropriate.
            </p>
          </div>
          <div className="mt-3 bg-[#132c32] border border-[#23535a] rounded-lg p-3 text-xs text-[#c6e8e5]">
            <b className="text-[#78e0d4] font-semibold">Risk context:</b> Volatility forecasts describe the scale of potential price variation, not the direction of future price movements.
          </div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-xs font-semibold text-slate-100">Model governance</h3>
            <span className="text-[10px] text-[#91a0b5]">Validation checklist</span>
          </div>
          <div className="divide-y divide-[#243247] text-xs">
            <div className="py-2.5 flex justify-between items-center">
              <span className="text-slate-300">Walk-forward evaluation</span>
              <b className="text-[#65d6a4] font-semibold">Active · 0.04 RMSE</b>
            </div>
            <div className="py-2.5 flex justify-between items-center">
              <span className="text-slate-300">Forecast error tracking</span>
              <b className="text-[#65d6a4] font-semibold">Passed</b>
            </div>
            <div className="py-2.5 flex justify-between items-center">
              <span className="text-slate-300">Regime stability checks</span>
              <b className="text-[#65d6a4] font-semibold">Passed</b>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
