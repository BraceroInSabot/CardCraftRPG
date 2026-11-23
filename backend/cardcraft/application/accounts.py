"""Use cases behind a Master's settings page."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any

from cardcraft.domain.accounts import Master, MasterRepository
from cardcraft.domain.exceptions import ValidationError

from .ports import PasswordService

PROFILE_FIELDS = frozenset({"display_name", "email"})
CARD_DEFAULT_FIELDS = frozenset({"default_background_color"})


class GetMaster:
    def __init__(self, masters: MasterRepository):
        self._masters = masters

    def execute(self, master_id: int) -> Master:
        return self._masters.get(master_id)


class UpdateMasterFields:
    """Change a fixed group of a Master's fields (profile, card defaults...)."""

    def __init__(self, masters: MasterRepository, editable: frozenset[str]):
        self._masters = masters
        self._editable = editable

    def execute(self, master_id: int, changes: Mapping[str, Any]) -> Master:
        current = self._masters.get(master_id)
        accepted = {key: value for key, value in changes.items() if key in self._editable}
        return self._masters.update(replace(current, **accepted))  # replace re-runs validation


class ChangePassword:
    """A new password is only accepted together with the current one."""

    def __init__(self, masters: MasterRepository, passwords: PasswordService):
        self._masters = masters
        self._passwords = passwords

    def execute(self, master_id: int, current_password: str, new_password: str) -> None:
        self._masters.get(master_id)  # raises NotFoundError for unknown accounts
        if not self._passwords.verify(master_id, current_password):
            raise ValidationError.single("current_password", "The current password is incorrect.")
        if new_password == current_password:
            raise ValidationError.single("new_password", "Choose a password different from the current one.")
        self._passwords.validate(master_id, new_password)
        self._passwords.change(master_id, new_password)


@dataclass(frozen=True)
class AccountUseCases:
    get: GetMaster
    update_profile: UpdateMasterFields
    update_card_defaults: UpdateMasterFields
    change_password: ChangePassword

    @classmethod
    def build(cls, masters: MasterRepository, passwords: PasswordService) -> AccountUseCases:
        return cls(
            get=GetMaster(masters),
            update_profile=UpdateMasterFields(masters, PROFILE_FIELDS),
            update_card_defaults=UpdateMasterFields(masters, CARD_DEFAULT_FIELDS),
            change_password=ChangePassword(masters, passwords),
        )
