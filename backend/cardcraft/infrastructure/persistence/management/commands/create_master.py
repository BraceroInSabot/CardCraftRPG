"""Create a Master account (there is no self sign-up)."""

import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Create a Master account. Without arguments it reads MASTER_USERNAME, MASTER_PASSWORD "
        "and MASTER_EMAIL, and does nothing if that account already exists (safe on every start)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--username", default=os.environ.get("MASTER_USERNAME", ""))
        parser.add_argument("--password", default=os.environ.get("MASTER_PASSWORD", ""))
        parser.add_argument("--email", default=os.environ.get("MASTER_EMAIL", ""))

    def handle(self, *args, username, password, email, **options):
        if not username or not password:
            raise CommandError("A username and a password are required (or MASTER_USERNAME / MASTER_PASSWORD).")
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"Master '{username}' already exists; nothing to do."))
            return
        user = User(username=username, email=email)
        try:
            validate_password(password, user=user)
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages)) from None
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Master '{username}' created."))
