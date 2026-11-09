"""Translation between ORM model instances and domain entities."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Generic, TypeVar

from django.db import models

from cardcraft.domain.entities import Entity

E = TypeVar("E", bound=Entity)


class EntityMapper(Generic[E]):
    """Maps entity fields to model attributes.

    ``renames`` lists the domain fields whose model attribute has a different
    name (e.g. ``class_id`` -> ``character_class_id``); every other field
    maps 1:1.
    """

    def __init__(self, entity_cls: type[E], renames: Mapping[str, str] | None = None):
        self._entity_cls = entity_cls
        self._renames = dict(renames or {})

    def model_attr(self, domain_field: str) -> str:
        return self._renames.get(domain_field, domain_field)

    def to_entity(self, instance: models.Model) -> E:
        data = {name: getattr(instance, self.model_attr(name)) for name in self._entity_cls.field_names()}
        return self._entity_cls(**data)

    def to_model_values(self, entity: E) -> dict[str, Any]:
        values = {self.model_attr(name): value for name, value in entity.to_dict().items() if name != "id"}
        # Enum members are stored by value.
        return {key: getattr(value, "value", value) for key, value in values.items()}
