# DATA LICENSING & REGULATORY USAGE MATRIX
# MARKET SENTINEL AI
## Legal Boundaries, Permitted Uses, and Data Governance Framework

---

## 1. Executive Summary & Regulatory Purpose

Market Sentinel AI is an **investigative decision-support and surveillance intelligence system**. It is designed for regulatory compliance research, market anomaly detection, and fraud pattern evaluation.

To maintain strict compliance with data provider contracts, copyright frameworks, and exchange data distribution policies, this document establishes a **four-tier legal data classification** and evaluates every data source ingested by the platform.

---

## 2. Four-Tier Data Classification Matrix

| Classification Tier | Description | Examples | Permitted System Usage | Redistribution / Commercial Restrictions |
|---|---|---|---|---|
| **Tier 1: Public Regulatory Disclosures** | Mandatory statutory company filings and regulatory notices submitted to securities regulators. | • SEC EDGAR Submissions (8-K, 10-Q)<br>• SEBI Orders & Show Cause Notices<br>• Exchange Corporate Filings (BSE/NSE announcements) | • Ingestion into local vector store (`pgvector`)<br>• Full-text extraction and RAG synthesis<br>• Citation and audit evidence generation | • Freely inspectable and quotable under statutory public record / fair use doctrine.<br>• Must not misrepresent or alter official filings. |
| **Tier 2: Historical Exchange Daily Archives** | Periodic end-of-day market summaries and delivery position files published publicly for investor education and market transparency. | • NSE UDiFF EOD Bhavcopy (`.csv.zip`)<br>• NSE Security-wise Delivery Position (`MTO_<date>.DAT`)<br>• BSE Bhavcopy CSV | • Internal historical research<br>• Statistical baseline estimation<br>• Anomaly detection model calibration | • **No commercial redistribution**: Data cannot be resold or republished as raw data feeds.<br>• Systematic high-frequency scraping of interactive website pages is restricted by NSE website terms.<br>• Official archive downloads must adhere to non-disruptive off-peak batch schedules. |
| **Tier 3: Commercial / Licensed Real-Time Feeds** | Proprietary, latency-sensitive tick-by-tick and Level 2/3 market feeds. | • NSE NOW / Direct Market Access (DMA)<br>• Bloomberg / Refinitiv Data Feeds<br>• Paid Alpha Vantage Premium APIs | • Real-time live surveillance (when authorized subscriber agreements are executed) | • Requires formal Subscriber License Agreement (SLA).<br>• Commercial deployment requires exchange redistribution licenses.<br>• **Not used in Open Source / Academic Core**: Synthetic or mocked equivalents are used exclusively for pipeline test fixtures. |
| **Tier 4: Public News Feeds & Media RSS** | Syndicated headlines and article summaries distributed via standard RSS/XML protocols. | • Economic Times RSS<br>• Moneycontrol RSS<br>• Business Standard RSS | • Real-time event extraction<br>• Sentiment score computation<br>• Metadata linking and title attribution | • Must retain canonical URLs and source attribution.<br>• Only title and brief summary stored; full body text cached ephemerally for NLP without persistent re-distribution.<br>• Respect `robots.txt` and publisher feed terms. |

---

## 3. Comprehensive Source Governance Table

| Source ID | Source Name | Publisher | Governing Policy / Terms | Internal Research | Commercial Use | Redistribution | Required Attribution |
|---|---|---|---|---|---|---|---|
| `SRC-NSE-EOD` | NSE UDiFF Bhavcopy & MTO | National Stock Exchange of India Ltd. | NSE Website Terms of Use & Data Sharing Policy | **Permitted** | **Restricted** (Requires Exchange Agreement) | **Prohibited** (Raw data cannot be republished) | "Source: National Stock Exchange of India Ltd. End-of-day summary data." |
| `SRC-SEC-EDGAR` | SEC EDGAR API | U.S. Securities and Exchange Commission | SEC EDGAR Access Terms (Public Domain / 17 U.S.C. § 105) | **Permitted** | **Permitted** | **Permitted** | "Source: U.S. Securities and Exchange Commission EDGAR System." |
| `SRC-NSE-CORP-ANNOUNCEMENTS` | NSE Corporate Announcements | NSE India / Listed Corporates | SEBI (LODR) Regulations, 2015 / Public Disclosure | **Permitted** | **Permitted for analysis** | **Restricted to excerpts/citations** | "Source: Official Corporate Disclosure filed under SEBI LODR." |
| `SRC-FIN-NEWS-RSS` | Financial News RSS Streams | Media Outlets (ET, Moneycontrol, etc.) | Standard RSS Syndication Terms | **Permitted** | **Derivative scoring only** | **Prohibited** (Store only URLs & snippets) | Full citation of publisher, author, and canonical article URL. |
| `SRC-ALPHAVANTAGE` | Alpha Vantage Market API | Alpha Vantage Inc. | Alpha Vantage Terms of Service | **Permitted** (Within 25 req/day free limit) | **Requires Commercial API Key** | **Prohibited** | "Market data provided by Alpha Vantage." |

---

## 4. Technical Compliance Controls Implemented in Codebase

1. **User-Agent & Contact Disclosure**:
   - `CorporateDisclosureClient` declares transparent user-agent contact headers per SEC EDGAR requirements (`User-Agent: MarketSentinelAI AdminContact@marketsentinel.local`).
2. **Rate Limiting & Exponential Backoff**:
   - All network calls utilize the `ingestion_retry` policy with exponential backoff and jitter to prevent server overload or quota denial.
3. **Data Provenance & Cryptographic Lineage**:
   - Every ingested quote, disclosure, and article stores:
     - `retrieval_timestamp_utc`: Time of download.
     - `original_source_url`: Full verified URL.
     - `content_hash`: SHA-256 fingerprint for tamper-evident provenance.
4. **Non-Redistribution Architecture**:
   - The application does not expose raw data export APIs that could constitute unauthorized data resale.

---
*Reference: Single Source of Truth [`docs/MASTER_IMPLEMENTATION_PROMPT.md`](file:///e:/Praxis/TERM%203/MARKET%20SENTINEL%20AI/docs/MASTER_IMPLEMENTATION_PROMPT.md).*
