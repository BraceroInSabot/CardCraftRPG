"""Django ORM models: the persistence representation of the domain entities.

Nothing outside ``cardcraft.infrastructure`` imports these models; the rest
of the system talks to repositories that return domain entities.
"""

from django.db import models

from cardcraft.domain.entities import (
    DEFAULT_BACKGROUND_COLOR,
    DESCRIPTION_MAX_LENGTH,
    IMAGE_KEY_MAX_LENGTH,
    NAME_MAX_LENGTH,
    SHORT_TEXT_MAX_LENGTH,
    Rarity,
    SkillKind,
)


def _choices(enum_cls) -> list[tuple[str, str]]:
    return [(member.value, getattr(member, "label", member.value.replace("_", " ").title())) for member in enum_cls]


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class NamedModel(TimestampedModel):
    name = models.CharField(max_length=NAME_MAX_LENGTH, db_index=True)
    description = models.TextField(max_length=DESCRIPTION_MAX_LENGTH, blank=True, default="")
    background_color = models.CharField(max_length=7, default=DEFAULT_BACKGROUND_COLOR)
    image = models.CharField(max_length=IMAGE_KEY_MAX_LENGTH, blank=True, default="")

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.name


class RpgSystemModel(NamedModel):
    class Meta:
        db_table = "rpg_system"


class CampaignModel(NamedModel):
    system = models.ForeignKey(RpgSystemModel, on_delete=models.CASCADE, related_name="campaigns")

    class Meta:
        db_table = "campaign"


class SystemScopedModel(NamedModel):
    system = models.ForeignKey(RpgSystemModel, on_delete=models.CASCADE, related_name="+")
    campaign = models.ForeignKey(
        CampaignModel, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    class Meta:
        abstract = True


class ItemModel(SystemScopedModel):
    item_type = models.CharField(max_length=SHORT_TEXT_MAX_LENGTH, blank=True, default="", db_index=True)
    rarity = models.CharField(max_length=20, choices=_choices(Rarity), default=Rarity.COMMON.value)
    cost = models.CharField(max_length=SHORT_TEXT_MAX_LENGTH, blank=True, default="")
    weight = models.CharField(max_length=SHORT_TEXT_MAX_LENGTH, blank=True, default="")
    damage = models.CharField(max_length=SHORT_TEXT_MAX_LENGTH, blank=True, default="")

    class Meta:
        db_table = "item"


class RaceModel(SystemScopedModel):
    class Meta:
        db_table = "race"


class CharacterClassModel(SystemScopedModel):
    class Meta:
        db_table = "character_class"


class SkillModel(NamedModel):
    kind = models.CharField(max_length=20, choices=_choices(SkillKind), default=SkillKind.PASSIVE.value)
    level = models.PositiveSmallIntegerField(null=True, blank=True)
    cost = models.CharField(max_length=SHORT_TEXT_MAX_LENGTH, blank=True, default="")

    class Meta:
        abstract = True


class RaceSkillModel(SkillModel):
    race = models.ForeignKey(RaceModel, on_delete=models.CASCADE, related_name="skills")

    class Meta:
        db_table = "race_skill"


class ClassSkillModel(SkillModel):
    character_class = models.ForeignKey(CharacterClassModel, on_delete=models.CASCADE, related_name="skills")

    class Meta:
        db_table = "class_skill"
