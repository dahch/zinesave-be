import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.domain.models.file import File
from app.domain.models.job import Job
from app.domain.models.user import User
from app.services.retention_service import RetentionService


class TestRetentionService(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.service = RetentionService(db=self.mock_db)

    @patch("app.services.retention_service.storage_service")
    def test_cleanup_expired_files(self, mock_storage):
        # Setup data
        User(id="u1", plan="free")
        Job(
            id="j1", user_id="u1", created_at=datetime.now(timezone.utc) - timedelta(days=200)
        )  # > 6 months
        file_to_delete = File(id="f1", job_id="j1", path="s3_key_1", is_deleted=False)

        # Mock DB query result
        # The query chain is complex, so we mock the final .all() return
        self.mock_db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = [
            file_to_delete
        ]

        # Execute
        self.service.cleanup_expired_files(dry_run=False)

        # Assert DB updates
        self.assertTrue(file_to_delete.is_deleted)
        self.assertIsNotNone(file_to_delete.deleted_at)
        self.mock_db.add.assert_called_with(file_to_delete)
        self.mock_db.commit.assert_called_once()

        # Assert Storage deletion
        mock_storage.delete_file.assert_called_with("s3_key_1")

    @patch("app.services.retention_service.storage_service")
    def test_dry_run(self, mock_storage):
        # Setup data
        file_to_delete = File(id="f1", job_id="j1", path="s3_key_1", is_deleted=False)
        self.mock_db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = [
            file_to_delete
        ]

        # Execute
        self.service.cleanup_expired_files(dry_run=True)

        # Assert NO DB updates
        self.assertFalse(file_to_delete.is_deleted)
        self.mock_db.commit.assert_not_called()

        # Assert NO Storage deletion
        mock_storage.delete_file.assert_not_called()


if __name__ == "__main__":
    unittest.main()
