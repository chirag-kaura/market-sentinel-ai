import React, { useState, useEffect } from 'react';
import { AlertQueue } from './components/AlertQueue';
import { DossierViewer } from './components/DossierViewer';
import { Sidebar, PageId } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { OverviewView } from './components/OverviewView';
import { SurveillanceView } from './components/SurveillanceView';
import { AnomalyView } from './components/AnomalyView';
import { VolatilityView } from './components/VolatilityView';
import { NewsView } from './components/NewsView';
import { AlertCentreView } from './components/AlertCentreView';
import { InvestigationView } from './components/InvestigationView';
import { AnalystReviewView } from './components/AnalystReviewView';
import { SystemHealthView } from './components/SystemHealthView';
import { api } from './services/api';
import {
  AlertSummary,
  AlertDetail,
  MarketWatchQuote,
  NewsAnnouncementItem,
  AuditLogEntry,
} from './types';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageId>('overview');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [alerts, setAlerts] = useState<AlertSummary[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<AlertDetail | null>(null);
  const [watchlist, setWatchlist] = useState<MarketWatchQuote[]>([]);
  const [news, setNews] = useState<NewsAnnouncementItem[]>([]);
  const [streamConnected, setStreamConnected] = useState(false);

  // Auditable review trail state
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([
    {
      timestamp: '14:51',
      case_id: 'MS-26017',
      action: 'Assigned',
      analyst: 'A. Rao',
      rationale: 'Initial triage · unusual pre-announcement volume spike',
    },
    {
      timestamp: '14:37',
      case_id: 'MS-26016',
      action: 'Under review',
      analyst: 'S. Mehta',
      rationale: 'Cross-checking sector monetary policy update',
    },
  ]);

  // Initial load
  useEffect(() => {
    async function initData() {
      try {
        const [loadedAlerts, loadedQuotes, loadedNews] = await Promise.all([
          api.getAlerts(),
          api.getWatchlist(),
          api.getNews(),
        ]);
        setAlerts(loadedAlerts);
        setWatchlist(loadedQuotes);
        setNews(loadedNews);

        if (loadedAlerts.length > 0) {
          const detail = await api.getAlertDetail(loadedAlerts[0].alert_id);
          setSelectedAlert(detail);
        }
      } catch (err) {
        console.error('Initial data load error:', err);
      }
    }
    initData();
  }, []);

  // SSE Stream integration
  useEffect(() => {
    const unsubscribe = api.subscribeToAlertStream((newAlert) => {
      setStreamConnected(true);
      setAlerts((prev) => {
        // Prevent duplicate alert IDs
        if (prev.some((a) => a.alert_id === newAlert.event_id)) return prev;

        const incoming: AlertSummary = {
          alert_id: newAlert.event_id,
          ticker: newAlert.ticker,
          event_timestamp: newAlert.timestamp,
          composite_risk_score: newAlert.composite_risk_score,
          priority_level: newAlert.priority,
          anomaly_category: newAlert.anomaly_type,
          summary_explanation:
            newAlert.summary_explanation || 'Streaming surveillance event detected.',
        };

        return [incoming, ...prev].slice(0, 50);
      });
    });

    return () => unsubscribe();
  }, []);

  const handleSelectAlert = async (alertId: string) => {
    const detail = await api.getAlertDetail(alertId);
    setSelectedAlert(detail);
    setCurrentPage('investigation');
  };

  const handleSelectSecurity = (symbol: string) => {
    const matching = alerts.find((a) => a.ticker === symbol);
    if (matching) {
      handleSelectAlert(matching.alert_id);
    } else {
      setCurrentPage('anomalies');
    }
  };

  const handleAddAuditLog = (entry: AuditLogEntry) => {
    setAuditLogs((prev) => [entry, ...prev]);
  };

  return (
    <div className="flex min-h-screen bg-[#0a0f18] text-[#e8eef7] font-sans antialiased">
      {/* Fixed Sidebar */}
      <Sidebar
        currentPage={currentPage}
        onNavigate={(page) => {
          setCurrentPage(page);
          setIsSidebarOpen(false);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        alertCount={alerts.length}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col md:ml-64 min-w-0">
        <TopBar
          currentPage={currentPage}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
          streamConnected={streamConnected}
        />

        <main className="flex-1 p-5 md:p-8 max-w-7xl w-full mx-auto space-y-6">
          {/* Institutional Compliance Notice */}
          <div className="bg-[#211d17] border border-[#59482d] text-[#e9c98e] rounded-xl px-4 py-3 text-xs flex items-center justify-between">
            <div>
              <strong className="text-[#ffe0a6]">SURVEILLANCE WORKSPACE NOTICE —</strong>{' '}
              All risk scores, anomaly detections, and AI case summaries are investigative screening aids and do not constitute legal findings of misconduct.
            </div>
          </div>

          {/* 9 Workspaces */}
          {currentPage === 'overview' && (
            <OverviewView
              alerts={alerts}
              onNavigateToAlerts={() => setCurrentPage('alerts')}
              onSelectAlert={handleSelectAlert}
            />
          )}

          {currentPage === 'surveillance' && (
            <SurveillanceView
              quotes={watchlist}
              onSelectSecurity={handleSelectSecurity}
            />
          )}

          {currentPage === 'anomalies' && (
            <AnomalyView onSelectSecurity={handleSelectSecurity} />
          )}

          {currentPage === 'volatility' && <VolatilityView />}

          {currentPage === 'news' && <NewsView news={news} />}

          {currentPage === 'alerts' && (
            <AlertCentreView
              alerts={alerts}
              selectedAlertId={selectedAlert?.alert_id || null}
              onSelectAlert={async (id) => {
                const detail = await api.getAlertDetail(id);
                setSelectedAlert(detail);
              }}
              onOpenInvestigation={() => setCurrentPage('investigation')}
            />
          )}

          {currentPage === 'investigation' && (
            <InvestigationView
              alert={selectedAlert}
              onBackToAlerts={() => setCurrentPage('alerts')}
              onSaveCaseUpdate={(status, notes) => {
                if (selectedAlert) {
                  handleAddAuditLog({
                    timestamp: new Date().toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    }),
                    case_id: selectedAlert.alert_id,
                    action: `Status: ${status}`,
                    analyst: 'A. Rao',
                    rationale: notes || 'Updated in investigation workspace',
                  });
                }
              }}
            />
          )}

          {currentPage === 'review' && (
            <AnalystReviewView
              auditLogs={auditLogs}
              onAddAuditLog={handleAddAuditLog}
              onSelectCase={(caseId) => handleSelectAlert(caseId)}
            />
          )}

          {currentPage === 'health' && <SystemHealthView />}

          <footer className="text-[#62738a] text-[11px] text-center pt-8 pb-4">
            MARKET SENTINEL AI · INSTITUTIONAL SURVEILLANCE & RISK INTELLIGENCE WORKSPACE
          </footer>
        </main>
      </div>
    </div>
  );
};
