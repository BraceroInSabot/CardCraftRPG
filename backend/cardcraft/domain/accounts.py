"""Accounts of the people who use Card Craft.

A ``Master`` (game master) owns RPG systems and, through them, every card.
Credentials are not part of the entity: checking and changing passwords is a
port of the application layer, so the domain never sees a password hash.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from .entities import DEFAULT_BACKGROUND_COLOR, Entity, _ErrorCollector, _HEX_COLOR

USERNAME_MAX_LENGTH = 150
DISPLAY_NAME_MAX_LENGTH = 120
EMAIL_MAX_LENGTH = 254

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(kw_only=True)
class Master(Entity):
    """A game master: profile data plus the defaults applied to new cards."""

    entity_name: ClassVar[str] = "Master"
    # The login name identifies the account; it is not editable from the settings page.
    managed_fields: ClassVar[frozenset[str]] = frozenset({"id", "username"})

    username: str
    display_name: str = ""
    email: str = ""
    default_background_color: str = DEFAULT_BACKGROUND_COLOR

    def _normalize(self) -> None:
        super()._normalize()
        self.username = (self.username or "").strip()
        self.display_name = (self.display_name or "").strip()
        self.email = (self.email or "").strip().lower()
        self.default_background_color = (
            (self.default_background_color or DEFAULT_BACKGROUND_COLOR).strip().lower()
        )

    def _collect_errors(self, errors: _ErrorCollector) -> None:
        super()._collect_errors(errors)
        errors.require_text("username", self.username, USERNAME_MAX_LENGTH)
        errors.limit_text("display_name", self.display_name, DISPLAY_NAME_MAX_LENGTH)
        errors.limit_text("email", self.email, EMAIL_MAX_LENGTH)
        if self.email and not _EMAIL.match(self.email):
            errors.add("email", "Enter a valid email address.")
        if not _HEX_COLOR.match(self.default_background_color):
            errors.add("default_background_color", "Use a hex color such as #ffffff.")

    @property
    def shown_name(self) -> str:
        return self.display_name or self.username


class MasterRepository(ABC):
    @abstractmethod
    def get(self, master_id: int) -> Master:
        """Return the Master or raise ``NotFoundError``."""

    @abstractmethod
    def update(self, master: Master) -> Master: ...
