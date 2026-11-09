import pytest

from cardcraft.application import CampaignBelongsToSystem, CrudUseCases, ImmutableField, ReferenceExists
from cardcraft.domain import Campaign, Item, ListQuery, NotFoundError, RpgSystem, ValidationError

from .fakes import InMemoryRepository


@pytest.fixture
def repos():
    return {
        "systems": InMemoryRepository(RpgSystem),
        "campaigns": InMemoryRepository(Campaign),
        "items": InMemoryRepository(Item),
    }


@pytest.fixture
def use_cases(repos):
    system_exists = ReferenceExists("system_id", repos["systems"], "RPG system")
    return {
        "systems": CrudUseCases.build(repos["systems"], RpgSystem),
        "campaigns": CrudUseCases.build(
            repos["campaigns"], Campaign, (system_exists, ImmutableField("system_id"))
        ),
        "items": CrudUseCases.build(
            repos["items"], Item, (system_exists, CampaignBelongsToSystem(repos["campaigns"]))
        ),
    }


def test_create_assigns_identity_and_ignores_client_id(use_cases):
    system = use_cases["systems"].create.execute({"name": "Ironvale", "id": 999})
    assert system.id == 1


def test_create_reports_missing_required_fields(use_cases):
    with pytest.raises(ValidationError) as exc:
        use_cases["campaigns"].create.execute({"description": "no name"})
    assert set(exc.value.errors) == {"name", "system_id"}


def test_create_rejects_unknown_reference(use_cases):
    with pytest.raises(ValidationError) as exc:
        use_cases["items"].create.execute({"name": "Sword", "system_id": 42})
    assert exc.value.errors == {"system_id": ["RPG system #42 does not exist."]}


def test_item_campaign_must_belong_to_same_system(use_cases):
    first = use_cases["systems"].create.execute({"name": "A"})
    second = use_cases["systems"].create.execute({"name": "B"})
    campaign = use_cases["campaigns"].create.execute({"name": "Saga", "system_id": first.id})

    with pytest.raises(ValidationError) as exc:
        use_cases["items"].create.execute({"name": "Sword", "system_id": second.id, "campaign_id": campaign.id})
    assert "campaign_id" in exc.value.errors

    item = use_cases["items"].create.execute({"name": "Sword", "system_id": first.id, "campaign_id": campaign.id})
    assert item.campaign_id == campaign.id


def test_update_merges_partial_changes(use_cases):
    system = use_cases["systems"].create.execute({"name": "Old", "description": "keep me"})
    updated = use_cases["systems"].update.execute(system.id, {"name": "New"})
    assert (updated.name, updated.description) == ("New", "keep me")


def test_campaign_system_cannot_change(use_cases):
    first = use_cases["systems"].create.execute({"name": "A"})
    second = use_cases["systems"].create.execute({"name": "B"})
    campaign = use_cases["campaigns"].create.execute({"name": "Saga", "system_id": first.id})
    with pytest.raises(ValidationError) as exc:
        use_cases["campaigns"].update.execute(campaign.id, {"system_id": second.id})
    assert "system_id" in exc.value.errors


def test_update_and_delete_unknown_entity_raise_not_found(use_cases):
    with pytest.raises(NotFoundError):
        use_cases["systems"].update.execute(7, {"name": "x"})
    with pytest.raises(NotFoundError):
        use_cases["systems"].delete.execute(7)


def test_list_filters_and_paginates(use_cases):
    system = use_cases["systems"].create.execute({"name": "A"})
    for name, rarity in [("Axe", "common"), ("Bow", "rare"), ("Cape", "rare")]:
        use_cases["items"].create.execute({"name": name, "system_id": system.id, "rarity": rarity})

    page = use_cases["items"].list.execute(ListQuery(filters={"rarity": "rare"}, page_size=1))
    assert page.total == 2
    assert [item.name for item in page.items] == ["Bow"]
