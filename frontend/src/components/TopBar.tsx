import React from 'react';
import { PageId } from './Sidebar';

const TITLES: Record<PageId, string> = {
  overview: 'Executive Overview',
  surveillance: 'Market Surveillance',
  anomalies: 'Anomaly Detection',
  volatility: 'Volatility Intelligence',
  news: 'News Intelligence',
  alerts: 'Alert Centre',
  investigation: 'Alert Investigation Workspace',
  review: 'Analyst Review',
  health: 'System Health',
};

interface TopBarProps {
  currentPage: PageId;
  onToggleSidebar: () => void;
  streamConnected: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({
  currentPage,
  onToggleSidebar,
  streamConnected,
}) => {
  return (
    <header className="h-16 border-b border-[#243247] flex items-center justify-between px-6 bg-[#0c131e] sticky top-0 z-10 shrink-0">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="md:hidden border border-[#243247] bg-[#111a28] text-[#b8c6d8] rounded-lg p-2 text-sm"
        >
          ☰
        </button>
        <div className="text-xs text-[#91a0b5]">
          Market Sentinel <span className="text-[#52647b]">/</span>{' '}
          <b className="text-slate-100 font-semibold">{TITLES[currentPage]}</b>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <span className="hidden sm:inline-flex border border-[#765c2f] text-[#f6ce85] bg-[#302718] px-2.5 py-1 rounded-full text-[10px] tracking-wider font-semibold">
          ● PRODUCTION WORKSPACE
        </span>

        <span className="flex items-center gap-1.5 text-[11px] text-[#91a0b5]">
          <span
            className={`w-2 h-2 rounded-full ${
              streamConnected ? 'bg-[#65d6a4] animate-pulse' : 'bg-[#ff777d]'
            }`}
          ></span>
          {streamConnected ? 'LIVE FEED: SSE ACTIVE' : 'STREAM: CONNECTING'}
        </span>

        <button
          title="Surveillance Notifications"
          className="border border-[#243247] bg-[#111a28] text-[#b8c6d8] rounded-lg px-2.5 py-1.5 text-xs hover:bg-[#1a2b40]"
        >
          ♧
        </button>
      </div>
    </header>
  );
};
