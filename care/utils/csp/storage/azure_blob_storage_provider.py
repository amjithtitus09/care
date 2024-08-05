# azure_blob_storage_provider.py
import logging
from datetime import datetime, timedelta

from azure.storage.blob import (
    BlobSasPermissions,
    BlobServiceClient,
    ContentSettings,
    generate_blob_sas,
)

from care.utils.csp.mime_type_utils import check_mime_type

from .base_storage_provider import BaseStorageProvider


class AzureBlobStorageProvider(BaseStorageProvider):

    def __init__(self, container_name: str, config: dict):
        self.container_name = container_name
        self.blob_service_client = BlobServiceClient.from_connection_string(
            config["connection_string"]
        )
        logging.info(
            f"Connected to Azure Blob Storage: {self.blob_service_client.account_name}"
        )
        logging.info(f"Container: {self.container_name}")
        logging.info(f"Connection String: {config['connection_string']}")

    def get_signed_upload_url(
        self, filename: str, mime_type: str, expires_in: int
    ) -> str:
        check_mime_type(mime_type)
        sas_token = generate_blob_sas(
            account_name=self.blob_service_client.account_name,
            container_name=self.container_name,
            blob_name=filename,
            permission=BlobSasPermissions(write=True),
            expiry=datetime.now() + timedelta(seconds=expires_in),
        )
        return f"https://{self.blob_service_client.account_name}.blob.core.windows.net/{self.container_name}/{filename}?{sas_token}"

    def get_signed_download_url(self, filename: str, expires_in: int) -> str:
        sas_token = generate_blob_sas(
            account_name=self.blob_service_client.account_name,
            container_name=self.container_name,
            blob_name=filename,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now() + timedelta(seconds=expires_in),
        )
        return f"https://{self.blob_service_client.account_name}.blob.core.windows.net/{self.container_name}/{filename}?{sas_token}"

    def upload_file(self, file: bytes, filename: str, mime_type: str, **kwargs):
        check_mime_type(mime_type)
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name, blob=filename
        )
        logging.info(f"Uploading file to {self.container_name}")
        logging.info(f"Content Type: {file}")
        blob_client.upload_blob(
            file,
            blob_type="BlockBlob",
            content_settings=ContentSettings(content_type=mime_type),
            overwrite=True,
            **kwargs,
        )

    def download_file(self, filename: str, **kwargs) -> bytes:
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name, blob=filename
        )
        stream = blob_client.download_blob(**kwargs)
        return stream.readall()
