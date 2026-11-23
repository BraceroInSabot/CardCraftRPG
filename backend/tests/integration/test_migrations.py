"""Content created before accounts existed is handed to the first Master."""

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

BEFORE = [("cardcraft", "0003_item_damage_and_rarity_labels")]
AFTER = [("cardcraft", "0006_system_owner_required")]


def _migrate(targets):
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    executor.migrate(targets)
    return executor.loader.project_state(targets).apps


@pytest.fixture
def at_0003(transactional_db):
    apps = _migrate(BEFORE)
    yield apps
    _migrate(MigrationExecutor(connection).loader.graph.leaf_nodes())  # leave the schema as found


def test_existing_systems_go_to_the_first_master(at_0003):
    User = get_user_model()  # auth is untouched by rolling cardcraft back
    first = User.objects.create(username="first", password="!")
    User.objects.create(username="second", password="!")
    at_0003.get_model("cardcraft", "RpgSystemModel").objects.create(name="Legacy")

    apps = _migrate(AFTER)
    system = apps.get_model("cardcraft", "RpgSystemModel").objects.get(name="Legacy")
    assert system.owner_id == first.pk


def test_a_master_is_created_when_there_is_content_but_no_user(at_0003):
    at_0003.get_model("cardcraft", "RpgSystemModel").objects.create(name="Legacy")

    apps = _migrate(AFTER)
    system = apps.get_model("cardcraft", "RpgSystemModel").objects.select_related("owner").get(name="Legacy")
    assert system.owner.username == "master"
    assert system.owner.password == "!"  # unusable until `changepassword master`
