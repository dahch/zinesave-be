from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, mock_open, patch

from app.domain.models.cloud_connection import CloudConnection
from app.services.cloud.onedrive import OneDriveAdapter


@patch("app.services.cloud.onedrive.requests.put")
@patch("builtins.open", new_callable=mock_open, read_data=b"test")
def test_onedrive_upload_file(mock_file, mock_put):
    adapter = OneDriveAdapter()

    conn = CloudConnection(
        access_token="test",
        refresh_token="ref",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db_mock = Mock()

    mock_upload_resp = Mock()
    mock_upload_resp.status_code = 200
    mock_upload_resp.json.return_value = {"id": "123", "webUrl": "http://link"}
    mock_put.return_value = mock_upload_resp

    result = adapter.upload_file("test.epub", conn, db_mock)

    assert result["id"] == "123"
    assert result["url"] == "http://link"


@patch("app.services.cloud.onedrive.requests.post")
def test_onedrive_refresh_token(mock_post):
    adapter = OneDriveAdapter()

    conn = CloudConnection(
        access_token="old",
        refresh_token="ref",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_mock = Mock()

    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "access_token": "new",
        "refresh_token": "new_ref",
        "expires_in": 3600,
    }
    mock_post.return_value = mock_resp

    adapter._refresh_token_if_needed(conn, db_mock)

    assert conn.access_token == "new"
    assert conn.refresh_token == "new_ref"
    db_mock.commit.assert_called_once()
