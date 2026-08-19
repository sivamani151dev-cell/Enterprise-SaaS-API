from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge
import time

# ─────────────────────────────────────────
# CUSTOM METRICS
# ─────────────────────────────────────────

# Count total orgs created
orgs_created_total = Counter(
    "orgs_created_total",
    "Total number of organizations created"
)

# Count total tasks created
tasks_created_total = Counter(
    "tasks_created_total",
    "Total number of tasks created"
)

# Count cache hits vs misses
cache_hits_total = Counter(
    "cache_hits_total",
    "Total number of cache hits",
    ["cache_key_prefix"]
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total number of cache misses",
    ["cache_key_prefix"]
)

# Count webhook deliveries
webhooks_delivered_total = Counter(
    "webhooks_delivered_total",
    "Total webhook delivery attempts",
    ["status"]  # success / failed
)

# Count active organizations
active_orgs_gauge = Gauge(
    "active_organizations_total",
    "Current number of active organizations"
)

# DB query duration
db_query_duration = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"]  # select / insert / update / delete
)

# Celery task duration
celery_task_duration = Histogram(
    "celery_task_duration_seconds",
    "Celery task execution duration",
    ["task_name"]
)


def setup_metrics(app):
    """
    Call this in main.py.
    Auto-instruments all HTTP endpoints.
    Exposes /metrics endpoint for Prometheus to scrape.
    """
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")