import pytest
from unittest.mock import patch, Mock
import json
from app.services.pipeline_service import run_pipeline, run_composite_pipeline
from app.domain.models.job import Job
from app.domain.models.job_content import JobContent

@patch("app.services.pipeline_service.extract_content")
@patch("app.services.pipeline_service.normalize_html")
@patch("app.services.pipeline_service.generate_epub")
@patch("app.services.pipeline_service.sentry_sdk")
def test_run_pipeline_single(mock_sentry, mock_gen, mock_norm, mock_extract):
    db_mock = Mock()
    job_mock = Job(id="1", base_url="https://example.com")
    db_mock.query().filter().first.return_value = job_mock
    
    run_pipeline("1", lambda: db_mock)
    
    mock_extract.assert_called_once_with(db_mock, job_mock)
    mock_norm.assert_called_once_with(db_mock, job_mock)
    mock_gen.assert_called_once_with(db_mock, job_mock)
    assert job_mock.status == "done"
    assert job_mock.progress == 100

@patch("app.services.pipeline_service.fetch_and_extract")
@patch("app.services.pipeline_service.process_html_normalization")
@patch("app.services.pipeline_service.generate_epub")
@patch("app.services.pipeline_service.sentry_sdk")
def test_run_composite_pipeline(mock_sentry, mock_gen, mock_norm, mock_fetch):
    db_mock = Mock()
    job_mock = Job(id="1", base_url="composite")
    
    meta_content = JobContent(content=json.dumps({"urls": ["https://example.com"], "title": "Test"}))
    
    # query().filter().first() returns meta_content for composite query
    db_mock.query().filter().first.side_effect = [job_mock, meta_content]
    
    mock_fetch.return_value = {"html": "<html></html>", "metadata": {"source": "Test Source"}}
    mock_norm.return_value = {"html": "<html>norm</html>"}
    
    run_pipeline("1", lambda: db_mock)
    
    mock_fetch.assert_called_once_with("https://example.com")
    mock_norm.assert_called_once_with("<html></html>")
    mock_gen.assert_called_once()
    assert job_mock.status == "done"
    
def test_run_pipeline_not_found():
    db_mock = Mock()
    db_mock.query().filter().first.return_value = None
    
    run_pipeline("1", lambda: db_mock)
    db_mock.commit.assert_not_called()

@patch("app.services.pipeline_service.extract_content")
def test_run_pipeline_error(mock_extract):
    db_mock = Mock()
    job_mock = Job(id="1", base_url="https://example.com")
    db_mock.query().filter().first.return_value = job_mock
    
    mock_extract.side_effect = Exception("Test error")
    
    run_pipeline("1", lambda: db_mock)
    
    assert job_mock.status == "failed"
    assert job_mock.error_message == "Test error"
