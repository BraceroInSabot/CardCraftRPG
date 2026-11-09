"""Cross-entity integrity rules.

Entities validate their own invariants; rules validate relationships that
need a repository lookup. Use cases receive a list of rules, so new
constraints are added by composition rather than by editing use cases
(Open/Closed principle).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from cardcraft.domain.entities import Campaign, Entity, SystemScopedEntity
from cardcraft.domain.exceptions import NotFoundError, ValidationError
from cardcraft.domain.repositories import Repository

E = TypeVar("E", bound=Entity)


class IntegrityRule(ABC, Generic[E]):
    @abstractmethod
    def check(self, entity: E, previous: E | None) -> None:
        """Raise ``ValidationError`` if ``entity`` breaks the rule.

        ``previous`` is the stored version on updates and ``None`` on creation.
        """


class ReferenceExists(IntegrityRule[Entity]):
    """The referenced entity (e.g. ``system_id``) must exist."""

    def __init__(self, field_name: str, repository: Repository, label: str):
        self._field_name = field_name
        self._repository = repository
        self._label = label

    def check(self, entity: Entity, previous: Entity | None) -> None:
        value = getattr(entity, self._field_name)
        if value is not None and not self._repository.exists(value):
            raise ValidationError.single(self._field_name, f"{self._label} #{value} does not exist.")


class CampaignBelongsToSystem(IntegrityRule[SystemScopedEntity]):
    """Content linked to a campaign must share that campaign's RPG system."""

    def __init__(self, campaigns: Repository[Campaign]):
        self._campaigns = campaigns

    def check(self, entity: SystemScopedEntity, previous: SystemScopedEntity | None) -> None:
        if entity.campaign_id is None:
            return
        try:
            campaign = self._campaigns.get(entity.campaign_id)
        except NotFoundError:
            raise ValidationError.single("campaign_id", f"Campaign #{entity.campaign_id} does not exist.")
        if campaign.system_id != entity.system_id:
            raise ValidationError.single("campaign_id", "The campaign belongs to a different RPG system.")


class ImmutableField(IntegrityRule[Entity]):
    """A field that cannot change after creation (keeps dependants consistent)."""

    def __init__(self, field_name: str):
        self._field_name = field_name

    def check(self, entity: Entity, previous: Entity | None) -> None:
        if previous is None:
            return
        if getattr(entity, self._field_name) != getattr(previous, self._field_name):
            raise ValidationError.single(self._field_name, "This field cannot be changed after creation.")
