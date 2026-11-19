import React, { useState } from 'react';
import { NewsAnnouncementItem } from '../types';

interface NewsViewProps {
  news: NewsAnnouncementItem[];
}

export const NewsView: React.FC<NewsViewProps> = ({ news }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [sourceFilter, setSourceFilter] = useState<'ALL' | 'OFFICIAL' | 'MEDIA'>('ALL');
  const [timeFilter, setTimeFilter] = useState<'24H' | '7D' | 'ALL'>('ALL');

  const nowMs = Date.now();
  const filteredNews = news.filter((n) => {
    const matchSearch =
      n.ticker.toLowerCase().includes(searchTerm.toLowerCase()) ||
      n.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      n.headline.toLowerCase().includes(searchTerm.toLowerCase());
    const matchCat = categoryFilter ? n.event_category.toLowerCase().includes(categoryFilter.toLowerCase()) : true;

    const srcLower = n.source_type.toLowerCase();
    const isOfficial = srcLower.includes('nse') || srcLower.includes('bse') || srcLower.includes('sec') || srcLower.includes('filing') || srcLower.includes('disclosure');
    const matchSource =
      sourceFilter === 'OFFICIAL' ? isOfficial : sourceFilter === 'MEDIA' ? !isOfficial : true;

    let matchTime = true;
    if (timeFilter !== 'ALL') {
      const pubMs = new Date(n.published_time).getTime();
      const maxAgeMs = timeFilter === '24H' ? 86400_000 : 7 * 86400_000;
      if (!Number.isNaN(pubMs)) {
        matchTime = nowMs - pubMs <= maxAgeMs;
      }
    }

    return matchSearch && matchCat && matchSource && matchTime;
  });

  const uniqueCompanies = new Set(filteredNews.map((n) => n.ticker)).size;
  const highSentimentCount = filteredNews.filter((n) => n.sentiment.toLowerCase() !== 'neutral').length;
  const officialCount = filteredNews.filter((n) => {
    const s = n.source_type.toLowerCase();
    return s.includes('nse') || s.includes('bse') || s.includes('sec') || s.includes('filing') || s.includes('disclosure');
  }).length;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="text-[#50d5d0] text-[10px] tracking-widest uppercase font-bold">
            Event context
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            News Intelligence
          </h1>
          <p className="text-xs text-[#91a0b5] mt-0.5">
            Connect corporate disclosures and verified news events to securities and unusual market behaviour.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value as 'ALL' | 'OFFICIAL' | 'MEDIA')}
            className="bg-[#0d1724] text-slate-200 border border-[#243247] rounded-lg px-3 py-1.5 text-xs outline-none"
          >
            <option value="ALL">All sources ({news.length})</option>
            <option value="OFFICIAL">Official disclosures</option>
            <option value="MEDIA">News providers</option>
          </select>
          <select
            value={timeFilter}
            onChange={(e) => setTimeFilter(e.target.value as '24H' | '7D' | 'ALL')}
            className="bg-[#0d1724] text-slate-200 border border-[#243247] rounded-lg px-3 py-1.5 text-xs outline-none"
          >
            <option value="ALL">All time</option>
            <option value="24H">Last 24 hours</option>
            <option value="7D">Last 7 days</option>
          </select>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Documents processed</div>
          <div className="text-2xl font-bold tracking-tight text-slate-100 my-1">
            {filteredNews.length}
          </div>
          <div className="text-[10px] text-[#91a0b5]">Exchange filings & news</div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Company-linked events</div>
          <div className="text-2xl font-bold tracking-tight text-slate-100 my-1">
            {uniqueCompanies}
          </div>
          <div className="text-[10px] text-[#91a0b5]">Distinct NSE tickers matched</div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">High sentiment events</div>
          <div className="text-2xl font-bold tracking-tight text-[#f4bd62] my-1">
            {String(highSentimentCount).padStart(2, '0')}
          </div>
          <div className="text-[10px] text-[#91a0b5]">|Sentiment| ≥ 0.50</div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="text-[11px] text-[#91a0b5]">Official disclosures</div>
          <div className="text-2xl font-bold tracking-tight text-slate-100 my-1">
            {String(officialCount).padStart(2, '0')}
          </div>
          <div className="text-[10px] text-[#91a0b5]">NSE / BSE / SEC filings</div>
        </div>
      </div>

      {/* Announcements Table */}
      <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-xs font-semibold text-slate-100">Recent company events</h3>
          <span className="text-[10px] text-[#91a0b5]">FinBERT classified documents</span>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-2.5 mb-4">
          <input
            type="text"
            placeholder="Search company or event…"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-[#0d1724] text-slate-100 border border-[#243247] rounded-lg px-3 py-1.5 text-xs outline-none min-w-[200px]"
          />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-[#0d1724] text-slate-100 border border-[#243247] rounded-lg px-3 py-1.5 text-xs outline-none"
          >
            <option value="">All event types</option>
            <option value="corporate">Corporate disclosure</option>
            <option value="business">Business update</option>
            <option value="regulatory">Regulatory</option>
            <option value="sector">Sector / macro</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs whitespace-nowrap">
            <thead>
              <tr className="border-b border-[#243247] text-[10px] uppercase text-[#8293a9]">
                <th className="py-2.5 px-3">Published</th>
                <th className="py-2.5 px-3">Company</th>
                <th className="py-2.5 px-3">Event category</th>
                <th className="py-2.5 px-3">Sentiment</th>
                <th className="py-2.5 px-3">Novelty</th>
                <th className="py-2.5 px-3">Source type</th>
                <th className="py-2.5 px-3">Linked signal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#202d3d]">
              {filteredNews.map((n) => (
                <tr key={n.id} className="hover:bg-[#172437] transition text-[#d2dce9]">
                  <td className="py-2.5 px-3 text-[#91a0b5]">{n.published_time}</td>
                  <td className="py-2.5 px-3 font-bold text-slate-100">
                    {n.ticker}
                    <span className="block font-normal text-[10px] text-[#8293a9]">
                      {n.company_name}
                    </span>
                  </td>
                  <td className="py-2.5 px-3">{n.event_category}</td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`font-semibold ${
                        n.sentiment === 'Positive'
                          ? 'text-[#65d6a4]'
                          : n.sentiment === 'Negative'
                          ? 'text-[#ff777d]'
                          : 'text-[#91a0b5]'
                      }`}
                    >
                      {n.sentiment}
                    </span>
                  </td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${
                        n.novelty === 'High'
                          ? 'bg-[#49262d] text-[#ff9ca1]'
                          : n.novelty === 'Medium'
                          ? 'bg-[#49391f] text-[#ffd18a]'
                          : 'bg-[#173b39] text-[#81e2c4]'
                      }`}
                    >
                      {n.novelty}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-[#91a0b5]">{n.source_type}</td>
                  <td className="py-2.5 px-3 font-medium text-slate-200">{n.linked_signal}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Event Intelligence Pipeline Workflow */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-xs font-semibold text-slate-100">Event intelligence pipeline</h3>
            <span className="text-[10px] text-[#91a0b5]">Conceptual workflow</span>
          </div>
          <div className="border-l border-[#35506b] ml-2 pl-4 space-y-4 text-xs">
            <div className="relative">
              <span className="absolute -left-[21px] top-1 w-2 h-2 rounded-full bg-[#50d5d0] ring-4 ring-[#18313b]"></span>
              <strong className="text-slate-100">Document ingestion</strong>
              <p className="text-[11px] text-[#91a0b5] mt-0.5">
                Retrieve from official exchange filings (NSE/BSE) and authorized news wires.
              </p>
            </div>
            <div className="relative">
              <span className="absolute -left-[21px] top-1 w-2 h-2 rounded-full bg-[#50d5d0] ring-4 ring-[#18313b]"></span>
              <strong className="text-slate-100">Entity recognition & mapping</strong>
              <p className="text-[11px] text-[#91a0b5] mt-0.5">
                Resolve company names, subsidiaries, promoters, and exchange tickers.
              </p>
            </div>
            <div className="relative">
              <span className="absolute -left-[21px] top-1 w-2 h-2 rounded-full bg-[#50d5d0] ring-4 ring-[#18313b]"></span>
              <strong className="text-slate-100">Event classification & FinBERT scoring</strong>
              <p className="text-[11px] text-[#91a0b5] mt-0.5">
                Classify filing category, financial sentiment, and historical novelty distance.
              </p>
            </div>
            <div className="relative">
              <span className="absolute -left-[21px] top-1 w-2 h-2 rounded-full bg-[#50d5d0] ring-4 ring-[#18313b]"></span>
              <strong className="text-slate-100">Market temporal correlation</strong>
              <p className="text-[11px] text-[#91a0b5] mt-0.5">
                Align publication timestamp with abnormal order flow or return bursts.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-[#131e2d] to-[#101925] border border-[#243247] rounded-xl p-4 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-xs font-semibold text-slate-100">Evidence discipline</h3>
              <span className="text-[10px] text-[#91a0b5]">Regulatory Compliance</span>
            </div>
            <p className="text-xs text-[#91a0b5] leading-relaxed">
              A related article does not establish that an event caused a price movement. The platform strictly reports publication time, source authenticity, entity match confidence, and the observed market anomaly window.
            </p>
          </div>
          <div className="mt-3 bg-[#132c32] border border-[#23535a] rounded-lg p-3 text-xs text-[#c6e8e5]">
            <b className="text-[#78e0d4] font-semibold">Analyst safeguard:</b> AI-generated summaries must link back to source documents. Missing or uncertain evidence is stated explicitly without fabrication.
          </div>
        </div>
      </div>
    </div>
  );
};
