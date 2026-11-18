/**
 * REST and SSE API Client for Surveillance Dashboard.
 * Phase 10 — Step 10.6: Typed HTTP requests with fallback mock dataset for offline development.
 */

import {
  AlertSummary,
  AlertDetail,
  InvestigationCase,
  SymbolInfo,
  MarketWatchQuote,
  NewsAnnouncementItem,
} from '../types';

const BASE_URL = 'http://localhost:8000/api/v1';

export class SurveillanceApiClient {
  private token: string | null = null;

  setAuthToken(token: string) {
    this.token = token;
  }

  private getHeaders(): HeadersInit {
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
      const res = await fetch(`${BASE_URL}/alerts?${params.toString()}`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return await res.json();
    } catch {
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
      const res = await fetch(`${BASE_URL}/market/watchlist`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return await res.json();
    } catch {
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
        {
          symbol: 'ICICIBANK',
          company_name: 'ICICI Bank Limited',
          last_price: 1208.80,
          change_pct: -0.86,
          volume_ratio: 2.1,
          volatility_regime: 'Moderate',
          signal: 'Volume',
          risk_score: 64.0,
          priority: 'MEDIUM',
        },
        {
          symbol: 'TCS',
          company_name: 'Tata Consultancy Services Limited',
          last_price: 3214.00,
          change_pct: 0.42,
          volume_ratio: 0.9,
          volatility_regime: 'Normal',
          signal: 'None',
          risk_score: 18.0,
          priority: 'LOW',
        },
        {
          symbol: 'BHARTIARTL',
          company_name: 'Bharti Airtel Limited',
          last_price: 1734.40,
          change_pct: 1.12,
          volume_ratio: 1.1,
          volatility_regime: 'Normal',
          signal: 'None',
          risk_score: 21.0,
          priority: 'LOW',
        },
      ];
    }
  }

  async getNews(): Promise<NewsAnnouncementItem[]> {
    try {
      const res = await fetch(`${BASE_URL}/news`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return await res.json();
    } catch {
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
        {
          id: 'NEWS-2026-003',
          published_time: '11:20',
          ticker: 'HDFCBANK',
          company_name: 'HDFC Bank Limited',
          event_category: 'Sector / macro',
          sentiment: 'Negative',
          novelty: 'Low',
          source_type: 'News source',
          linked_signal: 'Volatility',
          headline: 'RBI monetary committee note on unsecured consumer loan provisions.',
        },
      ];
    }
  }

  async getAlertDetail(alertId: string): Promise<AlertDetail> {
    try {
      const res = await fetch(`${BASE_URL}/alerts/${alertId}`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return await res.json();
    } catch {
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
    const eventSource = new EventSource(`${BASE_URL}/stream/alerts`);

    eventSource.addEventListener('alert', (event) => {
      try {
        const data = JSON.parse(event.data);
        onAlert(data);
      } catch (err) {
        console.error('Error parsing SSE stream message:', err);
      }
    });

    eventSource.onerror = () => {
      // Browser EventSource automatically retries
    };

    return () => {
      eventSource.close();
    };
  }
}

export const api = new SurveillanceApiClient();
