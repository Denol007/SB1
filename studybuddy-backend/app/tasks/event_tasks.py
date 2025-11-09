"""Event tasks for reminders and notifications.

This module will contain Celery tasks for:
- Sending event reminders (24h before, 1h before)
- Sending event cancellation notices
- Sending event update notifications
"""

from typing import Any

from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, name="app.tasks.event_tasks.send_event_reminder")
def send_event_reminder(self: Any, event_id: str) -> dict[str, str]:
    """Send event reminder to registered participants (placeholder task).

    Args:
        event_id: UUID of the event.

    Returns:
        dict with status and message.
    """
    # TODO: Implement actual event reminder sending in later tasks
    return {"status": "success", "message": f"Reminder sent for event {event_id}"}
