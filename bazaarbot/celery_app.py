"""Celery application factory for BazaarBot."""
from celery import Celery
from celery.schedules import crontab

from bazaarbot.config import Config


def make_celery() -> Celery:
    broker = Config.CELERY_BROKER_URL or Config.REDIS_URL
    backend = Config.CELERY_RESULT_BACKEND or Config.REDIS_URL

    app = Celery(
        "bazaarbot",
        broker=broker,
        backend=backend,
        include=[
            "bazaarbot.tasks.email_tasks",
            "bazaarbot.tasks.order_tasks",
            "bazaarbot.tasks.alert_tasks",
            "bazaarbot.tasks.appointment_tasks",
        ],
    )

    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="Asia/Karachi",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_always_eager=Config.CELERY_TASK_ALWAYS_EAGER,
        task_routes={
            "bazaarbot.tasks.email_tasks.*": {"queue": "email"},
            "bazaarbot.tasks.order_tasks.*": {"queue": "orders"},
            "bazaarbot.tasks.alert_tasks.*": {"queue": "alerts"},
            "bazaarbot.tasks.appointment_tasks.*": {"queue": "appointments"},
        },
        beat_schedule={
            "check-low-stock-daily": {
                "task": "bazaarbot.tasks.alert_tasks.check_all_low_stock",
                "schedule": crontab(hour=9, minute=0),
            },
            "appointment-reminders-daily": {
                "task": "bazaarbot.tasks.appointment_tasks.send_daily_reminders",
                "schedule": crontab(hour=8, minute=0),
            },
            "cleanup-old-sessions-weekly": {
                "task": "bazaarbot.tasks.order_tasks.cleanup_old_sessions",
                "schedule": crontab(day_of_week=0, hour=2, minute=0),
            },
        },
    )
    return app


celery = make_celery()
