/**
 * TypeScript Data Contracts for Market Sentinel AI Surveillance UI.
 * Phase 10 & 11: Full contracts matching 9-page Head of UI/UX Surveillance Workspace.
 */

export type PriorityLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export interface AlertSummary {
  alert_id: string;
  ticker: string;
  event_timestamp: string;
  composite_risk_score: number;
  priority_level: PriorityLevel;
  anomaly_category: string;
  summary_explanation: string;
}

export interface AlertDetail extends AlertSummary {
  model_version: string;
  abnormal_return: number;
  volume_ratio: number;
  sentiment_score: number;
  novelty_score: number;
  citations: string[];
}

export interface InvestigationCase {
  case_id: string;
  alert_id: string;
  ticker: string;
  status: 'New' | 'Under review' | 'Assigned' | 'Escalated' | 'Closed';
  analyst_notes?: string;
  created_at: string;
  updated_at: string;
  dossier_text?: string;
  evidence_count: number;
}

export interface SymbolInfo {
  symbol: string;
  company_name: string;
  sector: string;
  industry: string;
  exchange: string;
  is_active: boolean;
}

export interface MarketWatchQuote {
  symbol: string;
  company_name: string;
  last_price: number;
  change_pct: number;
  volume_ratio: number;
  volatility_regime: string;
  signal: string;
  risk_score: number;
  priority: string;
}

export interface NewsAnnouncementItem {
  id: string;
  published_time: string;
  ticker: string;
  company_name: string;
  event_category: string;
  sentiment: 'Positive' | 'Neutral' | 'Negative';
  novelty: 'High' | 'Medium' | 'Low';
  source_type: string;
  linked_signal: string;
  headline: string;
}

export interface AuditLogEntry {
  timestamp: string;
  case_id: string;
  action: string;
  analyst: string;
  rationale: string;
}
