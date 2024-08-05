# s3_storage_provider.py

import boto3
from botocore.exceptions import NoCredentialsError

from care.utils.csp.mime_type_utils import check_mime_type

from .base_storage_provider import BaseStorageProvider


class S3StorageProvider(BaseStorageProvider):

    def __init__(self, bucket_name: str, config: dict):
        self.bucket_name = bucket_name
        self.s3 = boto3.client("s3", **config)

    def get_signed_upload_url(
        self, filename: str, mime_type: str, expires_in: int
    ) -> str:
        check_mime_type(mime_type)
        return self.s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": filename,
                "ContentType": mime_type,
            },
            ExpiresIn=expires_in,
        )

    def get_signed_download_url(self, filename: str, expires_in: int) -> str:
        return self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": filename},
            ExpiresIn=expires_in,
        )

    def upload_file(self, file: bytes, filename: str, mime_type: str, **kwargs):
        check_mime_type(mime_type)
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=file,
                ContentType=mime_type,
                **kwargs,
            )
        except NoCredentialsError:
            print("Credentials not available")

    def download_file(self, filename: str, **kwargs) -> bytes:
        obj = self.s3.get_object(Bucket=self.bucket_name, Key=filename, **kwargs)
        return obj["Body"].read()
