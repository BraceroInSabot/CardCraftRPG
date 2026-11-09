import pytest

from cardcraft.domain import ClassSkill, Item, Rarity, RpgSystem, SkillKind, ValidationError
from cardcraft.domain.entities import DESCRIPTION_MAX_LENGTH, NAME_MAX_LENGTH
from cardcraft.domain.queries import MAX_PAGE_SIZE, ListQuery, Page


def test_named_entity_strips_whitespace():
    system = RpgSystem(name="  Ironvale  ", description="  gritty  ")
    assert system.name == "Ironvale"
    assert system.description == "gritty"


@pytest.mark.parametrize("name", ["", "   ", "x" * (NAME_MAX_LENGTH + 1)])
def test_invalid_names_are_rejected(name):
    with pytest.raises(ValidationError) as exc:
        RpgSystem(name=name)
    assert "name" in exc.value.errors


def test_description_has_a_length_limit():
    with pytest.raises(ValidationError) as exc:
        RpgSystem(name="ok", description="x" * (DESCRIPTION_MAX_LENGTH + 1))
    assert "description" in exc.value.errors


def test_item_coerces_rarity_strings_to_enum():
    item = Item(name="Sword", system_id=1, rarity="very_rare")
    assert item.rarity is Rarity.VERY_RARE


def test_item_reports_every_invalid_field_at_once():
    with pytest.raises(ValidationError) as exc:
        Item(name="", system_id=0, rarity="mythic")
    assert set(exc.value.errors) == {"name", "system_id", "rarity"}


def test_skill_level_bounds():
    with pytest.raises(ValidationError) as exc:
        ClassSkill(name="Bolt", class_id=1, level=101)
    assert "level" in exc.value.errors
    assert ClassSkill(name="Bolt", class_id=1, kind="active").kind is SkillKind.ACTIVE


def test_list_query_clamps_pagination():
    query = ListQuery(page=0, page_size=MAX_PAGE_SIZE + 10)
    assert query.page == 1
    assert query.page_size == MAX_PAGE_SIZE


def test_page_total_pages_rounds_up():
    assert Page(items=[], total=41, page=1, page_size=20).total_pages == 3
    assert Page(items=[], total=0, page=1, page_size=20).total_pages == 1
