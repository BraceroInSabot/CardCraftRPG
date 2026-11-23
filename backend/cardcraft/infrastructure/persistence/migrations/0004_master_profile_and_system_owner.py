import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Masters: a profile table and a (temporarily nullable) owner for RPG systems."""

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("cardcraft", "0003_item_damage_and_rarity_labels"),
    ]

    operations = [
        migrations.CreateModel(
            name="MasterProfileModel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("display_name", models.CharField(blank=True, default="", max_length=120)),
                ("default_background_color", models.CharField(default="#ffffff", max_length=7)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="master_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "master_profile"},
        ),
        migrations.AddField(
            model_name="rpgsystemmodel",
            name="owner",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="rpg_systems",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
