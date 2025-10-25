from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "oraculo_icms",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.beat_schedule = {
    "reset-monthly-limits": {
        "task": "app.workers.tasks.reset_monthly_limits",
        "schedule": 60 * 60 * 24,
    },
}

celery_app.autodiscover_tasks(["app.workers"])
