"""Issue #1: Master authentication, content ownership and settings."""

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db


def _login(client, username="gandalf", password=PASSWORD):
    return client.post("/api/auth/login/", {"username": username, "password": password}, format="json")


# --------------------------------------------------------------------------
# Login / logout / protected access
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    ["/api/systems/", "/api/campaigns/", "/api/items/", "/api/races/", "/api/race-skills/",
     "/api/classes/", "/api/class-skills/", "/api/meta/", "/api/account/"],
)
def test_api_requires_a_session(anonymous, path):
    response = anonymous.get(path)
    assert response.status_code == 401
    assert response.has_header("WWW-Authenticate")


def test_health_stays_public(anonymous):
    assert anonymous.get("/api/health/").status_code == 200


def test_login_starts_a_session(anonymous, master):
    response = _login(anonymous)
    assert response.status_code == 200
    assert response.json()["username"] == "gandalf"
    assert anonymous.get("/api/systems/").status_code == 200


@pytest.mark.parametrize("username,password", [("gandalf", "wrong-password"), ("nobody", PASSWORD), ("", "")])
def test_invalid_credentials_get_one_generic_error(anonymous, master, username, password):
    response = _login(anonymous, username, password)
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid username or password."}
    assert anonymous.get("/api/systems/").status_code == 401


def test_inactive_master_cannot_log_in(anonymous, make_master):
    make_master("radagast", is_active=False)
    assert _login(anonymous, "radagast").status_code == 400


def test_login_is_throttled_to_five_attempts_per_minute(anonymous, master):
    for _ in range(5):
        assert _login(anonymous, password="wrong").status_code == 400
    assert _login(anonymous).status_code == 429


def test_login_and_unsafe_requests_need_the_csrf_token(master):
    client = APIClient(enforce_csrf_checks=True)
    assert _login(client).status_code == 403  # no token yet

    assert client.get("/api/auth/csrf/").status_code == 204
    token = client.cookies["csrftoken"].value
    login = client.post(
        "/api/auth/login/", {"username": "gandalf", "password": PASSWORD}, format="json", HTTP_X_CSRFTOKEN=token
    )
    assert login.status_code == 200

    rotated = client.cookies["csrftoken"].value  # login rotates the token
    assert client.post("/api/systems/", {"name": "No token"}, format="json").status_code == 403
    created = client.post("/api/systems/", {"name": "Ironvale"}, format="json", HTTP_X_CSRFTOKEN=rotated)
    assert created.status_code == 201


def test_logout_ends_the_session(anonymous, master):
    _login(anonymous)
    assert anonymous.post("/api/auth/logout/").status_code == 204
    assert anonymous.get("/api/systems/").status_code == 401
    assert anonymous.post("/api/auth/logout/").status_code == 204  # harmless when already out


# --------------------------------------------------------------------------
# Ownership
# --------------------------------------------------------------------------


@pytest.fixture
def other(make_master):
    client = APIClient()
    client.force_login(make_master("saruman"))
    return client


@pytest.fixture
def other_content(other):
    """One of each resource, owned by another Master."""
    system = other.post("/api/systems/", {"name": "Isengard"}, format="json").json()
    sid = system["id"]
    race = other.post("/api/races/", {"name": "Uruk", "system_id": sid}, format="json").json()
    klass = other.post("/api/classes/", {"name": "Wizard", "system_id": sid}, format="json").json()
    return {
        "systems": system,
        "campaigns": other.post("/api/campaigns/", {"name": "Orthanc", "system_id": sid}, format="json").json(),
        "items": other.post("/api/items/", {"name": "Palantir", "system_id": sid}, format="json").json(),
        "races": race,
        "race-skills": other.post("/api/race-skills/", {"name": "Tireless", "race_id": race["id"]}, format="json").json(),
        "classes": klass,
        "class-skills": other.post("/api/class-skills/", {"name": "Voice", "class_id": klass["id"]}, format="json").json(),
    }


RESOURCES = ["systems", "campaigns", "items", "races", "race-skills", "classes", "class-skills"]


@pytest.mark.parametrize("resource", RESOURCES)
def test_another_masters_content_is_invisible(api, other_content, resource):
    target = other_content[resource]
    url = f"/api/{resource}/{target['id']}/"

    assert api.get(f"/api/{resource}/").json()["count"] == 0
    assert api.get(f"/api/{resource}/", {"ids": str(target["id"])}).json()["count"] == 0  # print selection
    assert api.get(url).status_code == 404
    assert api.patch(url, {"name": "Mine now"}, format="json").status_code == 404
    assert api.put(url, {"name": "Mine now"}, format="json").status_code in (400, 404)
    assert api.delete(url).status_code == 404
    assert api.delete(f"{url}image/").status_code == 404


def test_untouched_after_attempted_changes(api, other, other_content):
    item = other_content["items"]
    api.patch(f"/api/items/{item['id']}/", {"name": "Stolen"}, format="json")
    api.delete(f"/api/systems/{other_content['systems']['id']}/")
    assert other.get(f"/api/items/{item['id']}/").json()["name"] == "Palantir"


def test_cannot_attach_content_to_another_masters_parents(api, other_content):
    sid = other_content["systems"]["id"]
    response = api.post("/api/items/", {"name": "Sneaky", "system_id": sid}, format="json")
    assert response.status_code == 400
    assert response.json() == {"system_id": [f"RPG system #{sid} does not exist."]}

    mine = api.post("/api/systems/", {"name": "Shire"}, format="json").json()
    campaign_id = other_content["campaigns"]["id"]
    response = api.post(
        "/api/items/", {"name": "Sneaky", "system_id": mine["id"], "campaign_id": campaign_id}, format="json"
    )
    assert response.status_code == 400
    assert "campaign_id" in response.json()

    assert api.post("/api/race-skills/", {"name": "x", "race_id": other_content["races"]["id"]},
                    format="json").status_code == 400
    assert api.post("/api/class-skills/", {"name": "x", "class_id": other_content["classes"]["id"]},
                    format="json").status_code == 400


def test_filters_only_see_own_content(api, other, other_content):
    mine = api.post("/api/systems/", {"name": "Shire"}, format="json").json()
    api.post("/api/items/", {"name": "Pipe", "system_id": mine["id"], "rarity": "rare"}, format="json")
    other.post("/api/items/", {"name": "Pipe of Isengard", "system_id": other_content["systems"]["id"],
                               "rarity": "rare"}, format="json")

    rare = api.get("/api/items/", {"rarity": "rare", "search": "pipe"}).json()
    assert [row["name"] for row in rare["results"]] == ["Pipe"]
    assert api.get("/api/items/", {"system": other_content["systems"]["id"]}).json()["count"] == 0


def test_owner_is_never_taken_from_the_payload(api, master, other_content):
    created = api.post("/api/systems/", {"name": "Shire", "owner_id": 999}, format="json")
    assert created.status_code == 201
    assert "owner_id" not in created.json()
    from cardcraft.infrastructure.persistence.models import RpgSystemModel

    assert RpgSystemModel.objects.get(pk=created.json()["id"]).owner_id == master.pk


# --------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------


def test_account_shows_the_signed_in_master(api):
    body = api.get("/api/account/").json()
    assert body == {
        "id": body["id"], "username": "gandalf", "display_name": "", "email": "", "default_background_color": "#ffffff",
    }


def test_update_profile(api):
    response = api.patch("/api/account/profile/", {"display_name": "Mithrandir", "email": "Grey@Istari.org"},
                         format="json")
    assert response.status_code == 200
    assert response.json()["display_name"] == "Mithrandir"
    assert response.json()["email"] == "grey@istari.org"

    invalid = api.patch("/api/account/profile/", {"email": "nope"}, format="json")
    assert invalid.status_code == 400
    assert "email" in invalid.json()


def test_update_card_defaults(api):
    response = api.patch("/api/account/card-defaults/", {"default_background_color": "#F6ECD6"}, format="json")
    assert response.status_code == 200
    assert response.json()["default_background_color"] == "#f6ecd6"
    assert api.patch("/api/account/card-defaults/", {"default_background_color": "beige"},
                     format="json").status_code == 400


def test_password_change_requires_the_current_password(api, anonymous):
    wrong = api.post("/api/account/password/", {"current_password": "nope", "new_password": "Balrog-Slayer-77"},
                     format="json")
    assert wrong.status_code == 400
    assert "current_password" in wrong.json()

    weak = api.post("/api/account/password/", {"current_password": PASSWORD, "new_password": "123"}, format="json")
    assert weak.status_code == 400
    assert "new_password" in weak.json()

    ok = api.post("/api/account/password/", {"current_password": PASSWORD, "new_password": "Balrog-Slayer-77"},
                  format="json")
    assert ok.status_code == 204
    assert api.get("/api/account/").status_code == 200  # this session survives

    assert _login(anonymous, password=PASSWORD).status_code == 400
    assert _login(anonymous, password="Balrog-Slayer-77").status_code == 200


def test_password_change_signs_out_other_sessions(master, anonymous):
    _login(anonymous)
    second = APIClient()
    _login(second)
    second.post("/api/account/password/", {"current_password": PASSWORD, "new_password": "Balrog-Slayer-77"},
                format="json")
    assert anonymous.get("/api/account/").status_code == 401
    assert second.get("/api/account/").status_code == 200


# --------------------------------------------------------------------------
# Management commands
# --------------------------------------------------------------------------


def test_create_master_command_is_idempotent(anonymous):
    call_command("create_master", username="elrond", password="Rivendell-Council-3")
    call_command("create_master", username="elrond", password="Something-Else-9")
    assert _login(anonymous, "elrond", "Rivendell-Council-3").status_code == 200


def test_seed_demo_goes_to_the_chosen_master(api, other, make_master):
    call_command("seed_demo", owner="gandalf")
    assert api.get("/api/systems/").json()["count"] == 1
    assert api.get("/api/class-skills/").json()["count"] > 0
    assert other.get("/api/systems/").json()["count"] == 0
