"""Content created before accounts existed goes to the first Master.

The first Master is the oldest active user. When there is content but no
user yet, a ``master`` account is created with an unusable password; set
one with ``python manage.py changepassword master`` before signing in.
"""

from django.conf import settings
from django.db import migrations

FALLBACK_USERNAME = "master"


def assign_owner(apps, schema_editor):
    RpgSystem = apps.get_model("cardcraft", "RpgSystemModel")
    orphans = RpgSystem.objects.filter(owner__isnull=True)
    if not orphans.exists():
        return

    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(app_label, model_name)
    first_master = User.objects.filter(is_active=True).order_by("pk").first()
    if first_master is None:
        # Historical models have no create_user(); "!" marks the password as unusable.
        first_master = User.objects.create(username=FALLBACK_USERNAME, password="!", is_active=True)
    orphans.update(owner=first_master)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("cardcraft", "0004_master_profile_and_system_owner"),
    ]

    operations = [migrations.RunPython(assign_owner, migrations.RunPython.noop)]
