import json
import httpx
from app.workers.celery_app import celery_app
from app.core.security import generate_webhook_signature
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(
    name="deliver_webhook",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def deliver_webhook(
    self,
    webhook_url: str,
    event: str,
    payload: dict,
    org_id: str
):
    try:
        payload_str = json.dumps(payload)
        signature = generate_webhook_signature(payload_str)

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": event,
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Org-ID": org_id,
        }

        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                webhook_url,
                content=payload_str,
                headers=headers
            )
            response.raise_for_status()

        logger.info(
            "Webhook delivered",
            extra={
                "event": event,
                "org_id": org_id,
                "webhook_url": webhook_url,
                "status_code": response.status_code
            }
        )
        return {"status": "delivered", "event": event}

    except Exception as exc:
        logger.error(
            "Webhook delivery failed",
            extra={
                "event": event,
                "org_id": org_id,
                "webhook_url": webhook_url,
                "error": str(exc),
                "attempt": self.request.retries + 1
            }
        )
        raise self.retry(exc=exc)