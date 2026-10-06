"""In-memory request metrics for the admin System Monitoring page (Phase 7).

Deliberately not a database table or an external metrics backend (Prometheus,
etc.) — that would be premature infrastructure for a platform with no
production traffic yet. A bounded in-process ring buffer is enough to show
real, honest numbers (average response time, error rate, requests/minute)
for "since this process started", which is what a single-instance dev/thesis
deployment actually has. Resets on every process restart — documented, not
hidden, in the API response (see system_monitoring_service.py).
"""

import time
from collections import deque
from datetime import datetime, timezone

MAX_SAMPLES = 2000

_samples: deque[dict] = deque(maxlen=MAX_SAMPLES)
_process_started_at = datetime.now(timezone.utc)


def register_request_metrics(app):
    @app.before_request
    def _start_timer():
        from flask import g

        g._metrics_start = time.perf_counter()

    @app.after_request
    def _record_metrics(response):
        from flask import g, request

        start = getattr(g, "_metrics_start", None)
        if start is not None:
            duration_ms = (time.perf_counter() - start) * 1000
            _samples.append(
                {
                    "path": request.path,
                    "method": request.method,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                    "at": datetime.now(timezone.utc),
                }
            )
        return response


def get_samples() -> list[dict]:
    return list(_samples)


def get_process_started_at() -> datetime:
    return _process_started_at
