"""Repository ports.

The application layer depends on these abstractions (Dependency Inversion);
concrete implementations live in ``cardcraft.infrastructure``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from .entities import Entity
from .queries import ListQuery, Page

E = TypeVar("E", bound=Entity)


class Repository(ABC, Generic[E]):
    @abstractmethod
    def get(self, entity_id: int) -> E:
        """Return the entity or raise ``NotFoundError``."""

    @abstractmethod
    def exists(self, entity_id: int) -> bool: ...

    @abstractmethod
    def list(self, query: ListQuery) -> Page[E]: ...

    @abstractmethod
    def add(self, entity: E) -> E:
        """Persist a new entity and return it with its identity assigned."""

    @abstractmethod
    def update(self, entity: E) -> E: ...

    @abstractmethod
    def delete(self, entity_id: int) -> None: ...
