import logging

from django.conf import settings

from care.utils.csp.config import BucketType, CSProvider, get_client_config
from care.utils.csp.storage.azure_blob_storage_provider import AzureBlobStorageProvider
from care.utils.csp.storage.local_storage_provider import LocalStorageProvider
from care.utils.csp.storage.s3_storage_provider import S3StorageProvider


def get_storage_provider(bucket_type=BucketType.PATIENT, external=False):
    config, bucket_name = get_client_config(bucket_type, external)
    logging.info("PROVIDER " + settings.CS_PROVIDER)
    if settings.CS_PROVIDER == CSProvider.AWS.value:
        return S3StorageProvider(bucket_name, config)
    elif settings.CS_PROVIDER == CSProvider.AZURE.value:
        return AzureBlobStorageProvider(bucket_name, config)
    elif settings.CS_PROVIDER == CSProvider.LOCAL.value:
        return LocalStorageProvider(bucket_name, config)
    else:
        raise ValueError("Unsupported storage provider")
