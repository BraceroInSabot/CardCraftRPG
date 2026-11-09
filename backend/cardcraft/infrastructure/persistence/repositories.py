"""Django ORM implementation of the domain ``Repository`` port."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from functools import reduce
from operator import or_
from typing import Generic, TypeVar

from django.db import models

from cardcraft.domain.entities import Entity
from cardcraft.domain.exceptions import NotFoundError
from cardcraft.domain.queries import ListQuery, Page
from cardcraft.domain.repositories import Repository

from .mappers import EntityMapper

E = TypeVar("E", bound=Entity)


class DjangoRepository(Repository[E], Generic[E]):
    def __init__(
        self,
        model: type[models.Model],
        entity_cls: type[E],
        mapper: EntityMapper[E] | None = None,
        search_fields: Sequence[str] = ("name", "description"),
        default_ordering: str = "name",
        related_filters: Mapping[str, str] | None = None,
    ):
        self._model = model
        self._entity_cls = entity_cls
        self._mapper = mapper or EntityMapper(entity_cls)
        self._search_fields = tuple(search_fields)
        self._default_ordering = default_ordering
        # Filters on fields of related entities, e.g. {"system_id": "race__system_id"}.
        self._related_filters = dict(related_filters or {})

    # -- reads -------------------------------------------------------------

    def get(self, entity_id: int) -> E:
        try:
            return self._mapper.to_entity(self._model.objects.get(pk=entity_id))
        except self._model.DoesNotExist:
            raise NotFoundError(self._entity_cls.entity_name, entity_id) from None

    def exists(self, entity_id: int) -> bool:
        return self._model.objects.filter(pk=entity_id).exists()

    def list(self, query: ListQuery) -> Page[E]:
        queryset = self._apply_ordering(self._filtered(query), query.ordering)
        total = queryset.count()
        rows = queryset[query.offset : query.offset + query.page_size]
        return Page(
            items=[self._mapper.to_entity(row) for row in rows],
            total=total,
            page=query.page,
            page_size=query.page_size,
        )

    # -- writes ------------------------------------------------------------

    def add(self, entity: E) -> E:
        instance = self._model.objects.create(**self._mapper.to_model_values(entity))
        return self._mapper.to_entity(instance)

    def update(self, entity: E) -> E:
        try:
            instance = self._model.objects.get(pk=entity.id)
        except self._model.DoesNotExist:
            raise NotFoundError(self._entity_cls.entity_name, entity.id) from None
        for attr, value in self._mapper.to_model_values(entity).items():
            setattr(instance, attr, value)
        instance.save()
        return self._mapper.to_entity(instance)

    def delete(self, entity_id: int) -> None:
        self._model.objects.filter(pk=entity_id).delete()

    # -- helpers -----------------------------------------------------------

    def _filtered(self, query: ListQuery) -> models.QuerySet:
        queryset = self._model.objects.all()
        if query.ids:
            queryset = queryset.filter(pk__in=query.ids)
        if query.search and self._search_fields:
            conditions = [models.Q(**{f"{field}__icontains": query.search}) for field in self._search_fields]
            queryset = queryset.filter(reduce(or_, conditions))
        for domain_field, value in query.filters.items():
            attr = self._filter_attr(domain_field)
            if attr is None:
                continue
            lookup = {f"{attr}__isnull": True} if value is None else {attr: getattr(value, "value", value)}
            queryset = queryset.filter(**lookup)
        return queryset

    def _filter_attr(self, domain_field: str) -> str | None:
        if domain_field in self._related_filters:
            return self._related_filters[domain_field]
        if domain_field in self._entity_cls.field_names():
            return self._mapper.model_attr(domain_field)
        return None

    def _apply_ordering(self, queryset: models.QuerySet, ordering: str) -> models.QuerySet:
        descending = ordering.startswith("-")
        domain_field = ordering.lstrip("-")
        if domain_field not in self._entity_cls.field_names():
            descending, domain_field = False, self._default_ordering
        attr = self._mapper.model_attr(domain_field)
        primary = f"-{attr}" if descending else attr
        return queryset.order_by(primary, "pk")  # pk keeps pagination stable
