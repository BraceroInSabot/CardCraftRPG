"""Value objects describing how a collection should be listed."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 500


@dataclass(frozen=True)
class ListQuery:
    """A storage-agnostic description of a filtered, ordered, paginated list.

    ``filters`` uses *domain* field names (``system_id``, ``rarity``...).
    ``ordering`` is a domain field name, prefixed with ``-`` for descending.
    """

    search: str = ""
    filters: dict[str, Any] = field(default_factory=dict)
    ids: tuple[int, ...] = ()
    ordering: str = "name"
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE

    def __post_init__(self) -> None:
        object.__setattr__(self, "page", max(1, self.page))
        object.__setattr__(self, "page_size", min(max(1, self.page_size), MAX_PAGE_SIZE))

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


@dataclass(frozen=True)
class Page(Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        return max(1, -(-self.total // self.page_size))
