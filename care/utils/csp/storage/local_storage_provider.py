# local_storage_provider.py
import logging
import os
from urllib.parse import urljoin

from django.conf import settings

from care.utils.csp.mime_type_utils import check_mime_type

from .base_storage_provider import BaseStorageProvider


class LocalStorageProvider(BaseStorageProvider):

    def __init__(self, bucket_name: str, config: dict):
        self.storage_dir = (
            bucket_name  # For local storage, bucket name is used as the directory path
        )

    def get_signed_upload_url(
        self, filename: str, mime_type: str, expires_in: int
    ) -> str:
        check_mime_type(mime_type)
        return f"file://{os.path.join(self.storage_dir, filename)}"

    def get_signed_download_url(self, filename: str, expires_in: int) -> str:
        # Construct the URL based on MEDIA_URL and the relative path
        relative_path = os.path.relpath(
            os.path.join(self.storage_dir, filename), settings.MEDIA_ROOT
        )
        return urljoin(settings.MEDIA_URL, relative_path)

    def upload_file(self, file: bytes, filename: str, mime_type: str, **kwargs):
        check_mime_type(mime_type)
        file_path = os.path.join(self.storage_dir, filename)
        logging.info(f"Uploading file to {file_path}")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Read bytes from the file object if it's a file-like object
        if hasattr(file, "read"):
            file_content = file.read()
        else:
            file_content = file

        with open(file_path, "wb") as f:
            f.write(file_content)

    def download_file(self, filename: str, **kwargs) -> bytes:
        file_path = os.path.join(self.storage_dir, filename)
        with open(file_path, "rb") as f:
            return f.read()
