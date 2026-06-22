from unittest.mock import Mock, patch

import pytest

from app.domain.models.job import Job
from app.services.extract_service import extract_content, fetch_and_extract


@patch("app.services.extract_service.requests.get")
@patch("app.services.extract_service.extract_metadata")
@patch("app.services.extract_service.Document")
def test_fetch_and_extract_success(mock_document, mock_metadata, mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "<html><body><figure><img src='test.jpg' srcset='1' sizes='1' loading='lazy'></figure></body></html>"
    mock_get.return_value = mock_response

    mock_metadata.return_value = {"url": "http://example.com"}

    mock_doc_instance = mock_document.return_value
    mock_doc_instance.summary.return_value = "<p>Extracted content</p>"
    mock_doc_instance.short_title.return_value = "Test Title"

    result = fetch_and_extract("http://example.com")

    assert "Extracted content" in result["html"]
    assert "Test Title" in result["html"]
    assert result["title"] == "Test Title"
    assert result["metadata"]["url"] == "http://example.com"
    mock_get.assert_called_once()
    mock_document.assert_called_once()
    mock_metadata.assert_called_once()


@patch("app.services.extract_service.requests.get")
def test_fetch_and_extract_failure(mock_get):
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = Exception("Not found")
    mock_get.return_value = mock_response

    with pytest.raises(Exception):
        fetch_and_extract("http://example.com")


@patch("app.services.extract_service.fetch_and_extract")
def test_extract_content(mock_fetch):
    db_mock = Mock()
    job_mock = Job(id="1", source_url="http://example.com")

    mock_fetch.return_value = {
        "html": "test",
        "metadata": {"source": "Test"},
        "title": "Test Title",
    }

    extract_content(db_mock, job_mock)

    mock_fetch.assert_called_once_with("http://example.com")
    db_mock.add.assert_called()
    db_mock.commit.assert_called()
