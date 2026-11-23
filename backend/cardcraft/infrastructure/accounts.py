"""Django ``auth`` adapters for the account ports.

A Master is a Django ``User`` plus a ``MasterProfileModel`` row. The profile
is created on first access, so users made with ``createsuperuser`` work too.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from cardcraft.application.ports import PasswordService
from cardcraft.domain.accounts import Master, MasterRepository
from cardcraft.domain.exceptions import NotFoundError, ValidationError

from .persistence.models import MasterProfileModel


def _user(master_id: int):
    User = get_user_model()
    try:
        return User.objects.get(pk=master_id, is_active=True)
    except User.DoesNotExist:
        raise NotFoundError(Master.entity_name, master_id) from None


def _profile(user) -> MasterProfileModel:
    profile, _ = MasterProfileModel.objects.get_or_create(user=user)
    return profile


class DjangoMasterRepository(MasterRepository):
    def get(self, master_id: int) -> Master:
        user = _user(master_id)
        return self._to_entity(user, _profile(user))

    def update(self, master: Master) -> Master:
        user = _user(master.id)
        profile = _profile(user)
        user.email = master.email
        user.save(update_fields=["email"])
        profile.display_name = master.display_name
        profile.default_background_color = master.default_background_color
        profile.save()
        return self._to_entity(user, profile)

    @staticmethod
    def _to_entity(user, profile: MasterProfileModel) -> Master:
        return Master(
            id=user.pk,
            username=user.get_username(),
            email=user.email or "",
            display_name=profile.display_name,
            default_background_color=profile.default_background_color,
        )


class DjangoPasswordService(PasswordService):
    """Uses Django's hashers and ``AUTH_PASSWORD_VALIDATORS``."""

    def verify(self, master_id: int, raw_password: str) -> bool:
        return _user(master_id).check_password(raw_password)

    def validate(self, master_id: int, raw_password: str) -> None:
        try:
            validate_password(raw_password, user=_user(master_id))
        except DjangoValidationError as exc:
            raise ValidationError({"new_password": list(exc.messages)}) from None

    def change(self, master_id: int, raw_password: str) -> None:
        user = _user(master_id)
        user.set_password(raw_password)
        user.save(update_fields=["password"])
