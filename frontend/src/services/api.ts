/**
 * REST and SSE API Client for Surveillance Dashboard.
 * Phase 10 — Step 10.6: Typed HTTP requests with database persistence and JWT authentication.
 */

import {
  AlertSummary,
  AlertDetail,
  PriorityLevel,
  MarketWatchQuote,
  NewsAnnouncementItem,
  AuditLogEntry,
} from '../types';

const BASE_URL =
  (import.meta as unknown as { env?: Record<string, string> }).env?.VITE_API_BASE_URL ||
  'http://localhost:8000/api/v1';

export class SurveillanceApiClient {
  private token: string | null = null;
  public isUsingMockFallback: boolean = false;
  private onConnectionStateChange?: (connected: boolean) => void;

  setAuthToken(token: string) {
    this.token = token;
  }

  getAuthToken(): string | null {
    return this.token;
  }

  setConnectionCallback(cb: (connected: boolean) => void) {
    this.onConnectionStateChange = cb;
  }

  private notifyConnection(connected: boolean) {
    this.isUsingMockFallback = !connected;
    if (this.onConnectionStateChange) {
      this.onConnectionStateChange(connected);
    }
  }

  async ensureAuthenticated(): Promise<string> {
    if (this.token) return this.token;
    try {
      const res = await fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'analyst1', password: 'analyst_password123' }),
      });
      if (res.ok) {
        const data = await res.json();
        this.token = data.access_token;
        return this.token || '';
      }
    } catch (err) {
      console.warn('Backend authentication offline:', err);
    }
    return '';
  }

  private async getHeaders(): Promise<HeadersInit> {
    await this.ensureAuthenticated();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async getAlerts(ticker?: string, priority?: string, minScore = 0): Promise<AlertSummary[]> {
    const params = new URLSearchParams();
    if (ticker) params.append('ticker', ticker);
    if (priority) params.append('priority', priority);
    if (minScore > 0) params.append('min_score', minScore.toString());

    try {
      const headers = await this.getHeaders();
      const res = await fetch(`${BASE_URL}/alerts?${params.toString()}`, { headers });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      this.notifyConnection(true);
      return data;
    } catch (err) {
      this.notifyConnection(false);
      console.warn('Backend unavailable, fallback preview active:', err);
      return [
        {
          alert_id: 'MS-26018',
          ticker: 'RELIANCE',
          event_timestamp: new Date().toISOString(),
          composite_risk_score: 91.0,
          priority_level: 'HIGH',
          anomaly_category: 'Price + volume anomaly',
          summary_explanation: 'Significant volume surge (3.4x) coupled with +3.82% price expansion.',
        },
        {
          alert_id: 'MS-26017',
          ticker: 'INFY',
          event_timestamp: new Date().toISOString(),
          composite_risk_score: 86.0,
          priority_level: 'HIGH',
          anomaly_category: 'Volume + event correlation',
          summary_explanation: 'Abnormal volume cluster preceding unscheduled corporate disclosure.',
        },
        {
          alert_id: 'MS-26016',
          ticker: 'HDFCBANK',
          event_timestamp: new Date().toISOString(),
          composite_risk_score: 72.0,
          priority_level: 'MEDIUM',
          anomaly_category: 'Volatility expansion',
          summary_explanation: 'Conditional volatility expansion outside rolling reference threshold.',
        },
      ];
    }
  }

  async getWatchlist(): Promise<MarketWatchQuote[]> {
    try {
      const headers = await this.getHeaders();
      const res = await fetch(`${BASE_URL}/market/watchlist`, { headers });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      this.notifyConnection(true);
      return data;
    } catch (err) {
      this.notifyConnection(false);
      console.warn('Backend unavailable, fallback preview active:', err);
      return [
        {
          symbol: 'RELIANCE',
          company_name: 'Reliance Industries Limited',
          last_price: 1462.50,
          change_pct: 3.82,
          volume_ratio: 3.4,
          volatility_regime: 'Elevated',
          signal: 'Price + volume',
          risk_score: 91.0,
          priority: 'HIGH',
        },
        {
          symbol: 'INFY',
          company_name: 'Infosys Limited',
          last_price: 1584.20,
          change_pct: 2.76,
          volume_ratio: 2.9,
          volatility_regime: 'High',
          signal: 'Volume + news',
          risk_score: 86.0,
          priority: 'HIGH',
        },
        {
          symbol: 'HDFCBANK',
          company_name: 'HDFC Bank Limited',
          last_price: 978.65,
          change_pct: -1.92,
          volume_ratio: 1.7,
          volatility_regime: 'Elevated',
          signal: 'Volatility',
          risk_score: 72.0,
          priority: 'MEDIUM',
        },
      ];
    }
  }

  async getNews(): Promise<NewsAnnouncementItem[]> {
    try {
      const headers = await this.getHeaders();
      const res = await fetch(`${BASE_URL}/news`, { headers });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      this.notifyConnection(true);
      return data;
    } catch (err) {
      this.notifyConnection(false);
      console.warn('Backend news unavailable, fallback preview active:', err);
      return [
        {
          id: 'NEWS-2026-001',
          published_time: '14:05',
          ticker: 'INFY',
          company_name: 'Infosys Limited',
          event_category: 'Corporate disclosure',
          sentiment: 'Positive',
          novelty: 'High',
          source_type: 'Official filing',
          linked_signal: 'Volume anomaly',
          headline: 'Board approval of strategic multi-year cloud expansion contract.',
        },
        {
          id: 'NEWS-2026-002',
          published_time: '12:40',
          ticker: 'RELIANCE',
          company_name: 'Reliance Industries Limited',
          event_category: 'Business update',
          sentiment: 'Neutral',
          novelty: 'Medium',
          source_type: 'News source',
          linked_signal: 'Price + volume',
          headline: 'Consortium negotiation updates for domestic energy retail venture.',
        },
      ];
    }
  }

  async getAlertDetail(alertId: string): Promise<AlertDetail> {
    try {
      const headers = await this.getHeaders();
      const res = await fetch(`${BASE_URL}/alerts/${alertId}`, { headers });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      this.notifyConnection(true);
      return data;
    } catch (err) {
      this.notifyConnection(false);
      console.warn('Backend alert detail unavailable, fallback preview active:', err);
      return {
        alert_id: alertId,
        ticker: 'RELIANCE',
        event_timestamp: new Date().toISOString(),
        composite_risk_score: 91.0,
        priority_level: 'HIGH',
        anomaly_category: 'Price + volume anomaly',
        summary_explanation: 'The security exhibits an unusually large price movement alongside volume materially above its rolling baseline. A company-linked document was identified in the surrounding time window.',
        model_version: 'IForest v0.3.1',
        abnormal_return: 0.0382,
        volume_ratio: 3.4,
        sentiment_score: 0.15,
        novelty_score: 0.65,
        citations: ['DISC-EXCH-RELIANCE-2026', 'NSE-CASH-TICK-9941'],
      };
    }
  }

  async getInvestigationCases(): Promise<any[]> {
    try {
      const headers = await this.getHeaders();
      const res = await fetch(`${BASE_URL}/investigations`, { headers });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return res.json();
    } catch (err) {
      console.error('Failed to load investigation cases:', err);
      return [];
    }
  }

  async addInvestigationNotes(caseId: string, notes: string): Promise<any> {
    const headers = await this.getHeaders();
    const res = await fetch(`${BASE_URL}/investigations/${caseId}/notes`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ notes }),
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  }

  async updateInvestigationStatus(caseId: string, status: string, rationale?: string): Promise<any> {
    const headers = await this.getHeaders();
    const res = await fetch(`${BASE_URL}/investigations/${caseId}/status`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify({ status, rationale }),
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  }

  async escalateCaseToSAR(caseId: string, rationale: string): Promise<any> {
    const headers = await this.getHeaders();
    const res = await fetch(`${BASE_URL}/investigations/${caseId}/escalate`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ rationale }),
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  }

  async dismissCase(caseId: string, rationale: string): Promise<any> {
    const headers = await this.getHeaders();
    const res = await fetch(`${BASE_URL}/investigations/${caseId}/dismiss`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ rationale }),
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  }

  async getAuditTrail(): Promise<AuditLogEntry[]> {
    try {
      const headers = await this.getHeaders();
      const res = await fetch(`${BASE_URL}/investigations/audit/dispositions`, { headers });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      return data.map((item: any) => ({
        timestamp: new Date(item.reviewed_at_utc).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        case_id: item.case_id,
        action: item.action,
        analyst: item.analyst_username,
        rationale: item.disposition_notes,
      }));
    } catch (err) {
      console.warn('Failed to load audit trail:', err);
      return [];
    }
  }

  subscribeToAlertStream(
    onAlert: (alert: {
      event_id: string;
      timestamp: string;
      ticker: string;
      anomaly_type: string;
      composite_risk_score: number;
      priority: PriorityLevel;
      summary_explanation?: string;
    }) => void
  ): () => void {
    let eventSource: EventSource | null = null;

    this.ensureAuthenticated().then((token) => {
      const url = token ? `${BASE_URL}/stream/alerts?token=${encodeURIComponent(token)}` : `${BASE_URL}/stream/alerts`;
      eventSource = new EventSource(url);

      eventSource.addEventListener('alert', (event) => {
        try {
          const data = JSON.parse(event.data);
          onAlert(data);
        } catch (err) {
          console.error('Error parsing SSE stream message:', err);
        }
      });

      eventSource.onerror = () => {
        // Automatic reconnection handled by browser EventSource
      };
    });

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }
}

export const api = new SurveillanceApiClient();
