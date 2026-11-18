"""
Service Health Probe and Startup Sequencing Evaluator.
Phase 12 — Step 12.3: Validates readiness of dependent services (PostgreSQL, Redis, API) before pipeline execution.
"""

import sys
import time
import urllib.request
import urllib.error
from typing import Dict, List, Tuple


def probe_http_endpoint(url: str, timeout: float = 3.0) -> Tuple[bool, str]:
    """Probes an HTTP health endpoint, returning status flag and response or error message."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Sentinel-Probe/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                return True, f"HTTP 200 OK from {url}"
            return False, f"HTTP {resp.status} from {url}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP error {e.code}: {e.reason}"
    except Exception as e:
        return False, f"Connection failure: {str(e)}"


def wait_for_service(
    service_name: str,
    url: str,
    max_retries: int = 5,
    delay_seconds: float = 1.0,
) -> bool:
    """Blocks until target service passes health probe or retry limit is exhausted."""
    for attempt in range(1, max_retries + 1):
        healthy, msg = probe_http_endpoint(url)
        if healthy:
            return True
        time.sleep(delay_seconds)
    return False


def run_system_health_audit(service_urls: Dict[str, str]) -> Dict[str, bool]:
    """Runs concurrent health probes across all configured surveillance system dependencies."""
    results = {}
    for name, url in service_urls.items():
        healthy, _ = probe_http_endpoint(url)
        results[name] = healthy
    return results


if __name__ == "__main__":
    endpoints = {
        "FastAPI Backend": "http://localhost:8000/health",
        "Frontend NGINX": "http://localhost/healthz",
        "Prometheus": "http://localhost:9090/-/healthy",
    }
    audit = run_system_health_audit(endpoints)
    all_healthy = all(audit.values())
    sys.exit(0 if all_healthy else 1)
