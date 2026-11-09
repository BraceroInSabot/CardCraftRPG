"""In-memory repository used to test the application layer without a database."""

from __future__ import annotations

from dataclasses import replace
from typing import Generic, TypeVar

from cardcraft.domain.entities import Entity
from cardcraft.domain.exceptions import NotFoundError
from cardcraft.domain.queries import ListQuery, Page
from cardcraft.domain.repositories import Repository

E = TypeVar("E", bound=Entity)


class InMemoryRepository(Repository[E], Generic[E]):
    def __init__(self, entity_cls: type[E]):
        self._entity_cls = entity_cls
        self._rows: dict[int, E] = {}
        self._next_id = 1

    def get(self, entity_id: int) -> E:
        if entity_id not in self._rows:
            raise NotFoundError(self._entity_cls.entity_name, entity_id)
        return self._rows[entity_id]

    def exists(self, entity_id: int) -> bool:
        return entity_id in self._rows

    def list(self, query: ListQuery) -> Page[E]:
        rows = list(self._rows.values())
        if query.ids:
            rows = [r for r in rows if r.id in query.ids]
        if query.search:
            needle = query.search.lower()
            rows = [r for r in rows if needle in r.name.lower() or needle in r.description.lower()]
        for key, value in query.filters.items():
            rows = [r for r in rows if getattr(r, key, None) == value]
        key = query.ordering.lstrip("-")
        rows.sort(key=lambda r: getattr(r, key), reverse=query.ordering.startswith("-"))
        window = rows[query.offset : query.offset + query.page_size]
        return Page(items=window, total=len(rows), page=query.page, page_size=query.page_size)

    def add(self, entity: E) -> E:
        stored = replace(entity, id=self._next_id)
        self._rows[stored.id] = stored
        self._next_id += 1
        return stored

    def update(self, entity: E) -> E:
        self.get(entity.id)
        self._rows[entity.id] = entity
        return entity

    def delete(self, entity_id: int) -> None:
        self._rows.pop(entity_id, None)
