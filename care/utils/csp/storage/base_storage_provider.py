# base_storage_provider.py
from abc import ABC, abstractmethod


class BaseStorageProvider(ABC):

    @abstractmethod
    def get_signed_upload_url(
        self, filename: str, mime_type: str, expires_in: int
    ) -> str:
        pass

    @abstractmethod
    def get_signed_download_url(self, filename: str, expires_in: int) -> str:
        pass

    @abstractmethod
    def upload_file(self, file: bytes, filename: str, mime_type: str, **kwargs):
        pass

    @abstractmethod
    def download_file(self, filename: str, **kwargs) -> bytes:
        pass
