import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

PASSWORD = "Dragon-Hoard-42"


@pytest.fixture(autouse=True)
def _reset_throttles():
    # Login throttling counts attempts in the cache; tests must not leak them into each other.
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def make_master(db):
    def make(username: str = "gandalf", password: str = PASSWORD, **extra):
        return get_user_model().objects.create_user(username=username, password=password, **extra)

    return make


@pytest.fixture
def master(make_master):
    return make_master()


@pytest.fixture
def api(master):
    """A client signed in as ``master``."""
    client = APIClient()
    client.force_login(master)
    return client


@pytest.fixture
def anonymous():
    return APIClient()
