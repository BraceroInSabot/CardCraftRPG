"""Use cases that manage the illustration printed on a card."""

from __future__ import annotations

from dataclasses import replace
from typing import Generic, TypeVar

from cardcraft.domain.entities import NamedEntity
from cardcraft.domain.exceptions import ValidationError
from cardcraft.domain.repositories import Repository

from .ports import ImageInspector, ImageStorage, ImageUpload

E = TypeVar("E", bound=NamedEntity)

ALLOWED_IMAGE_FORMATS = frozenset({"png", "jpeg", "webp", "gif"})
MAX_IMAGE_BYTES = 5 * 1024 * 1024


class SetCardImage(Generic[E]):
    """Validate an upload, store it and attach it to the card (replacing any previous image)."""

    def __init__(
        self,
        repository: Repository[E],
        inspector: ImageInspector,
        storage: ImageStorage,
        max_bytes: int = MAX_IMAGE_BYTES,
    ):
        self._repository = repository
        self._inspector = inspector
        self._storage = storage
        self._max_bytes = max_bytes

    def execute(self, entity_id: int, upload: ImageUpload) -> E:
        entity = self._repository.get(entity_id)
        image_format = self._validated_format(upload)

        key = self._storage.save(upload.content, image_format)
        try:
            updated = self._repository.update(replace(entity, image=key))
        except Exception:
            self._storage.delete(key)
            raise

        if entity.has_image:
            self._storage.delete(entity.image)
        return updated

    def _validated_format(self, upload: ImageUpload) -> str:
        if not upload.content:
            raise ValidationError.single("image", "The file is empty.")
        if len(upload.content) > self._max_bytes:
            limit_mb = self._max_bytes // (1024 * 1024)
            raise ValidationError.single("image", f"Images must be at most {limit_mb} MB.")
        image_format = self._inspector.detect_format(upload.content)
        if image_format not in ALLOWED_IMAGE_FORMATS:
            raise ValidationError.single("image", "Upload a PNG, JPEG, WebP or GIF image.")
        return image_format


class RemoveCardImage(Generic[E]):
    def __init__(self, repository: Repository[E], storage: ImageStorage):
        self._repository = repository
        self._storage = storage

    def execute(self, entity_id: int) -> E:
        entity = self._repository.get(entity_id)
        if not entity.has_image:
            return entity
        updated = self._repository.update(replace(entity, image=""))
        self._storage.delete(entity.image)
        return updated
