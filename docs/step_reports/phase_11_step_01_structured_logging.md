# Step 11.1: Structured JSON Logging & Correlation IDs Report

## 1. Objective & Business Relevance
Step 11.1 introduces structured JSON logging and distributed request correlation across Market Sentinel AI. In compliance-regulated financial surveillance environments, every incoming alert query, event ingestion, and analyst interaction must have an immutable trace identifier (`X-Correlation-ID`) across logs and service responses to provide clear audit trails for regulatory inquiries.

## 2. Technical Explanation & Architectural Fit
- **Structured JSON Formatter (`backend/core/logging.py`)**: Extends Python's `logging.Formatter` to output single-line JSON logs containing ISO-8601 timestamps, log level, module, line number, message, and extracted correlation context.
- **Async Context Variable**: Utilizes Python `contextvars.ContextVar` to propagate correlation IDs across async FastAPI task contexts without thread-safety risks or global state mutation.
- **ASGI Correlation Middleware**: Intercepts requests, extracts existing `X-Correlation-ID` headers or generates new RFC 4122 UUID4 values, attaches them to context and outgoing response headers.
- **Middleware Integration**: Mounted in `backend/main.py`.

## 3. Technology Decisions & Alternatives Considered
- **Standard Library `logging` + `contextvars` vs Heavy Log Frameworks**:
  - Eliminates external dependencies, avoids background process churn, and operates with sub-millisecond execution matching the 16 GB CPU-only development profile.

## 4. Files Created / Modified
- `backend/core/logging.py`: Structured JSON formatter and correlation ID middleware.
- `backend/main.py`: Registered correlation middleware.
- `tests/unit/test_structured_logging.py`: Automated tests verifying JSON formatting, auto-generation, and preservation of correlation IDs.
- `docs/step_reports/phase_11_step_01_structured_logging.md`: This report.

## 5. Commands Executed & Testing Report
```bash
python -m pytest tests/unit/test_structured_logging.py -v
```
Output:
```
tests/unit/test_structured_logging.py::test_json_formatter_structure PASSED [ 33%]
tests/unit/test_structured_logging.py::test_correlation_id_auto_generation PASSED [ 66%]
tests/unit/test_structured_logging.py::test_correlation_id_preservation PASSED [100%]
============================== 3 passed in 0.35s ==============================
```

## 6. Known Limitations & Edge Cases
- When streaming high-frequency ticks from Redpanda, log volume should be throttled to warning/error levels in production to avoid disk I/O saturation.

## 7. Status & Sign-off
- **Status**: COMPLETED & VERIFIED
- **Phase 11 Step**: Step 11.1 Approved
