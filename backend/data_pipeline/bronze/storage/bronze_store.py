from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

from backend.data_pipeline.config.settings import EnvironmentSettings
from backend.data_pipeline.config.constants import DataSourceName


class BronzeObjectStore:
    """Manages raw JSON payload storage in AWS S3."""

    def __init__(self, settings: EnvironmentSettings) -> None:
        self.settings = settings
        self.bucket_name = settings.bronze_s3_bucket
        self._s3_client = boto3.client(
            "s3",
            region_name=settings.bronze_s3_region,
            aws_access_key_id=settings.bronze_s3_access_key or None,
            aws_secret_access_key=settings.bronze_s3_secret_key or None,
        )

    def ensure_bucket_exists(self) -> None:
        """Create the bronze bucket if it does not already exist."""
        try:
            self._s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            create_kwargs: dict = {"Bucket": self.bucket_name}
            if self.settings.bronze_s3_region != "us-east-1":
                create_kwargs["CreateBucketConfiguration"] = {
                    "LocationConstraint": self.settings.bronze_s3_region
                }
            self._s3_client.create_bucket(**create_kwargs)

    def store_raw_payload(
        self,
        source_name: DataSourceName,
        envelope: dict,
    ) -> str:
        """Serialize and upload a bronze envelope to S3.

        Returns the generated object key.
        """
        now = datetime.now(timezone.utc)
        object_key = (
            f"{source_name.value}"
            f"/{now.year:04d}"
            f"/{now.month:02d}"
            f"/{now.day:02d}"
            f"/{uuid.uuid4()}.json"
        )

        serialized_payload = json.dumps(envelope, default=str)

        self._s3_client.put_object(
            Bucket=self.bucket_name,
            Key=object_key,
            Body=serialized_payload.encode("utf-8"),
            ContentType="application/json",
        )

        return object_key

    def retrieve_raw_payload(self, object_key: str) -> dict:
        """Download and deserialize a bronze envelope from S3."""
        response = self._s3_client.get_object(
            Bucket=self.bucket_name,
            Key=object_key,
        )
        raw_bytes = response["Body"].read()
        return json.loads(raw_bytes)
