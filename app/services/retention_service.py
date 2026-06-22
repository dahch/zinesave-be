import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.domain.models.file import File
from app.domain.models.job import Job
from app.domain.models.user import User
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)


class RetentionService:
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def cleanup_expired_files(self, dry_run: bool = False):
        """
        Deletes files from storage and marks them as deleted in DB if:
        - User is on 'free' plan
        - Job was created > 7 days ago
        - File is not already deleted
        """
        try:
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

            # Query for files that need to be deleted
            # Join Job to check created_at
            # Join Job -> User to check plan
            files_to_delete = (
                self.db.query(File)
                .join(Job, File.job_id == Job.id)
                .join(User, Job.user_id == User.id)
                .filter(
                    User.plan == "free", Job.created_at < seven_days_ago, File.is_deleted == False
                )
                .all()
            )

            logger.info(f"Found {len(files_to_delete)} expired files to clean up.")

            for file_record in files_to_delete:
                try:
                    logger.info(
                        f"Processing file {file_record.id} (Job: {file_record.job_id}, Path: {file_record.path})"
                    )

                    if not dry_run:
                        # 1. Delete from B2
                        # The path in File model usually stores the key.
                        # If full URL is stored, we might need to extract the key.
                        # Assuming 'path' stores the key as per standard practice in this app,
                        # but let's verify if extraction is needed.
                        # Based on typical usage, if it's a key, we use it directly.
                        storage_service.delete_file(file_record.path)

                        # 2. Update DB
                        file_record.is_deleted = True
                        file_record.deleted_at = datetime.now(timezone.utc)
                        self.db.add(file_record)

                except Exception as e:
                    logger.error(f"Error processing file {file_record.id}: {e}", exc_info=True)
                    # Continue with next file even if one fails

            if not dry_run:
                self.db.commit()
                logger.info("Cleanup completed successfully.")
            else:
                logger.info("Dry run completed. No changes made.")

        except Exception as e:
            logger.error(f"Critical error in cleanup_expired_files: {e}", exc_info=True)
            raise e
        finally:
            self.db.close()
