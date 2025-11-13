"""Unit tests for Celery application configuration.

Following TDD principles:
1. Write tests FIRST (they should FAIL)
2. Implement the feature
3. Run tests (they should PASS)
4. Refactor while keeping tests passing
"""

import pytest

from app.tasks.celery_app import celery_app


class TestCeleryConfiguration:
    """Test cases for Celery app configuration."""

    def test_celery_app_exists(self):
        """Test that celery_app instance exists."""
        assert celery_app is not None

    def test_celery_app_name(self):
        """Test that Celery app has correct name."""
        assert celery_app.main == "studybuddy"

    def test_broker_url_configured(self):
        """Test that broker URL is configured from settings."""
        assert celery_app.conf.broker_url is not None
        assert "redis://" in celery_app.conf.broker_url

    def test_result_backend_configured(self):
        """Test that result backend is configured."""
        assert celery_app.conf.result_backend is not None
        assert "redis://" in celery_app.conf.result_backend

    def test_task_serializer_is_json(self):
        """Test that task serializer is set to JSON."""
        assert celery_app.conf.task_serializer == "json"

    def test_result_serializer_is_json(self):
        """Test that result serializer is set to JSON."""
        assert celery_app.conf.result_serializer == "json"

    def test_accept_content_includes_json(self):
        """Test that accept_content includes JSON."""
        assert "json" in celery_app.conf.accept_content

    def test_timezone_is_utc(self):
        """Test that timezone is set to UTC."""
        assert celery_app.conf.timezone == "UTC"

    def test_enable_utc_is_true(self):
        """Test that enable_utc is True."""
        assert celery_app.conf.enable_utc is True

    def test_task_track_started_is_true(self):
        """Test that task_track_started is enabled."""
        assert celery_app.conf.task_track_started is True

    def test_task_time_limit_configured(self):
        """Test that task_time_limit is configured."""
        assert celery_app.conf.task_time_limit is not None
        assert celery_app.conf.task_time_limit > 0

    def test_task_soft_time_limit_configured(self):
        """Test that task_soft_time_limit is configured."""
        assert celery_app.conf.task_soft_time_limit is not None
        assert celery_app.conf.task_soft_time_limit > 0
        # Soft limit should be less than hard limit
        assert celery_app.conf.task_soft_time_limit < celery_app.conf.task_time_limit


class TestCeleryRetryConfiguration:
    """Test cases for Celery retry configuration."""

    def test_task_autoretry_for_configured(self):
        """Test that task_autoretry_for includes common exceptions."""
        assert celery_app.conf.task_autoretry_for is not None
        # Should retry on Exception
        assert Exception in celery_app.conf.task_autoretry_for

    def test_task_retry_backoff_configured(self):
        """Test that retry backoff is configured."""
        # Exponential backoff should be enabled
        assert celery_app.conf.task_retry_backoff is not None
        assert celery_app.conf.task_retry_backoff is True

    def test_task_retry_backoff_max_configured(self):
        """Test that maximum retry backoff is configured."""
        assert celery_app.conf.task_retry_backoff_max is not None
        assert celery_app.conf.task_retry_backoff_max > 0

    def test_task_retry_jitter_configured(self):
        """Test that retry jitter is enabled to prevent thundering herd."""
        assert celery_app.conf.task_retry_jitter is not None
        assert celery_app.conf.task_retry_jitter is True

    def test_task_max_retries_configured(self):
        """Test that max retries is configured."""
        assert celery_app.conf.task_max_retries is not None
        assert celery_app.conf.task_max_retries >= 3


class TestCeleryTaskRouting:
    """Test cases for Celery task routing configuration."""

    def test_task_routes_configured(self):
        """Test that task routes are configured."""
        assert celery_app.conf.task_routes is not None
        assert isinstance(celery_app.conf.task_routes, dict)

    def test_email_tasks_routed_to_email_queue(self):
        """Test that email tasks are routed to email queue."""
        routes = celery_app.conf.task_routes
        # Email tasks should go to 'email' queue
        email_route = routes.get("app.tasks.email_tasks.*")
        assert email_route is not None
        assert email_route.get("queue") == "email"

    def test_default_queue_configured(self):
        """Test that default queue is configured."""
        assert celery_app.conf.task_default_queue is not None
        assert celery_app.conf.task_default_queue == "default"

    def test_task_create_missing_queues(self):
        """Test that Celery will create missing queues."""
        # This prevents errors when queues don't exist
        assert celery_app.conf.task_create_missing_queues is True


class TestCeleryResultBackend:
    """Test cases for Celery result backend configuration."""

    def test_result_expires_configured(self):
        """Test that result expiration is configured."""
        assert celery_app.conf.result_expires is not None
        assert celery_app.conf.result_expires > 0
        # Should be reasonable (e.g., 1 day = 86400 seconds)
        assert celery_app.conf.result_expires >= 3600  # At least 1 hour

    def test_result_persistent_configured(self):
        """Test that result persistence is configured."""
        # Results should be persisted for reliability
        assert celery_app.conf.result_persistent is not None


class TestCeleryBeatSchedule:
    """Test cases for Celery Beat periodic tasks configuration."""

    def test_beat_schedule_exists(self):
        """Test that beat_schedule is configured (even if empty initially)."""
        # beat_schedule should exist (can be empty dict initially)
        assert hasattr(celery_app.conf, "beat_schedule")

    def test_beat_scheduler_configured(self):
        """Test that beat scheduler is configured."""
        # Using database scheduler or default
        assert celery_app.conf.beat_scheduler is not None


class TestCeleryWorkerConfiguration:
    """Test cases for Celery worker configuration."""

    def test_worker_prefetch_multiplier_configured(self):
        """Test that worker prefetch multiplier is configured."""
        assert celery_app.conf.worker_prefetch_multiplier is not None
        # Should be reasonable (1-4 for I/O bound tasks)
        assert 1 <= celery_app.conf.worker_prefetch_multiplier <= 10

    def test_worker_max_tasks_per_child_configured(self):
        """Test that max tasks per child is configured to prevent memory leaks."""
        assert celery_app.conf.worker_max_tasks_per_child is not None
        # Should recycle workers after N tasks
        assert celery_app.conf.worker_max_tasks_per_child > 0

    def test_worker_disable_rate_limits_configured(self):
        """Test that rate limits configuration exists."""
        # This is optional but should be defined
        assert hasattr(celery_app.conf, "worker_disable_rate_limits")


class TestCeleryTaskDiscovery:
    """Test cases for Celery task autodiscovery."""

    def test_celery_imports_configured(self):
        """Test that Celery is configured to import task modules."""
        # Should have imports or autodiscover configured
        assert hasattr(celery_app.conf, "imports") or hasattr(celery_app, "autodiscover_tasks")

    def test_celery_include_configured(self):
        """Test that task modules are included."""
        # Either through conf.include or autodiscover_tasks
        if hasattr(celery_app.conf, "include"):
            assert celery_app.conf.include is not None


class TestCeleryBaseTask:
    """Test cases for BaseTask class."""

    def test_base_task_exists(self):
        """Test that BaseTask is configured."""
        assert celery_app.Task is not None

    def test_base_task_ignore_result_default(self):
        """Test that ignore_result has expected default."""
        task_instance = celery_app.Task()
        assert hasattr(task_instance, "ignore_result")
        assert task_instance.ignore_result is False

    def test_base_task_store_errors_configured(self):
        """Test that store_errors_even_if_ignored is configured."""
        task_instance = celery_app.Task()
        assert hasattr(task_instance, "store_errors_even_if_ignored")
        assert task_instance.store_errors_even_if_ignored is True

    def test_base_task_track_started_configured(self):
        """Test that track_started is configured."""
        task_instance = celery_app.Task()
        assert hasattr(task_instance, "track_started")
        assert task_instance.track_started is True

    def test_base_task_has_on_failure_handler(self):
        """Test that BaseTask has on_failure handler."""
        task_instance = celery_app.Task()
        assert hasattr(task_instance, "on_failure")
        assert callable(task_instance.on_failure)

    def test_base_task_has_on_retry_handler(self):
        """Test that BaseTask has on_retry handler."""
        task_instance = celery_app.Task()
        assert hasattr(task_instance, "on_retry")
        assert callable(task_instance.on_retry)

    def test_base_task_has_on_success_handler(self):
        """Test that BaseTask has on_success handler."""
        task_instance = celery_app.Task()
        assert hasattr(task_instance, "on_success")
        assert callable(task_instance.on_success)


class TestPlaceholderTasks:
    """Test cases for placeholder task modules."""

    def test_email_tasks_module_imported(self):
        """Test that email_tasks module is included."""
        assert "app.tasks.email_tasks" in celery_app.conf.include

    def test_analytics_tasks_module_imported(self):
        """Test that analytics_tasks module is included."""
        assert "app.tasks.analytics_tasks" in celery_app.conf.include

    def test_event_tasks_module_imported(self):
        """Test that event_tasks module is included."""
        assert "app.tasks.event_tasks" in celery_app.conf.include

    def test_can_import_email_tasks(self):
        """Test that email_tasks module can be imported."""
        from app.tasks import email_tasks

        assert hasattr(email_tasks, "send_verification_email")

    def test_can_import_analytics_tasks(self):
        """Test that analytics_tasks module can be imported."""
        from app.tasks import analytics_tasks

        assert hasattr(analytics_tasks, "aggregate_metrics")

    def test_can_import_event_tasks(self):
        """Test that event_tasks module can be imported."""
        from app.tasks import event_tasks

        assert hasattr(event_tasks, "send_event_reminders")

    def test_send_verification_email_task_callable(self):
        """Test that send_verification_email task is callable."""
        from app.tasks.email_tasks import send_verification_email

        assert callable(send_verification_email)
        # Test with delay() method (async task call)
        assert hasattr(send_verification_email, "delay")

    def test_aggregate_metrics_task_callable(self):
        """Test that aggregate_metrics task is callable."""
        from app.tasks.analytics_tasks import aggregate_metrics

        assert callable(aggregate_metrics)
        assert hasattr(aggregate_metrics, "delay")

    def test_send_event_reminder_task_callable(self):
        """Test that send_event_reminders task is callable."""
        from app.tasks.event_tasks import send_event_reminders

        assert callable(send_event_reminders)
        assert hasattr(send_event_reminders, "delay")


class TestTaskExecution:
    """Test cases for task execution and callbacks."""

    def test_analytics_task_execution(self):
        """Test that analytics task executes successfully."""
        from app.tasks.analytics_tasks import aggregate_metrics

        result = aggregate_metrics("daily")
        assert result["status"] == "success"
        assert "daily" in result["message"]

    @pytest.mark.skip(reason="Integration test - requires database connection")
    def test_event_reminder_task_execution(self):
        """Test that event reminders task executes successfully."""
        from app.tasks.event_tasks import send_event_reminders

        result = send_event_reminders()
        assert result["status"] == "success"

    def test_base_task_on_failure(self, capsys):
        """Test that BaseTask.on_failure logs correctly."""
        from app.tasks.celery_app import BaseTask

        task = BaseTask()
        task.name = "test_task"
        exc = Exception("Test error")
        task.on_failure(exc, "task-123", [], {}, None)

        captured = capsys.readouterr()
        assert "test_task" in captured.out
        assert "task-123" in captured.out
        assert "failed" in captured.out

    def test_base_task_on_retry(self, capsys):
        """Test that BaseTask.on_retry logs correctly."""
        from app.tasks.celery_app import BaseTask

        task = BaseTask()
        task.name = "test_task"
        exc = Exception("Test error")
        task.on_retry(exc, "task-123", [], {}, None)

        captured = capsys.readouterr()
        assert "test_task" in captured.out
        assert "task-123" in captured.out
        assert "retrying" in captured.out

    def test_base_task_on_success(self, capsys):
        """Test that BaseTask.on_success logs correctly."""
        from app.tasks.celery_app import BaseTask

        task = BaseTask()
        task.name = "test_task"
        task.on_success({"result": "success"}, "task-123", [], {})

        captured = capsys.readouterr()
        assert "test_task" in captured.out
        assert "task-123" in captured.out
        assert "succeeded" in captured.out
