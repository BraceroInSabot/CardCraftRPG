"""Create the default development Master (bracero / bracero123).

The password is weak on purpose (easy local logins), so the strength checks
are skipped and the command refuses to run with DEBUG off unless --force is
given. Change the password from the settings page outside local development.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

DEFAULT_USERNAME = "bracero"
DEFAULT_PASSWORD = "bracero123"


class Command(BaseCommand):
    help = "Create the default development Master (bracero / bracero123) if it does not exist."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Run even with DEBUG off.")

    def handle(self, *args, force, **options):
        if not settings.DEBUG and not force:
            raise CommandError("Refusing to create a Master with a default password while DEBUG is off (use --force).")
        User = get_user_model()
        if User.objects.filter(username=DEFAULT_USERNAME).exists():
            self.stdout.write(self.style.WARNING(f"Master '{DEFAULT_USERNAME}' already exists; nothing to do."))
            return
        User.objects.create_user(username=DEFAULT_USERNAME, password=DEFAULT_PASSWORD)
        self.stdout.write(self.style.SUCCESS(f"Master '{DEFAULT_USERNAME}' created (password: {DEFAULT_PASSWORD})."))
