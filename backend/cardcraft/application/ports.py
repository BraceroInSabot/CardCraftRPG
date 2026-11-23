"""Ports for external services the application needs (besides repositories).

Implementations live in ``cardcraft.infrastructure``; tests use fakes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ImageUpload:
    content: bytes
    filename: str = ""


class ImageInspector(ABC):
    @abstractmethod
    def detect_format(self, content: bytes) -> str | None:
        """Return the real format of the bytes (``png``, ``jpeg``...) or ``None`` if not an image."""


class ImageStorage(ABC):
    @abstractmethod
    def save(self, content: bytes, extension: str) -> str:
        """Store the bytes and return a storage key."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove a stored file. Unknown keys are ignored."""

    @abstractmethod
    def url(self, key: str) -> str:
        """Public URL for a stored file."""


class PasswordService(ABC):
    """Credential checks for a Master. Hashing and password policy live behind this port."""

    @abstractmethod
    def verify(self, master_id: int, raw_password: str) -> bool: ...

    @abstractmethod
    def validate(self, master_id: int, raw_password: str) -> None:
        """Raise ``ValidationError`` (field ``new_password``) if the password is too weak."""

    @abstractmethod
    def change(self, master_id: int, raw_password: str) -> None: ...
