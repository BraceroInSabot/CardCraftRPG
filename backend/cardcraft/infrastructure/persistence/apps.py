from django.apps import AppConfig


class PersistenceConfig(AppConfig):
    name = "cardcraft.infrastructure.persistence"
    label = "cardcraft"
    verbose_name = "Card Craft RPG"
    default_auto_field = "django.db.models.BigAutoField"
