import React from 'react';

export type PageId =
  | 'overview'
  | 'surveillance'
  | 'anomalies'
  | 'volatility'
  | 'news'
  | 'alerts'
  | 'investigation'
  | 'review'
  | 'health';

interface SidebarProps {
  currentPage: PageId;
  onNavigate: (page: PageId) => void;
  isOpen: boolean;
  onClose: () => void;
  alertCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onNavigate,
  isOpen,
  alertCount,
}) => {
  return (
    <aside
      className={`w-64 bg-[#0d1420] border-r border-[#243247] p-5 fixed inset-y-0 left-0 flex flex-col z-20 transition-transform duration-200 md:translate-x-0 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}
    >
      {/* Brandmark */}
      <div className="flex items-center gap-3 px-2 pb-6 border-b border-[#243247]/60">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#52ddd0] to-[#3579bc] flex items-center justify-center text-[#07121b] font-black text-lg shadow-sm">
          M
        </div>
        <div>
          <strong className="text-sm font-bold tracking-wide text-slate-100 block">
            MARKET SENTINEL
          </strong>
          <small className="block text-[#91a0b5] text-[10px] tracking-widest uppercase font-semibold">
            AI risk intelligence
          </small>
        </div>
      </div>

      {/* Nav Group 1 */}
      <div className="text-[#66768c] text-[10px] tracking-widest uppercase px-3 pt-5 pb-2 font-semibold">
        Surveillance workspace
      </div>
      <nav className="flex flex-col gap-1">
        <button
          onClick={() => onNavigate('overview')}
          className={`w-full border-0 text-left px-3 py-2.5 rounded-lg flex items-center gap-3 text-xs transition-colors ${
            currentPage === 'overview'
              ? 'bg-[#1a2b40] text-[#f1f7ff] font-semibold border-l-2 border-[#50d5d0]'
              : 'text-[#9eacc0] hover:bg-[#152235] hover:text-[#f1f7ff]'
          }`}
        >
          <span className="w-4 text-center text-sm">◫</span>
          Executive Overview
        </button>

        <button
          onClick={() => onNavigate('surveillance')}
          className={`w-full border-0 text-left px-3 py-2.5 rounded-lg flex items-center gap-3 text-xs transition-colors ${
            currentPage === 'surveillance'
              ? 'bg-[#1a2b40] text-[#f1f7ff] font-semibold border-l-2 border-[#50d5d0]'
              : 'text-[#9eacc0] hover:bg-[#152235] hover:text-[#f1f7ff]'
          }`}
        >
          <span className="w-4 text-center text-sm">⌁</span>
          Market Surveillance
        </button>

        <button
          onClick={() => onNavigate('anomalies')}
          className={`w-full border-0 text-left px-3 py-2.5 rounded-lg flex items-center gap-3 text-xs transition-colors ${
            currentPage === 'anomalies'
              ? 'bg-[#1a2b40] text-[#f1f7ff] font-semibold border-l-2 border-[#50d5d0]'
              : 'text-[#9eacc0] hover:bg-[#152235] hover:text-[#f1f7ff]'
          }`}
        >
          <span className="w-4 text-center text-sm">◈</span>
          Anomaly Detection
        </button>

        <button
          onClick={() => onNavigate('volatility')}
          className={`w-full border-0 text-left px-3 py-2.5 rounded-lg flex items-center gap-3 text-xs transition-colors ${
            currentPage === 'volatility'
              ? 'bg-[#1a2b40] text-[#f1f7ff] font-semibold border-l-2 border-[#50d5d0]'
              : 'text-[#9eacc0] hover:bg-[#152235] hover:text-[#f1f7ff]'
          }`}
        >
          <span className="w-4 text-center text-sm">⌁</span>
          Volatility Intelligence
        </button>

        <button
          onClick={() => onNavigate('news')}
          className={`w-full border-0 text-left px-3 py-2.5 rounded-lg flex items-center gap-3 text-xs transition-colors ${
            currentPage === 'news'
              ? 'bg-[#1a2b40] text-[#f1f7ff] font-semibold border-l-2 border-[#50d5d0]'
              : 'text-[#9eacc0] hover:bg-[#152235] hover:text-[#f1f7ff]'
          }`}
        >
          <span className="w-4 text-center text-sm">▤</span>
          News Intelligence
        </button>

        {/* Nav Group 2 */}
        <div className="text-[#66768c] text-[10px] tracking-widest uppercase px-3 pt-4 pb-2 font-semibold">
          Investigation
        </div>

        <button
          onClick={() => onNavigate('alerts')}
          className={`w-full border-0 text-left px-3 py-2.5 rounded-lg flex items-center gap-3 text-xs transition-colors ${
            currentPage === 'alerts'
              ? 'bg-[#1a2b40] text-[#f1f7ff] font-semibold border-l-2 border-[#50d5d0]'
              : 'text-[#9eacc0] hover:bg-[#152235] hover:text-[#f1f7ff]'
          }`}
        >
          <span className="w-4 text-center text-sm">⚑</span>
          Alert Centre
          <span className="ml-auto bg-[#49262d] text-[#ff9ca1] text-[10px] font-bold px-2 py-0.5 rounded-full">
            {alertCount}
          </span>
        </button>

        <button
          onClick={() => onNavigate('investigation')}
          className={`w-full border-0 text-left px-3 py-2.5 rounded-lg flex items-center gap-3 text-xs transition-colors ${
            currentPage === 'investigation'
              ? 'bg-[#1a2b40] text-[#f1f7ff] font-semibold border-l-2 border-[#50d5d0]'
              : 'text-[#9eacc0] hover:bg-[#152235] hover:text-[#f1f7ff]'
          }`}
        >
          <span className="w-4 text-center text-sm">⌕</span>
          Investigation Workspace
        </button>

        <button
          onClick={() => onNavigate('review')}
          className={`w-full border-0 text-left px-3 py-2.5 rounded-lg flex items-center gap-3 text-xs transition-colors ${
            currentPage === 'review'
              ? 'bg-[#1a2b40] text-[#f1f7ff] font-semibold border-l-2 border-[#50d5d0]'
              : 'text-[#9eacc0] hover:bg-[#152235] hover:text-[#f1f7ff]'
          }`}
        >
          <span className="w-4 text-center text-sm">✓</span>
          Analyst Review
        </button>

        {/* Nav Group 3 */}
        <div className="text-[#66768c] text-[10px] tracking-widest uppercase px-3 pt-4 pb-2 font-semibold">
          Platform
        </div>

        <button
          onClick={() => onNavigate('health')}
          className={`w-full border-0 text-left px-3 py-2.5 rounded-lg flex items-center gap-3 text-xs transition-colors ${
            currentPage === 'health'
              ? 'bg-[#1a2b40] text-[#f1f7ff] font-semibold border-l-2 border-[#50d5d0]'
              : 'text-[#9eacc0] hover:bg-[#152235] hover:text-[#f1f7ff]'
          }`}
        >
          <span className="w-4 text-center text-sm">▦</span>
          System Health
        </button>
      </nav>

      {/* Bottom Profile */}
      <div className="mt-auto border-t border-[#243247] pt-4 text-[#91a0b5] text-[11px]">
        <div className="tracking-wide">
          SURVEILLANCE ENVIRONMENT
          <div className="flex items-center gap-1.5 text-[#65d6a4] text-xs font-semibold mt-0.5">
            <span className="w-2 h-2 rounded-full bg-[#65d6a4] animate-pulse"></span>
            Live Intelligence
          </div>
        </div>
        <div className="flex items-center gap-2.5 mt-3 text-slate-100">
          <div className="w-7 h-7 rounded-full bg-[#29435a] flex items-center justify-center text-[#aeece6] font-bold text-xs">
            AR
          </div>
          <div>
            <b className="text-[11px] block leading-tight">Analyst Workspace</b>
            <span className="text-[10px] text-[#8293a9]">Risk & Compliance</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
