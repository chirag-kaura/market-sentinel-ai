import React, { useState } from 'react';
import { MarketWatchQuote } from '../types';

interface SurveillanceViewProps {
  quotes: MarketWatchQuote[];
  onSelectSecurity: (symbol: string) => void;
}

export const SurveillanceView: React.FC<SurveillanceViewProps> = ({
  quotes,
  onSelectSecurity,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [signalFilter, setSignalFilter] = useState('');

  const filteredQuotes = quotes.filter((q) => {
    const matchSearch =
      q.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.company_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchSignal = signalFilter ? q.signal.toLowerCase().includes(signalFilter.toLowerCase()) : true;
    return matchSearch && matchSignal;
  });

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="text-[#50d5d0] text-[10px] tracking-widest uppercase font-bold">
            Market observability
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Market Surveillance
          </h1>
          <p className="text-xs text-[#91a0b5] mt-0.5">
            Scan monitored securities for unusual movements across price, volume and trading behaviour.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select className="bg-[#0d1724] text-slate-200 border border-[#243247] rounded-lg px-3 py-1.5 text-xs outline-none">
            <option>NSE cash market</option>
            <option>Watchlist</option>
          </select>
          <select className="bg-[#0d1724] text-slate-200 border border-[#243247] rounded-lg px-3 py-1.5 text-xs outline-none">
            <option>Today</option>
            <option>Last 5 sessions</option>
          </select>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Universe coverage</div>
          <div className="text-2xl font-bold tracking-tight text-slate-100 my-1">
            248 <small className="text-xs font-normal text-[#91a0b5]">symbols</small>
          </div>
          <div className="text-[10px] text-[#91a0b5]">Active exchange universe</div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Price outliers</div>
          <div className="text-2xl font-bold tracking-tight text-[#f4bd62] my-1">14</div>
          <div className="text-[10px] text-[#91a0b5]">Outside expected range</div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Volume outliers</div>
          <div className="text-2xl font-bold tracking-tight text-slate-100 my-1">11</div>
          <div className="text-[10px] text-[#91a0b5]">Relative to historical baseline</div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Combined signals</div>
          <div className="text-2xl font-bold tracking-tight text-[#ff777d] my-1">09</div>
          <div className="text-[10px] text-[#91a0b5]">Queued for alert evaluation</div>
        </div>
      </div>

      {/* Security Watchlist Table */}
      <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-xs font-semibold text-slate-100">Security watchlist</h3>
          <span className="text-[10px] text-[#91a0b5]">Active market quotes</span>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-2.5 mb-4">
          <input
            type="text"
            placeholder="Search symbol or company…"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-[#0d1724] text-slate-100 border border-[#243247] rounded-lg px-3 py-1.5 text-xs outline-none min-w-[200px]"
          />
          <select
            value={signalFilter}
            onChange={(e) => setSignalFilter(e.target.value)}
            className="bg-[#0d1724] text-slate-100 border border-[#243247] rounded-lg px-3 py-1.5 text-xs outline-none"
          >
            <option value="">All signals</option>
            <option value="price">Price anomaly</option>
            <option value="volume">Volume anomaly</option>
            <option value="volatility">Volatility</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs whitespace-nowrap">
            <thead>
              <tr className="border-b border-[#243247] text-[10px] uppercase text-[#8293a9]">
                <th className="py-2.5 px-3">Symbol</th>
                <th className="py-2.5 px-3">Last price (₹)</th>
                <th className="py-2.5 px-3">Change</th>
                <th className="py-2.5 px-3">Volume vs avg.</th>
                <th className="py-2.5 px-3">Volatility</th>
                <th className="py-2.5 px-3">Signal</th>
                <th className="py-2.5 px-3">Risk</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#202d3d]">
              {filteredQuotes.map((q) => (
                <tr
                  key={q.symbol}
                  onClick={() => onSelectSecurity(q.symbol)}
                  className="hover:bg-[#172437] cursor-pointer transition text-[#d2dce9]"
                >
                  <td className="py-2.5 px-3 font-bold text-slate-100">
                    {q.symbol}
                    <span className="block font-normal text-[10px] text-[#8293a9]">
                      {q.company_name}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-medium">₹{q.last_price.toFixed(2)}</td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`font-semibold ${
                        q.change_pct >= 0 ? 'text-[#65d6a4]' : 'text-[#ff777d]'
                      }`}
                    >
                      {q.change_pct >= 0 ? '+' : ''}
                      {q.change_pct.toFixed(2)}%
                    </span>
                  </td>
                  <td className="py-2.5 px-3">
                    <span
                      className={q.volume_ratio >= 2.0 ? 'text-[#ff777d] font-bold' : 'text-[#91a0b5]'}
                    >
                      {q.volume_ratio.toFixed(1)}×
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-[#91a0b5]">{q.volatility_regime}</td>
                  <td className="py-2.5 px-3">{q.signal}</td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${
                        q.priority === 'HIGH'
                          ? 'bg-[#49262d] text-[#ff9ca1]'
                          : q.priority === 'MEDIUM'
                          ? 'bg-[#49391f] text-[#ffd18a]'
                          : 'bg-[#173b39] text-[#81e2c4]'
                      }`}
                    >
                      {q.risk_score}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
