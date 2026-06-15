import logging

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.bucket = settings.B2_BUCKET_NAME
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.B2_ENDPOINT_URL,
            aws_access_key_id=settings.B2_KEY_ID,
            aws_secret_access_key=settings.B2_APPLICATION_KEY,
            config=Config(signature_version="s3v4")
        )

    def upload_file(self, file_obj, key: str, content_type: str = "application/epub+zip"):
        """Uploads a file-like object to B2."""
        try:
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket,
                key,
                ExtraArgs={"ContentType": content_type}
            )
            return key
        except ClientError as e:
            logger.error(f"Failed to upload file to B2: {e}")
            raise e

    def generate_presigned_url(self, key: str, expiration=3600):
        """Generates a presigned URL for downloading a file."""
        try:
            response = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None

    def download_file(self, key: str, destination_path: str):
        """Downloads a file from B2 to a local path."""
        try:
            self.s3_client.download_file(self.bucket, key, destination_path)
        except ClientError as e:
            logger.error(f"Failed to download file from B2: {e}")
            raise e

    def delete_file(self, key: str):
        """Deletes a file from B2."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
        except ClientError as e:
            logger.error(f"Failed to delete file from B2: {e}")
            raise e

storage_service = StorageService()
