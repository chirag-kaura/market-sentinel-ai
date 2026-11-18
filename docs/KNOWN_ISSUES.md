# KNOWN ISSUES, CONSTRAINTS & WORKAROUNDS
# MARKET SENTINEL AI

---

## 1. Hardware & Resource Constraints
- **Hardware Profile**: Windows 11 host with 16 GB shared system RAM and no dedicated GPU.
- **Impact**: Heavy LLMs cannot be hosted locally without freezing host execution or triggering OS paging.
- **Mitigation / Workaround**:
  - All LLM inference is strictly delegated via API abstraction (Groq baseline).
  - Multi-service Docker stacks must use Docker Compose profiles (`core`, `data`, `streaming`, `monitoring`) rather than running simultaneously.
  - Container memory limits (`mem_limit: 1g` or similar) are mandatory.

## 2. Market Data Feeds & Real-Time Limitations
- **Constraint**: Exchange direct real-time tick feeds (e.g. NSE Level 2/Level 3) require costly commercial licensing and institutional colocation.
- **Impact**: Simulating real-time market data on public streams is prohibited to maintain product integrity.
- **Mitigation / Workaround**:
  - The core market data pipeline is batch-first using authentic historical exchange reports (EOD/UDiFF reports, official historical archives).
  - Real-time streaming demonstrations will be performed on authorized live news feeds or legitimate public event APIs, cleanly distinguished from delayed/historical market data.

## 3. Financial Modeling & Anti-Look-Ahead Constraints
- **Constraint**: Financial time-series data suffers from look-ahead bias if processed naively.
- **Impact**: Model performance can appear artificially inflated if features use future data.
- **Mitigation / Workaround**:
  - Strict chronological walk-forward validation splits only.
  - Publication timestamps vs. ingestion timestamps must be stored and evaluated separately.
