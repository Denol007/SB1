"""Email tasks for sending notifications and alerts.

This module will contain Celery tasks for:
- Sending verification emails
- Sending event reminders
- Sending notification emails
- Sending password reset emails
"""

from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, name="app.tasks.email_tasks.send_email")
def send_email(self, to: str, subject: str, body: str) -> dict[str, str]:
    """Send an email (placeholder task).

    Args:
        to: Recipient email address.
        subject: Email subject.
        body: Email body (HTML or plain text).

    Returns:
        dict with status and message.
    """
    # TODO: Implement actual email sending in later tasks
    return {"status": "success", "message": f"Email sent to {to}"}
