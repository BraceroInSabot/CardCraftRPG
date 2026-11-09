"""Composition root.

The only place that knows which concrete implementations back each port.
Swapping the ORM, adding a cache or a new rule only touches this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from cardcraft.application import CampaignBelongsToSystem, CrudUseCases, ImmutableField, ReferenceExists
from cardcraft.domain import (
    Campaign,
    CharacterClass,
    ClassSkill,
    Item,
    Race,
    RaceSkill,
    RpgSystem,
)


@dataclass(frozen=True)
class Container:
    systems: CrudUseCases[RpgSystem]
    campaigns: CrudUseCases[Campaign]
    items: CrudUseCases[Item]
    races: CrudUseCases[Race]
    race_skills: CrudUseCases[RaceSkill]
    classes: CrudUseCases[CharacterClass]
    class_skills: CrudUseCases[ClassSkill]


def build_container() -> Container:
    # Imported lazily: Django models need the app registry to be ready.
    from cardcraft.infrastructure.persistence import models as orm
    from cardcraft.infrastructure.persistence.mappers import EntityMapper
    from cardcraft.infrastructure.persistence.repositories import DjangoRepository

    systems = DjangoRepository(orm.RpgSystemModel, RpgSystem)
    campaigns = DjangoRepository(orm.CampaignModel, Campaign)
    items = DjangoRepository(
        orm.ItemModel, Item, search_fields=("name", "description", "item_type")
    )
    races = DjangoRepository(orm.RaceModel, Race)
    race_skills = DjangoRepository(
        orm.RaceSkillModel, RaceSkill, related_filters={"system_id": "race__system_id"}
    )
    classes = DjangoRepository(orm.CharacterClassModel, CharacterClass)
    class_skills = DjangoRepository(
        orm.ClassSkillModel,
        ClassSkill,
        mapper=EntityMapper(ClassSkill, renames={"class_id": "character_class_id"}),
        related_filters={"system_id": "character_class__system_id"},
    )

    system_exists = ReferenceExists("system_id", systems, "RPG system")
    system_scoped_rules = (system_exists, CampaignBelongsToSystem(campaigns))

    return Container(
        systems=CrudUseCases.build(systems, RpgSystem),
        campaigns=CrudUseCases.build(campaigns, Campaign, (system_exists, ImmutableField("system_id"))),
        items=CrudUseCases.build(items, Item, system_scoped_rules),
        races=CrudUseCases.build(races, Race, system_scoped_rules),
        race_skills=CrudUseCases.build(race_skills, RaceSkill, (ReferenceExists("race_id", races, "Race"),)),
        classes=CrudUseCases.build(classes, CharacterClass, system_scoped_rules),
        class_skills=CrudUseCases.build(
            class_skills, ClassSkill, (ReferenceExists("class_id", classes, "Class"),)
        ),
    )


@lru_cache(maxsize=1)
def get_container() -> Container:
    return build_container()
