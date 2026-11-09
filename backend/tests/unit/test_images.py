import pytest

from cardcraft.application import CardUseCases, ImageUpload
from cardcraft.domain import RpgSystem, ValidationError

from .fakes import FakeImageInspector, FakeImageStorage, InMemoryRepository


@pytest.fixture
def storage():
    return FakeImageStorage()


@pytest.fixture
def systems(storage):
    repository = InMemoryRepository(RpgSystem)
    use_cases = CardUseCases.build_for_cards(repository, RpgSystem, FakeImageInspector(), storage)
    return use_cases


def test_background_color_defaults_to_white_and_is_normalised():
    assert RpgSystem(name="A").background_color == "#ffffff"
    assert RpgSystem(name="A", background_color=" #F4E3C1 ").background_color == "#f4e3c1"


@pytest.mark.parametrize("color", ["white", "#fff", "#12345g", "123456"])
def test_invalid_background_colors_are_rejected(color):
    with pytest.raises(ValidationError) as exc:
        RpgSystem(name="A", background_color=color)
    assert "background_color" in exc.value.errors


def test_create_and_update_cannot_set_the_image_directly(systems):
    system = systems.create.execute({"name": "A", "image": "../../etc/passwd"})
    assert system.image == ""
    updated = systems.update.execute(system.id, {"image": "hack.png", "background_color": "#000000"})
    assert updated.image == ""
    assert updated.background_color == "#000000"


def test_set_image_stores_file_and_replaces_previous_one(systems, storage):
    system = systems.create.execute({"name": "A"})

    first = systems.set_image.execute(system.id, ImageUpload(b"PNG-1"))
    assert first.image in storage.files

    second = systems.set_image.execute(system.id, ImageUpload(b"PNG-2"))
    assert list(storage.files) == [second.image]
    assert systems.get.execute(system.id).image == second.image


@pytest.mark.parametrize(
    "content, message",
    [
        (b"", "The file is empty."),
        (b"%PDF-1.7", "Upload a PNG, JPEG, WebP or GIF image."),
        (b"PNG" + b"x" * (5 * 1024 * 1024), "Images must be at most 5 MB."),
    ],
)
def test_invalid_uploads_are_rejected_without_storing_anything(systems, storage, content, message):
    system = systems.create.execute({"name": "A"})
    with pytest.raises(ValidationError) as exc:
        systems.set_image.execute(system.id, ImageUpload(content))
    assert exc.value.errors == {"image": [message]}
    assert storage.files == {}


def test_remove_image_and_delete_entity_clean_up_files(systems, storage):
    system = systems.create.execute({"name": "A"})
    systems.set_image.execute(system.id, ImageUpload(b"PNG"))
    assert systems.remove_image.execute(system.id).image == ""
    assert storage.files == {}

    systems.set_image.execute(system.id, ImageUpload(b"PNG"))
    systems.delete.execute(system.id)
    assert storage.files == {}
