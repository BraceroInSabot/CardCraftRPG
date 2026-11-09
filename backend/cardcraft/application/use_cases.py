"""Application use cases.

Each class has a single responsibility (one operation) and depends only on
domain abstractions. They are generic over the entity type, so every
resource reuses the same, tested orchestration logic.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import MISSING, dataclass, fields
from typing import Any, Generic, TypeVar

from cardcraft.domain.entities import Entity
from cardcraft.domain.exceptions import ValidationError
from cardcraft.domain.queries import ListQuery, Page
from cardcraft.domain.repositories import Repository

from .rules import IntegrityRule

E = TypeVar("E", bound=Entity)


def build_entity(entity_cls: type[E], data: Mapping[str, Any]) -> E:
    """Create an entity from raw data, reporting missing fields as validation errors."""
    known = {f.name: f for f in fields(entity_cls)}
    missing = [
        name
        for name, f in known.items()
        if name not in data and f.default is MISSING and f.default_factory is MISSING
    ]
    if missing:
        raise ValidationError({name: ["This field is required."] for name in missing})
    return entity_cls(**{key: value for key, value in data.items() if key in known})


class _RuleRunner(Generic[E]):
    def __init__(self, rules: Sequence[IntegrityRule[E]]):
        self._rules = tuple(rules)

    def _enforce(self, entity: E, previous: E | None) -> None:
        for rule in self._rules:
            rule.check(entity, previous)


class CreateEntity(_RuleRunner[E]):
    def __init__(self, repository: Repository[E], entity_cls: type[E], rules: Sequence[IntegrityRule[E]] = ()):
        super().__init__(rules)
        self._repository = repository
        self._entity_cls = entity_cls

    def execute(self, data: Mapping[str, Any]) -> E:
        entity = build_entity(self._entity_cls, {**data, "id": None})
        self._enforce(entity, previous=None)
        return self._repository.add(entity)


class UpdateEntity(_RuleRunner[E]):
    def __init__(self, repository: Repository[E], entity_cls: type[E], rules: Sequence[IntegrityRule[E]] = ()):
        super().__init__(rules)
        self._repository = repository
        self._entity_cls = entity_cls

    def execute(self, entity_id: int, changes: Mapping[str, Any]) -> E:
        current = self._repository.get(entity_id)
        entity = build_entity(self._entity_cls, {**current.to_dict(), **changes, "id": entity_id})
        self._enforce(entity, previous=current)
        return self._repository.update(entity)


class GetEntity(Generic[E]):
    def __init__(self, repository: Repository[E]):
        self._repository = repository

    def execute(self, entity_id: int) -> E:
        return self._repository.get(entity_id)


class ListEntities(Generic[E]):
    def __init__(self, repository: Repository[E]):
        self._repository = repository

    def execute(self, query: ListQuery) -> Page[E]:
        return self._repository.list(query)


class DeleteEntity(Generic[E]):
    def __init__(self, repository: Repository[E]):
        self._repository = repository

    def execute(self, entity_id: int) -> None:
        self._repository.get(entity_id)  # raises NotFoundError for unknown ids
        self._repository.delete(entity_id)


@dataclass(frozen=True)
class CrudUseCases(Generic[E]):
    """The complete set of operations offered for one resource."""

    create: CreateEntity[E]
    update: UpdateEntity[E]
    get: GetEntity[E]
    list: ListEntities[E]
    delete: DeleteEntity[E]

    @classmethod
    def build(
        cls,
        repository: Repository[E],
        entity_cls: type[E],
        rules: Sequence[IntegrityRule[E]] = (),
    ) -> CrudUseCases[E]:
        return cls(
            create=CreateEntity(repository, entity_cls, rules),
            update=UpdateEntity(repository, entity_cls, rules),
            get=GetEntity(repository),
            list=ListEntities(repository),
            delete=DeleteEntity(repository),
        )
