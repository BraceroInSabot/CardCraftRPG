import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def system(api):
    return api.post("/api/systems/", {"name": "Ironvale"}, format="json").json()


@pytest.fixture
def campaign(api, system):
    return api.post("/api/campaigns/", {"name": "Ashen Crown", "system_id": system["id"]}, format="json").json()


def test_crud_round_trip(api, system):
    created = api.post(
        "/api/items/",
        {"name": "Longsword", "system_id": system["id"], "rarity": "rare", "cost": "15 gp"},
        format="json",
    )
    assert created.status_code == 201
    item_id = created.json()["id"]

    assert api.get(f"/api/items/{item_id}/").json()["rarity"] == "rare"

    patched = api.patch(f"/api/items/{item_id}/", {"weight": "3 lb"}, format="json")
    assert patched.status_code == 200
    assert patched.json()["cost"] == "15 gp"
    assert patched.json()["weight"] == "3 lb"

    replaced = api.put(f"/api/items/{item_id}/", {"name": "Greatsword", "system_id": system["id"]}, format="json")
    assert replaced.status_code == 200
    assert replaced.json()["name"] == "Greatsword"

    assert api.delete(f"/api/items/{item_id}/").status_code == 204
    assert api.get(f"/api/items/{item_id}/").status_code == 404


def test_serializer_and_domain_errors_share_a_format(api, system):
    bad_shape = api.post("/api/items/", {"system_id": system["id"], "rarity": "mythic"}, format="json")
    assert bad_shape.status_code == 400
    assert {"name", "rarity"} <= set(bad_shape.json())

    bad_reference = api.post("/api/items/", {"name": "Sword", "system_id": 999}, format="json")
    assert bad_reference.status_code == 400
    assert bad_reference.json() == {"system_id": ["RPG system #999 does not exist."]}


def test_campaign_from_another_system_is_rejected(api, campaign):
    other = api.post("/api/systems/", {"name": "Neon Drift"}, format="json").json()
    response = api.post(
        "/api/races/", {"name": "Elf", "system_id": other["id"], "campaign_id": campaign["id"]}, format="json"
    )
    assert response.status_code == 400
    assert "campaign_id" in response.json()


def test_list_filters_search_ordering_and_pagination(api, system, campaign):
    for name, rarity, with_campaign in [
        ("Axe", "common", False),
        ("Bow", "rare", True),
        ("Cape of Stars", "rare", False),
        ("Dagger", "rare", True),
    ]:
        api.post(
            "/api/items/",
            {
                "name": name,
                "rarity": rarity,
                "system_id": system["id"],
                "campaign_id": campaign["id"] if with_campaign else None,
            },
            format="json",
        )

    rare = api.get("/api/items/", {"rarity": "rare", "ordering": "-name", "page_size": 2}).json()
    assert rare["count"] == 3
    assert rare["total_pages"] == 2
    assert [r["name"] for r in rare["results"]] == ["Dagger", "Cape of Stars"]

    by_campaign = api.get("/api/items/", {"campaign": campaign["id"]}).json()
    assert [r["name"] for r in by_campaign["results"]] == ["Bow", "Dagger"]

    searched = api.get("/api/items/", {"search": "stars"}).json()
    assert [r["name"] for r in searched["results"]] == ["Cape of Stars"]

    first_two_ids = [r["id"] for r in api.get("/api/items/").json()["results"][:2]]
    by_ids = api.get("/api/items/", {"ids": ",".join(map(str, first_two_ids))}).json()
    assert by_ids["count"] == 2


def test_skills_filter_by_parent_and_by_system(api, system):
    other = api.post("/api/systems/", {"name": "Neon Drift"}, format="json").json()
    mage = api.post("/api/classes/", {"name": "Mage", "system_id": system["id"]}, format="json").json()
    hacker = api.post("/api/classes/", {"name": "Hacker", "system_id": other["id"]}, format="json").json()
    api.post("/api/class-skills/", {"name": "Bolt", "class_id": mage["id"], "kind": "active"}, format="json")
    api.post("/api/class-skills/", {"name": "Overclock", "class_id": hacker["id"]}, format="json")

    in_system = api.get("/api/class-skills/", {"system": system["id"]}).json()
    assert [r["name"] for r in in_system["results"]] == ["Bolt"]

    by_class = api.get("/api/class-skills/", {"character_class": hacker["id"]}).json()
    assert [r["name"] for r in by_class["results"]] == ["Overclock"]


def test_deleting_a_system_cascades(api, system, campaign):
    race = api.post("/api/races/", {"name": "Dwarf", "system_id": system["id"]}, format="json").json()
    api.post("/api/race-skills/", {"name": "Stonecunning", "race_id": race["id"]}, format="json")

    assert api.delete(f"/api/systems/{system['id']}/").status_code == 204
    assert api.get("/api/campaigns/").json()["count"] == 0
    assert api.get("/api/race-skills/").json()["count"] == 0


def test_deleting_a_campaign_keeps_its_content(api, system, campaign):
    item = api.post(
        "/api/items/", {"name": "Relic", "system_id": system["id"], "campaign_id": campaign["id"]}, format="json"
    ).json()
    api.delete(f"/api/campaigns/{campaign['id']}/")
    assert api.get(f"/api/items/{item['id']}/").json()["campaign_id"] is None


def test_meta_exposes_choices(api):
    body = api.get("/api/meta/").json()
    assert {"value": "very_rare", "label": "Very Rare"} in body["rarities"]
    assert [k["value"] for k in body["skill_kinds"]] == ["passive", "active", "reaction"]
