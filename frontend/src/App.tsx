import React, { useState, useEffect } from 'react';
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
import { AlertQueue } from './components/AlertQueue';
import { DossierViewer } from './components/DossierViewer';
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
  const [backendConnected, setBackendConnected] = useState(true);

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
    api.setConnectionCallback((connected) => {
      setBackendConnected(connected);
    });

    async function initData() {
      try {
        const [loadedAlerts, loadedQuotes, loadedNews, loadedAudit] = await Promise.all([
          api.getAlerts(),
          api.getWatchlist(),
          api.getNews(),
          api.getAuditTrail(),
        ]);
        setAlerts(loadedAlerts);
        setWatchlist(loadedQuotes);
        setNews(loadedNews);
        if (loadedAudit.length > 0) {
          setAuditLogs(loadedAudit);
        }

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

  // Automatic 10-second reconnect when backend is disconnected
  useEffect(() => {
    if (backendConnected) return;
    const timer = setInterval(async () => {
      try {
        const res = await fetch('http://localhost:8000/health');
        if (res.ok) {
          setBackendConnected(true);
          const [loadedAlerts, loadedQuotes, loadedNews] = await Promise.all([
            api.getAlerts(),
            api.getWatchlist(),
            api.getNews(),
          ]);
          setAlerts(loadedAlerts);
          setWatchlist(loadedQuotes);
          setNews(loadedNews);
        }
      } catch {
        // Still offline; will retry in 10s
      }
    }, 10000);
    return () => clearInterval(timer);
  }, [backendConnected]);

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
          backendConnected={backendConnected}
        />

        <main className="flex-1 p-5 md:p-8 max-w-7xl w-full mx-auto space-y-6">
          {!backendConnected && (
            <div className="bg-[#381616] border border-[#7a2e2e] text-[#ffbbbb] rounded-xl px-4 py-3 text-xs flex items-center justify-between shadow-lg">
              <div className="flex items-center gap-2">
                <span className="text-base">⚠</span>
                <span>
                  <strong>DISCONNECTED SURVEILLANCE BACKEND:</strong> Unable to connect to FastAPI at <code className="bg-[#241010] px-1 py-0.5 rounded text-red-200">http://localhost:8000/api/v1</code>. An offline cached fallback dataset is being rendered for preview.
                </span>
              </div>
              <button
                onClick={() => window.location.reload()}
                className="bg-[#5c2323] hover:bg-[#782e2e] text-white px-2.5 py-1 rounded text-[11px] font-semibold border border-[#963b3b]"
              >
                Retry Connection
              </button>
            </div>
          )}
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
              watchlistCount={watchlist.length}
              openInvestigationsCount={auditLogs.length}
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
            <AnomalyView alerts={alerts} onSelectSecurity={handleSelectSecurity} />
          )}

          {currentPage === 'volatility' && <VolatilityView quotes={watchlist} />}

          {currentPage === 'news' && <NewsView news={news} />}

          {currentPage === 'alerts' && (
            <>
              <AlertQueue
                alerts={alerts}
                selectedAlertId={selectedAlert?.alert_id || null}
                onSelectAlert={handleSelectAlert}
              />
              <AlertCentreView
                alerts={alerts}
                selectedAlertId={selectedAlert?.alert_id || null}
                onSelectAlert={async (id) => {
                  const detail = await api.getAlertDetail(id);
                  setSelectedAlert(detail);
                }}
                onOpenInvestigation={() => setCurrentPage('investigation')}
              />
            </>
          )}

          {currentPage === 'investigation' && (
            <div className="space-y-6">
              <InvestigationView
                alert={selectedAlert}
                onBackToAlerts={() => setCurrentPage('alerts')}
                onSaveCaseUpdate={async (status, notes) => {
                  if (selectedAlert) {
                    const caseId = selectedAlert.alert_id.startsWith('CASE-')
                      ? selectedAlert.alert_id
                      : `CASE-${selectedAlert.alert_id}`;
                    try {
                      if (notes) {
                        await api.addInvestigationNotes(caseId, notes);
                      }
                      if (status) {
                        await api.updateInvestigationStatus(caseId, status, notes);
                      }
                      const updatedAudit = await api.getAuditTrail();
                      if (updatedAudit.length > 0) {
                        setAuditLogs(updatedAudit);
                      }
                    } catch (err) {
                      console.warn('API save fallback:', err);
                    }
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
              <DossierViewer
                alert={selectedAlert}
                onInitiateCase={(alertId) => handleSelectAlert(alertId)}
              />
            </div>
          )}

          {currentPage === 'review' && (
            <AnalystReviewView
              alerts={alerts}
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
