from django.conf import settings


def is_allowed_mime_type(mime_type: str) -> bool:
    return mime_type in settings.ALLOWED_MIME_TYPES


def check_mime_type(mime_type: str):
    if not is_allowed_mime_type(mime_type):
        raise ValueError(f"MIME type {mime_type} not allowed")
