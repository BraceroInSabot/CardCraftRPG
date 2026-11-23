import pytest

from cardcraft.application import AccountUseCases
from cardcraft.domain import Master, NotFoundError, RpgSystem, ValidationError

from .fakes import FakePasswordService, InMemoryMasterRepository


@pytest.fixture
def passwords():
    return FakePasswordService({1: "old-secret"})


@pytest.fixture
def accounts(passwords):
    masters = InMemoryMasterRepository(Master(id=1, username="gandalf", email="g@shire.me"))
    return AccountUseCases.build(masters, passwords)


def test_master_normalizes_and_validates():
    master = Master(username="  gandalf ", email="G@Shire.ME", default_background_color="#F6ECD6")
    assert (master.username, master.email, master.default_background_color) == ("gandalf", "g@shire.me", "#f6ecd6")
    assert master.shown_name == "gandalf"

    with pytest.raises(ValidationError) as exc:
        Master(username="", email="not-an-email", default_background_color="red")
    assert set(exc.value.errors) == {"username", "email", "default_background_color"}


def test_rpg_system_owner_is_not_settable_from_input():
    assert "owner_id" in RpgSystem.managed_fields


def test_update_profile_only_touches_profile_fields(accounts):
    updated = accounts.update_profile.execute(
        1, {"display_name": "Mithrandir", "email": "grey@istari.org", "username": "saruman",
            "default_background_color": "#000000"}
    )
    assert (updated.username, updated.display_name, updated.email) == ("gandalf", "Mithrandir", "grey@istari.org")
    assert updated.default_background_color == "#ffffff"


def test_update_profile_reports_invalid_values(accounts):
    with pytest.raises(ValidationError) as exc:
        accounts.update_profile.execute(1, {"email": "nope"})
    assert "email" in exc.value.errors
    assert accounts.get.execute(1).email == "g@shire.me"


def test_update_card_defaults(accounts):
    updated = accounts.update_card_defaults.execute(1, {"default_background_color": "#E8F1F2", "email": "x@y.z"})
    assert updated.default_background_color == "#e8f1f2"
    assert updated.email == "g@shire.me"


def test_change_password_requires_the_current_password(accounts, passwords):
    with pytest.raises(ValidationError) as exc:
        accounts.change_password.execute(1, "wrong", "brand-new-secret")
    assert set(exc.value.errors) == {"current_password"}
    assert passwords.passwords[1] == "old-secret"


def test_change_password_validates_the_new_one(accounts, passwords):
    with pytest.raises(ValidationError) as exc:
        accounts.change_password.execute(1, "old-secret", "short")
    assert set(exc.value.errors) == {"new_password"}
    with pytest.raises(ValidationError):
        accounts.change_password.execute(1, "old-secret", "old-secret")

    accounts.change_password.execute(1, "old-secret", "brand-new-secret")
    assert passwords.passwords[1] == "brand-new-secret"


def test_unknown_master_is_not_found(accounts):
    with pytest.raises(NotFoundError):
        accounts.get.execute(99)
    with pytest.raises(NotFoundError):
        accounts.change_password.execute(99, "a", "b")
