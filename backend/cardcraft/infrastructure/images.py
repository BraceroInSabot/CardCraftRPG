"""Image adapters: Pillow for inspection, Django's storage API for files."""

from __future__ import annotations

import uuid
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.files.storage import Storage, default_storage
from PIL import Image, UnidentifiedImageError

from cardcraft.application.ports import ImageInspector, ImageStorage


class PillowImageInspector(ImageInspector):
    def detect_format(self, content: bytes) -> str | None:
        try:
            with Image.open(BytesIO(content)) as image:
                image.verify()  # detects truncated or corrupt files
                return (image.format or "").lower() or None
        except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
            return None


class DjangoImageStorage(ImageStorage):
    """Stores card images through a Django ``Storage`` (local disk by default, S3 etc. via settings)."""

    def __init__(self, folder: str = "cards", storage: Storage | None = None):
        self._folder = folder
        self._storage = storage

    @property
    def _backend(self) -> Storage:
        # Resolved lazily so settings overrides (e.g. in tests) are honoured.
        return self._storage or default_storage

    def save(self, content: bytes, extension: str) -> str:
        name = f"{self._folder}/{uuid.uuid4().hex}.{extension}"
        return self._backend.save(name, ContentFile(content))

    def delete(self, key: str) -> None:
        if key and self._backend.exists(key):
            self._backend.delete(key)

    def url(self, key: str) -> str:
        return self._backend.url(key) if key else ""
