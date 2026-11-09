"""Domain entities.

Plain dataclasses with their own invariants. They know nothing about Django,
the database or HTTP, so they can be tested and reused in isolation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, fields
from enum import StrEnum
from typing import Any, ClassVar

from .exceptions import ValidationError

NAME_MAX_LENGTH = 120
SHORT_TEXT_MAX_LENGTH = 60
DESCRIPTION_MAX_LENGTH = 1200
DEFAULT_BACKGROUND_COLOR = "#ffffff"
IMAGE_KEY_MAX_LENGTH = 255

_HEX_COLOR = re.compile(r"^#[0-9a-f]{6}$")


class Rarity(StrEnum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    VERY_RARE = "very_rare"
    LEGENDARY = "legendary"
    ARTIFACT = "artifact"

    @property
    def label(self) -> str:
        return _RARITY_LABELS[self]


_RARITY_LABELS = {
    Rarity.COMMON: "Comum",
    Rarity.UNCOMMON: "Incomum",
    Rarity.RARE: "Raro",
    Rarity.VERY_RARE: "Muito raro",
    Rarity.LEGENDARY: "Lendário",
    Rarity.ARTIFACT: "Artefato",
}

# Item types (compared case-insensitively) whose cards show a damage value.
WEAPON_ITEM_TYPES = frozenset({"arma"})


class SkillKind(StrEnum):
    PASSIVE = "passive"
    ACTIVE = "active"
    REACTION = "reaction"


class _ErrorCollector:
    """Accumulates field errors so every invalid field is reported at once."""

    def __init__(self) -> None:
        self._errors: dict[str, list[str]] = {}

    def add(self, field_name: str, message: str) -> None:
        self._errors.setdefault(field_name, []).append(message)

    def require_text(self, field_name: str, value: str, max_length: int) -> None:
        if not value:
            self.add(field_name, "This field is required.")
        self.limit_text(field_name, value, max_length)

    def limit_text(self, field_name: str, value: str, max_length: int) -> None:
        if len(value) > max_length:
            self.add(field_name, f"Must have at most {max_length} characters.")

    def require_reference(self, field_name: str, value: int | None) -> None:
        if value is None:
            self.add(field_name, "This field is required.")
        else:
            self.optional_reference(field_name, value)

    def optional_reference(self, field_name: str, value: int | None) -> None:
        if value is not None and (not isinstance(value, int) or value < 1):
            self.add(field_name, "Must be a valid identifier.")

    def raise_if_any(self) -> None:
        if self._errors:
            raise ValidationError(self._errors)


@dataclass(kw_only=True)
class Entity:
    """Base entity: identity plus self-validation on construction."""

    entity_name: ClassVar[str] = "Entity"
    # Fields only changed by dedicated use cases, never by plain create/update input.
    managed_fields: ClassVar[frozenset[str]] = frozenset({"id"})

    id: int | None = None

    def __post_init__(self) -> None:
        self._normalize()
        errors = _ErrorCollector()
        self._collect_errors(errors)
        errors.raise_if_any()

    def _normalize(self) -> None:
        """Hook for subclasses to clean values before validation."""

    def _collect_errors(self, errors: _ErrorCollector) -> None:
        """Hook for subclasses to register invariant violations."""

    @classmethod
    def field_names(cls) -> set[str]:
        return {f.name for f in fields(cls)}

    def to_dict(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}


@dataclass(kw_only=True)
class NamedEntity(Entity):
    """Anything that can be printed as a card: a name, a text and its look."""

    managed_fields: ClassVar[frozenset[str]] = frozenset({"id", "image"})

    name: str
    description: str = ""
    background_color: str = DEFAULT_BACKGROUND_COLOR
    image: str = ""  # storage key of the card illustration; "" when there is none

    def _normalize(self) -> None:
        super()._normalize()
        self.name = (self.name or "").strip()
        self.description = (self.description or "").strip()
        self.background_color = (self.background_color or DEFAULT_BACKGROUND_COLOR).strip().lower()
        self.image = self.image or ""

    def _collect_errors(self, errors: _ErrorCollector) -> None:
        super()._collect_errors(errors)
        errors.require_text("name", self.name, NAME_MAX_LENGTH)
        errors.limit_text("description", self.description, DESCRIPTION_MAX_LENGTH)
        errors.limit_text("image", self.image, IMAGE_KEY_MAX_LENGTH)
        if not _HEX_COLOR.match(self.background_color):
            errors.add("background_color", "Use a hex color such as #ffffff.")

    @property
    def has_image(self) -> bool:
        return bool(self.image)


@dataclass(kw_only=True)
class RpgSystem(NamedEntity):
    entity_name: ClassVar[str] = "RPG system"


@dataclass(kw_only=True)
class Campaign(NamedEntity):
    entity_name: ClassVar[str] = "Campaign"

    system_id: int

    def _collect_errors(self, errors: _ErrorCollector) -> None:
        super()._collect_errors(errors)
        errors.require_reference("system_id", self.system_id)


@dataclass(kw_only=True)
class SystemScopedEntity(NamedEntity):
    """Content that belongs to a system and, optionally, to one campaign of it."""

    system_id: int
    campaign_id: int | None = None

    def _collect_errors(self, errors: _ErrorCollector) -> None:
        super()._collect_errors(errors)
        errors.require_reference("system_id", self.system_id)
        errors.optional_reference("campaign_id", self.campaign_id)


@dataclass(kw_only=True)
class Item(SystemScopedEntity):
    entity_name: ClassVar[str] = "Item"

    item_type: str = ""
    rarity: Rarity = Rarity.COMMON
    cost: str = ""
    weight: str = ""
    damage: str = ""  # only kept for weapons, e.g. "1d8 cortante"

    @property
    def is_weapon(self) -> bool:
        return self.item_type.casefold() in WEAPON_ITEM_TYPES

    def _normalize(self) -> None:
        super()._normalize()
        self.item_type = (self.item_type or "").strip()
        self.cost = (self.cost or "").strip()
        self.weight = (self.weight or "").strip()
        self.rarity = _coerce_enum(Rarity, self.rarity)
        # Damage belongs to weapons only: changing the type away from "Arma" drops it.
        self.damage = (self.damage or "").strip() if self.is_weapon else ""

    def _collect_errors(self, errors: _ErrorCollector) -> None:
        super()._collect_errors(errors)
        errors.limit_text("item_type", self.item_type, SHORT_TEXT_MAX_LENGTH)
        errors.limit_text("cost", self.cost, SHORT_TEXT_MAX_LENGTH)
        errors.limit_text("weight", self.weight, SHORT_TEXT_MAX_LENGTH)
        errors.limit_text("damage", self.damage, SHORT_TEXT_MAX_LENGTH)
        if not isinstance(self.rarity, Rarity):
            errors.add("rarity", f"Must be one of: {', '.join(Rarity)}.")


@dataclass(kw_only=True)
class Race(SystemScopedEntity):
    entity_name: ClassVar[str] = "Race"


@dataclass(kw_only=True)
class CharacterClass(SystemScopedEntity):
    entity_name: ClassVar[str] = "Class"


@dataclass(kw_only=True)
class Skill(NamedEntity):
    """Shared shape of race and class skills."""

    kind: SkillKind = SkillKind.PASSIVE
    level: int | None = None
    cost: str = ""

    def _normalize(self) -> None:
        super()._normalize()
        self.cost = (self.cost or "").strip()
        self.kind = _coerce_enum(SkillKind, self.kind)

    def _collect_errors(self, errors: _ErrorCollector) -> None:
        super()._collect_errors(errors)
        errors.limit_text("cost", self.cost, SHORT_TEXT_MAX_LENGTH)
        if not isinstance(self.kind, SkillKind):
            errors.add("kind", f"Must be one of: {', '.join(SkillKind)}.")
        if self.level is not None and (not isinstance(self.level, int) or not 0 <= self.level <= 100):
            errors.add("level", "Must be between 0 and 100.")


@dataclass(kw_only=True)
class RaceSkill(Skill):
    entity_name: ClassVar[str] = "Race skill"

    race_id: int

    def _collect_errors(self, errors: _ErrorCollector) -> None:
        super()._collect_errors(errors)
        errors.require_reference("race_id", self.race_id)


@dataclass(kw_only=True)
class ClassSkill(Skill):
    entity_name: ClassVar[str] = "Class skill"

    class_id: int

    def _collect_errors(self, errors: _ErrorCollector) -> None:
        super()._collect_errors(errors)
        errors.require_reference("class_id", self.class_id)


def _coerce_enum(enum_cls: type[StrEnum], value: Any) -> Any:
    """Turn raw strings into enum members; leave invalid values for validation."""
    if isinstance(value, enum_cls):
        return value
    try:
        return enum_cls(value)
    except ValueError:
        return value
