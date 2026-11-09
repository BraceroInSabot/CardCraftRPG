"""Application use cases.

Each class has a single responsibility (one operation) and depends only on
domain abstractions. They are generic over the entity type, so every
resource reuses the same, tested orchestration logic.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import MISSING, dataclass, fields
from typing import Any, Generic, TypeVar

from cardcraft.domain.entities import Entity, NamedEntity
from cardcraft.domain.exceptions import ValidationError
from cardcraft.domain.queries import ListQuery, Page
from cardcraft.domain.repositories import Repository

from .images import RemoveCardImage, SetCardImage
from .ports import ImageInspector, ImageStorage
from .rules import IntegrityRule

E = TypeVar("E", bound=Entity)
C = TypeVar("C", bound=NamedEntity)


def _accepted_input(entity_cls: type[Entity], data: Mapping[str, Any]) -> dict[str, Any]:
    """Drop fields that plain create/update must not set (id, image...)."""
    return {key: value for key, value in data.items() if key not in entity_cls.managed_fields}


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
        entity = build_entity(self._entity_cls, _accepted_input(self._entity_cls, data))
        self._enforce(entity, previous=None)
        return self._repository.add(entity)


class UpdateEntity(_RuleRunner[E]):
    def __init__(self, repository: Repository[E], entity_cls: type[E], rules: Sequence[IntegrityRule[E]] = ()):
        super().__init__(rules)
        self._repository = repository
        self._entity_cls = entity_cls

    def execute(self, entity_id: int, changes: Mapping[str, Any]) -> E:
        current = self._repository.get(entity_id)
        changes = _accepted_input(self._entity_cls, changes)
        entity = build_entity(self._entity_cls, {**current.to_dict(), **changes})
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
    def __init__(self, repository: Repository[E], image_storage: ImageStorage | None = None):
        self._repository = repository
        self._image_storage = image_storage

    def execute(self, entity_id: int) -> None:
        entity = self._repository.get(entity_id)  # raises NotFoundError for unknown ids
        self._repository.delete(entity_id)
        image = getattr(entity, "image", "")
        if image and self._image_storage:
            self._image_storage.delete(image)


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


@dataclass(frozen=True)
class CardUseCases(CrudUseCases[C]):
    """CRUD plus the operations that manage a card's illustration."""

    set_image: SetCardImage[C]
    remove_image: RemoveCardImage[C]

    @classmethod
    def build_for_cards(
        cls,
        repository: Repository[C],
        entity_cls: type[C],
        inspector: ImageInspector,
        storage: ImageStorage,
        rules: Sequence[IntegrityRule[C]] = (),
    ) -> CardUseCases[C]:
        return cls(
            create=CreateEntity(repository, entity_cls, rules),
            update=UpdateEntity(repository, entity_cls, rules),
            get=GetEntity(repository),
            list=ListEntities(repository),
            delete=DeleteEntity(repository, storage),
            set_image=SetCardImage(repository, inspector, storage),
            remove_image=RemoveCardImage(repository, storage),
        )
