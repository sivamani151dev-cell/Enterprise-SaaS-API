from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "enterprise_saas",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks.emails",
        "app.workers.tasks.webhooks",
    ]
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Retry settings
    task_max_retries=3,
    task_default_retry_delay=60,  # 60 seconds between retries

    # Result expiry
    result_expires=3600,  # results expire after 1 hour

    # Routing
    task_routes={
        "app.workers.tasks.emails.*": {"queue": "emails"},
        "app.workers.tasks.webhooks.*": {"queue": "webhooks"},
    },

    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,  # acknowledge after completion, not before
)