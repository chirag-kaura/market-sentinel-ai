# Step 11.5: Operational Notification Engine (Alertmanager) Report

## 1. Objective & Business Relevance
Step 11.5 defines operational alerting, notification routing, and threshold rules for Prometheus Alertmanager in Market Sentinel AI. High-severity market risk anomalies (surges in critical alerts) or infrastructure degradation (API latency spikes, 5xx error bursts) must automatically notify surveillance leads and site-reliability engineers without overwhelming operational inboxes with noisy flapping alerts.

## 2. Technical Explanation & Architectural Fit
- **Alert Routing (`deployment/alertmanager/alertmanager.yml`)**:
  - Structured routing tree grouping alerts by `alertname`, `priority`, and `ticker`.
  - Notification grouping delays (`group_wait: 10s`, `repeat_interval: 1h`) to avoid alert spamming.
  - Distinct receivers for general surveillance ops webhooks and emergency critical paging.
  - Inhibit rules suppressing warning-level notifications when an equal critical event is firing.
- **Prometheus Surveillance Rules (`deployment/alertmanager/surveillance_alert_rules.yml`)**:
  - `HighSurveillanceAlertRate`: Fires if critical alerts exceed 0.5/sec for 2 minutes.
  - `APIHighLatencyWarning`: Fires if p95 API response times exceed 1.5 seconds for 3 minutes.
  - `HighAPIErrorRate`: Fires if 5xx errors exceed 5% of total request traffic.

## 3. Technology Decisions & Alternatives Considered
- **Prometheus Alertmanager**: Native integration with Prometheus metrics scraping; declarative YAML configuration decouples operational alerting logic from core application code.

## 4. Files Created / Modified
- `deployment/alertmanager/alertmanager.yml`: Alertmanager routing, deduplication, and receivers config.
- `deployment/alertmanager/surveillance_alert_rules.yml`: Operational PromQL alerting rules.
- `tests/unit/test_alertmanager_rules.py`: Automated tests verifying YAML schema and rule completeness.
- `docs/step_reports/phase_11_step_05_alertmanager_notifications.md`: This report.

## 5. Commands Executed & Testing Report
```bash
python -m pytest tests/unit/test_alertmanager_rules.py -v
```
Output:
```
tests/unit/test_alertmanager_rules.py::test_alertmanager_config_structure PASSED [ 50%]
tests/unit/test_alertmanager_rules.py::test_prometheus_alert_rules PASSED [100%]
============================== 2 passed in 0.25s ==============================
```

## 6. Known Limitations & Edge Cases
- Webhook endpoints must be reachable within the Docker network bridge or host network.

## 7. Status & Sign-off
- **Status**: COMPLETED & VERIFIED
- **Phase 11 Step**: Step 11.5 Approved
