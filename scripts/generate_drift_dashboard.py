"""Generates an interactive HTML Data & Model Drift Dashboard from PostgreSQL 16."""
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.database import SessionLocal
from backend.models.market import MarketFeatureDailyModel
from monitoring.drift.drift_detector import DriftDetector


def build_histogram(ref_vals: np.ndarray, cur_vals: np.ndarray, bins: int = 16):
    combined = np.concatenate([ref_vals, cur_vals])
    lo, hi = float(np.percentile(combined, 1)), float(np.percentile(combined, 99))
    if hi <= lo:
        hi = lo + 1.0
    edges = np.linspace(lo, hi, bins + 1)
    ref_counts, _ = np.histogram(ref_vals, bins=edges)
    cur_counts, _ = np.histogram(cur_vals, bins=edges)
    ref_pct = [round(float(c / max(1, len(ref_vals)) * 100), 2) for c in ref_counts]
    cur_pct = [round(float(c / max(1, len(cur_vals)) * 100), 2) for c in cur_counts]
    labels = [f"{edges[i]:.3f}" for i in range(bins)]
    return labels, ref_pct, cur_pct


def main(symbol: str = "RELIANCE"):
    db = SessionLocal()
    try:
        rows = (
            db.query(MarketFeatureDailyModel)
            .filter_by(symbol=symbol)
            .order_by(MarketFeatureDailyModel.feature_date)
            .all()
        )
        df = pd.DataFrame(
            [
                {
                    "log_return_1d": float(r.return_daily),
                    "volatility_20d": float(r.volatility_roll_20d),
                    "volume_zscore_20d": float(r.volume_zscore_20d),
                    "delivery_zscore_20d": float(r.delivery_zscore_20d or 0.0),
                }
                for r in rows
            ]
        )
    finally:
        db.close()

    split = int(len(df) * 0.70)
    ref, cur = df.iloc[:split], df.iloc[split:]
    report = DriftDetector().run_drift_audit(ref, cur, list(df.columns))

    hist_data = {}
    for col in df.columns:
        labels, ref_pct, cur_pct = build_histogram(ref[col].values, cur[col].values)
        hist_data[col] = {"labels": labels, "ref": ref_pct, "cur": cur_pct}

    psi_labels = list(report.metrics.keys())
    psi_vals = [round(report.metrics[k].psi_score, 4) for k in psi_labels]
    psi_colors = [
        "#ff777d" if report.metrics[k].drift_level == "CRITICAL"
        else "#f4bd62" if report.metrics[k].drift_level == "MODERATE"
        else "#65d6a4"
        for k in psi_labels
    ]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Market Sentinel AI — Drift Dashboard ({symbol})</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    body {{ background:#0a0f18; color:#e8eef7; font-family:system-ui,sans-serif; margin:0; padding:24px; }}
    .wrap {{ max-width:1100px; margin:0 auto; }}
    .card {{ background:#131e2d; border:1px solid #243247; border-radius:12px; padding:18px; margin-bottom:18px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(460px,1fr)); gap:18px; }}
    .badge {{ padding:4px 10px; border-radius:999px; font-size:12px; font-weight:700; }}
    .crit {{ background:#49262d; color:#ff9ca1; }}
    .ok {{ background:#173b2f; color:#65d6a4; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card" style="display:flex;justify-content:space-between;align-items:center;">
      <div>
        <div style="color:#50d5d0;font-size:11px;font-weight:700;letter-spacing:1px;">EVIDENTLY / KS + PSI DRIFT MONITOR</div>
        <h1 style="margin:4px 0 0;font-size:22px;">{symbol} Feature Drift Report (PostgreSQL 16)</h1>
        <div style="color:#91a0b5;font-size:12px;margin-top:4px;">Reference: {len(ref)} days (70%) vs Current: {len(cur)} days (30%)</div>
      </div>
      <span class="badge {'crit' if report.overall_drift_detected else 'ok'}">
        {'DRIFT DETECTED' if report.overall_drift_detected else 'STABLE'}
      </span>
    </div>

    <div class="card">
      <h3 style="margin-top:0;font-size:14px;">Population Stability Index (PSI) by Feature</h3>
      <canvas id="psiChart" height="90"></canvas>
    </div>

    <div class="grid">
      {''.join(f'<div class="card"><h3 style="margin-top:0;font-size:14px;">{col} (PSI: {report.metrics[col].psi_score:.3f} · {report.metrics[col].drift_level})</h3><canvas id="hist_{col}" height="150"></canvas></div>' for col in df.columns)}
    </div>
  </div>

  <script>
    new Chart(document.getElementById('psiChart'), {{
      type: 'bar',
      data: {{
        labels: {json.dumps(psi_labels)},
        datasets: [{{ label: 'PSI Score (≥0.25 Critical, ≥0.10 Moderate)', data: {json.dumps(psi_vals)}, backgroundColor: {json.dumps(psi_colors)} }}]
      }},
      options: {{ plugins: {{ legend: {{ labels: {{ color: '#91a0b5' }} }} }}, scales: {{ x: {{ ticks: {{ color: '#91a0b5' }} }}, y: {{ ticks: {{ color: '#91a0b5' }} }} }} }}
    }});

    const histData = {json.dumps(hist_data)};
    Object.entries(histData).forEach(([col, d]) => {{
      new Chart(document.getElementById('hist_' + col), {{
        type: 'bar',
        data: {{
          labels: d.labels,
          datasets: [
            {{ label: 'Reference (Past 70%) %', data: d.ref, backgroundColor: 'rgba(80, 213, 208, 0.55)' }},
            {{ label: 'Current (Recent 30%) %', data: d.cur, backgroundColor: 'rgba(255, 119, 125, 0.55)' }}
          ]
        }},
        options: {{ plugins: {{ legend: {{ labels: {{ color: '#91a0b5' }} }} }}, scales: {{ x: {{ ticks: {{ color: '#91a0b5' }} }}, y: {{ ticks: {{ color: '#91a0b5' }} }} }} }}
      }});
    }});
  </script>
</body>
</html>"""

    out_path = PROJECT_ROOT / "drift_dashboard.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Generated interactive Drift Dashboard: {out_path}")


if __name__ == "__main__":
    main()
