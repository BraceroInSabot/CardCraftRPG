"""Domain-level errors.

They carry no knowledge of HTTP or Django; the presentation layer is
responsible for translating them into transport-specific responses.
"""


class DomainError(Exception):
    """Base class for every error raised by the domain/application layers."""


class ValidationError(DomainError):
    """An entity invariant or business rule was violated.

    ``errors`` maps a field name to a list of human readable messages so the
    API can report every problem at once.
    """

    def __init__(self, errors: dict[str, list[str]]):
        self.errors = errors
        super().__init__("; ".join(f"{field}: {', '.join(msgs)}" for field, msgs in errors.items()))

    @classmethod
    def single(cls, field: str, message: str) -> "ValidationError":
        return cls({field: [message]})


class NotFoundError(DomainError):
    """The requested entity does not exist."""

    def __init__(self, entity_name: str, entity_id: int):
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} with id {entity_id} was not found.")
