"""DRF serializers.

Plain ``Serializer`` classes (not ``ModelSerializer``): they validate the
shape of HTTP payloads and render domain entities. Business invariants stay
in the domain layer.
"""

from __future__ import annotations

from rest_framework import serializers

from cardcraft.domain.entities import (
    DESCRIPTION_MAX_LENGTH,
    NAME_MAX_LENGTH,
    SHORT_TEXT_MAX_LENGTH,
    Rarity,
    SkillKind,
)
from cardcraft.domain.queries import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, ListQuery


def _enum_choices(enum_cls) -> list[str]:
    return [member.value for member in enum_cls]


def _short_text() -> serializers.CharField:
    return serializers.CharField(max_length=SHORT_TEXT_MAX_LENGTH, required=False, allow_blank=True)


# --------------------------------------------------------------------------
# Entity payloads
# --------------------------------------------------------------------------


class NamedEntitySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=NAME_MAX_LENGTH)
    description = serializers.CharField(max_length=DESCRIPTION_MAX_LENGTH, required=False, allow_blank=True)


class RpgSystemSerializer(NamedEntitySerializer):
    pass


class CampaignSerializer(NamedEntitySerializer):
    system_id = serializers.IntegerField(min_value=1)


class SystemScopedSerializer(NamedEntitySerializer):
    system_id = serializers.IntegerField(min_value=1)
    campaign_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)


class ItemSerializer(SystemScopedSerializer):
    item_type = _short_text()
    rarity = serializers.ChoiceField(choices=_enum_choices(Rarity), required=False)
    cost = _short_text()
    weight = _short_text()


class RaceSerializer(SystemScopedSerializer):
    pass


class CharacterClassSerializer(SystemScopedSerializer):
    pass


class SkillSerializer(NamedEntitySerializer):
    kind = serializers.ChoiceField(choices=_enum_choices(SkillKind), required=False)
    level = serializers.IntegerField(min_value=0, max_value=100, required=False, allow_null=True)
    cost = _short_text()


class RaceSkillSerializer(SkillSerializer):
    race_id = serializers.IntegerField(min_value=1)


class ClassSkillSerializer(SkillSerializer):
    class_id = serializers.IntegerField(min_value=1)


# --------------------------------------------------------------------------
# List query parameters
# --------------------------------------------------------------------------


class IdListField(serializers.Field):
    """Comma separated ids: ``?ids=1,2,3``."""

    default_error_messages = {"invalid": "Use a comma separated list of positive integers."}

    def to_internal_value(self, data):
        try:
            ids = tuple(int(part) for part in str(data).split(",") if part.strip())
        except ValueError:
            self.fail("invalid")
        if any(value < 1 for value in ids):
            self.fail("invalid")
        return ids


class ListParamsSerializer(serializers.Serializer):
    """Common list parameters. Subclasses declare resource-specific filters.

    Filter fields use ``source`` to name the *domain* field they filter on,
    e.g. ``system = IntegerField(source="system_id")``.
    """

    COMMON_FIELDS = ("search", "ordering", "page", "page_size", "ids")

    search = serializers.CharField(required=False, allow_blank=True, max_length=100)
    ordering = serializers.CharField(required=False, max_length=40)
    page = serializers.IntegerField(required=False, min_value=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=MAX_PAGE_SIZE)
    ids = IdListField(required=False)

    def to_query(self) -> ListQuery:
        data = dict(self.validated_data)
        common = {key: data.pop(key) for key in self.COMMON_FIELDS if key in data}
        return ListQuery(
            search=common.get("search", "").strip(),
            ordering=common.get("ordering", "name"),
            page=common.get("page", 1),
            page_size=common.get("page_size", DEFAULT_PAGE_SIZE),
            ids=common.get("ids", ()),
            filters=data,
        )


def _id_filter(source: str) -> serializers.IntegerField:
    return serializers.IntegerField(required=False, min_value=1, source=source)


class CampaignListParams(ListParamsSerializer):
    system = _id_filter("system_id")


class SystemScopedListParams(ListParamsSerializer):
    system = _id_filter("system_id")
    campaign = _id_filter("campaign_id")


class ItemListParams(SystemScopedListParams):
    rarity = serializers.ChoiceField(choices=_enum_choices(Rarity), required=False)
    item_type = serializers.CharField(required=False, max_length=SHORT_TEXT_MAX_LENGTH)


class SkillListParams(ListParamsSerializer):
    system = _id_filter("system_id")
    kind = serializers.ChoiceField(choices=_enum_choices(SkillKind), required=False)
    level = serializers.IntegerField(required=False, min_value=0, max_value=100)


class RaceSkillListParams(SkillListParams):
    race = _id_filter("race_id")


class ClassSkillListParams(SkillListParams):
    character_class = _id_filter("class_id")
