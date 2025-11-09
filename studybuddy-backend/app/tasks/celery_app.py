"""Celery application configuration.

This module configures Celery for background task processing including:
- Redis broker and result backend
- Task routing to different queues
- Retry policies with exponential backoff
- Serialization and timezone settings
- Worker and beat scheduler configuration
"""

from celery import Celery

from app.core.config import settings

# Create Celery instance
celery_app = Celery("studybuddy")

# Configure Celery
celery_app.conf.update(
    # Broker and Backend
    broker_url=settings.REDIS_URL,
    result_backend=settings.REDIS_URL,
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Task Tracking
    task_track_started=True,
    # Time Limits (5 minutes hard, 4 minutes soft)
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    # Retry Configuration
    task_autoretry_for=(Exception,),
    task_retry_backoff=True,  # Exponential backoff
    task_retry_backoff_max=600,  # Max 10 minutes between retries
    task_retry_jitter=True,  # Add randomness to prevent thundering herd
    task_max_retries=3,
    # Task Routing
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "email"},
        "app.tasks.analytics_tasks.*": {"queue": "analytics"},
        "app.tasks.event_tasks.*": {"queue": "events"},
    },
    task_default_queue="default",
    task_create_missing_queues=True,
    # Result Backend
    result_expires=86400,  # Results expire after 24 hours
    result_persistent=True,  # Persist results to backend
    # Beat Scheduler (for periodic tasks)
    beat_scheduler="celery.beat:PersistentScheduler",
    beat_schedule={},  # Will be populated by task modules
    # Worker Configuration
    worker_prefetch_multiplier=4,  # Fetch 4 tasks at a time
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks (prevent memory leaks)
    worker_disable_rate_limits=False,
    # Task Discovery
    include=[
        "app.tasks.email_tasks",
        "app.tasks.analytics_tasks",
        "app.tasks.event_tasks",
    ],
)


# Task base class with custom defaults
class BaseTask(celery_app.Task):  # type: ignore[name-defined]
    """Base task with custom configuration.

    All tasks inherit from this base class to get consistent behavior.
    """

    # Ignore result by default (can be overridden per task)
    ignore_result = False

    # Store errors even if ignore_result is True
    store_errors_even_if_ignored = True

    # Track started state
    track_started = True

    def on_failure(
        self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: object
    ) -> None:
        """Handle task failure.

        Args:
            exc: The exception raised by the task.
            task_id: Unique id of the failed task.
            args: Original arguments for the task.
            kwargs: Original keyword arguments for the task.
            einfo: ExceptionInfo instance with exception traceback.
        """
        # Log failure (will be picked up by structlog)
        print(f"Task {self.name}[{task_id}] failed: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(
        self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: object
    ) -> None:
        """Handle task retry.

        Args:
            exc: The exception that caused the retry.
            task_id: Unique id of the retried task.
            args: Original arguments for the task.
            kwargs: Original keyword arguments for the task.
            einfo: ExceptionInfo instance with exception traceback.
        """
        # Log retry (will be picked up by structlog)
        print(f"Task {self.name}[{task_id}] retrying: {exc}")
        super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval: object, task_id: str, args: tuple, kwargs: dict) -> None:
        """Handle task success.

        Args:
            retval: The return value of the task.
            task_id: Unique id of the executed task.
            args: Original arguments for the task.
            kwargs: Original keyword arguments for the task.
        """
        # Log success (will be picked up by structlog)
        print(f"Task {self.name}[{task_id}] succeeded")
        super().on_success(retval, task_id, args, kwargs)


# Set the base task class
celery_app.Task = BaseTask


if __name__ == "__main__":
    celery_app.start()
