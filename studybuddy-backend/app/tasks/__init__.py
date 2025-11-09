"""Background tasks package.

This package contains Celery tasks for asynchronous operations:
- celery_app.py: Main Celery application configuration
- email_tasks.py: Email sending tasks
- analytics_tasks.py: Analytics aggregation tasks
- event_tasks.py: Event reminder and notification tasks
"""

from app.tasks.celery_app import celery_app

__all__ = ["celery_app"]
