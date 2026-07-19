"""S3 download helpers for task images."""

import logging
import boto3
from botocore.exceptions import ClientError
from src.config import settings

logger = logging.getLogger(__name__)

def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    )

def download_file_from_s3(object_name: str, local_file_path: str) -> None:
    s3 = get_s3_client()
    try:
        s3.download_file(
            Bucket=settings.S3_BUCKET_NAME,
            Key=object_name,
            Filename=local_file_path,
        )
        logger.info("Successfully downloaded S3 object %s to %s", object_name, local_file_path)
    except ClientError as e:
        logger.error("Failed to download file from S3: %s", e)
        raise
