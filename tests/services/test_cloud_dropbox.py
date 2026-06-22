import pytest
from unittest.mock import patch, Mock, mock_open
from datetime import datetime, timedelta, timezone
from app.services.cloud.dropbox import DropboxAdapter
from app.domain.models.cloud_connection import CloudConnection

@patch("app.services.cloud.dropbox.requests.post")
@patch("app.services.cloud.dropbox.os.path.getsize", return_value=100)
@patch("builtins.open", new_callable=mock_open, read_data=b"test")
def test_dropbox_upload_file(mock_file, mock_getsize, mock_post):
    adapter = DropboxAdapter()
    
    conn = CloudConnection(access_token="test", refresh_token="ref", expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
    db_mock = Mock()
    
    mock_upload_resp = Mock()
    mock_upload_resp.status_code = 200
    mock_upload_resp.json.return_value = {"id": "123"}
    
    mock_link_resp = Mock()
    mock_link_resp.status_code = 200
    mock_link_resp.json.return_value = {"url": "http://link"}
    
    mock_post.side_effect = [mock_upload_resp, mock_link_resp]
    
    result = adapter.upload_file("test.epub", conn, db_mock)
    
    assert result["id"] == "123"
    assert result["url"] == "http://link"

@patch("app.services.cloud.dropbox.requests.post")
def test_dropbox_refresh_token(mock_post):
    adapter = DropboxAdapter()
    
    conn = CloudConnection(access_token="old", refresh_token="ref", expires_at=datetime.now(timezone.utc) - timedelta(hours=1))
    db_mock = Mock()
    
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"access_token": "new", "expires_in": 14400}
    mock_post.return_value = mock_resp
    
    adapter._refresh_token_if_needed(conn, db_mock)
    
    assert conn.access_token == "new"
    db_mock.commit.assert_called_once()
