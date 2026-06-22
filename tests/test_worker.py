from unittest.mock import patch

import pytest

from app.worker import WorkerSettings, execute_pipeline, run_retention_cleanup


@pytest.mark.asyncio
@patch("app.worker.run_pipeline")
@patch("app.worker.sentry_sdk")
async def test_execute_pipeline(mock_sentry, mock_run_pipeline):
    await execute_pipeline({}, "job_123")
    mock_sentry.set_tag.assert_called_with("job_id", "job_123")
    mock_sentry.set_context.assert_called_with("job", {"job_id": "job_123"})


@pytest.mark.asyncio
@patch("app.worker.RetentionService")
@patch("app.worker.sentry_sdk")
async def test_run_retention_cleanup(mock_sentry, mock_retention_service):
    mock_instance = mock_retention_service.return_value
    await run_retention_cleanup({})
    mock_instance.cleanup_expired_files.assert_called_once_with(dry_run=False)


@pytest.mark.asyncio
@patch("app.worker.RetentionService")
@patch("app.worker.sentry_sdk")
async def test_run_retention_cleanup_error(mock_sentry, mock_retention_service):
    mock_instance = mock_retention_service.return_value
    mock_instance.cleanup_expired_files.side_effect = Exception("Test error")
    await run_retention_cleanup({})
    mock_sentry.capture_exception.assert_called_once()


@pytest.mark.asyncio
@patch("app.worker.sentry_sdk")
async def test_worker_settings(mock_sentry):
    settings = WorkerSettings()
    await settings.on_startup()
    await settings.on_shutdown()
    mock_sentry.init.assert_called_once()
