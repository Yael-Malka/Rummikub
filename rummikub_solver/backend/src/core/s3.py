"""S3 upload helpers for play/turn images."""

import logging
import boto3
from botocore.exceptions import ClientError
from src.core.config import settings

logger = logging.getLogger(__name__)

def get_s3_client():
    """Create and return a boto3 S3 client instance for local MinIO."""
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    )

def ensure_bucket_exists():
    """Ensure that the configured S3 bucket exists."""
    s3 = get_s3_client()
    try:
        s3.head_bucket(Bucket=settings.S3_BUCKET_NAME)
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        if error_code == '404' or error_code == 'NoSuchBucket':
            logger.info("Bucket %s does not exist, creating it...", settings.S3_BUCKET_NAME)
            s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)
        else:
            logger.error("Failed to check bucket existence: %s", e)
            raise

def upload_file_to_s3(file_data: bytes, object_name: str, content_type: str = None) -> str:
    """Upload file bytes to the configured MinIO bucket.

    Args:
        file_data (bytes): The raw bytes of the file.
        object_name (str): The destination path/name in the bucket.
        content_type (str, optional): The MIME type of the file.

    Returns:
        str: The object name (path within the bucket).
    """
    s3 = get_s3_client()
    ensure_bucket_exists()

    extra_args = {}
    if content_type:
        extra_args["ContentType"] = content_type

    try:
        s3.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=object_name,
            Body=file_data,
            **extra_args
        )
        logger.info("Successfully uploaded file to S3 (MinIO): %s", object_name)
        return object_name
    except ClientError as e:
        logger.error("Failed to upload file to S3 (MinIO): %s", e)
        raise
