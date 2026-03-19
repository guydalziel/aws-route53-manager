"""Enum types used by Route 53 record management models."""

from enum import Enum

from .errors import RecordValidationError


class _StringEnum(str, Enum):
    """String-backed enum with convenience helpers for CLI-friendly values."""

    def __str__(self) -> str:
        return self.value

    @classmethod
    def values(cls) -> tuple[str, ...]:
        """Return the string values accepted by the enum."""
        return tuple(member.value for member in cls)


class RecordAction(_StringEnum):
    """Supported Route 53 change actions."""

    CREATE = "CREATE"
    DELETE = "DELETE"
    UPSERT = "UPSERT"

    @classmethod
    def coerce(cls, value: "RecordAction | str") -> "RecordAction":
        """Convert a string or enum value into a RecordAction."""
        if isinstance(value, cls):
            return value

        if isinstance(value, str):
            try:
                return cls(value.upper())
            except ValueError as exc:
                raise RecordValidationError(f"unsupported action '{value}'") from exc

        raise RecordValidationError(f"unsupported action '{value}'")


class RecordType(_StringEnum):
    """Supported single-value Route 53 record types."""

    # TO-DO: Support multi-line records and more complex record types.

    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"

    @classmethod
    def coerce(cls, value: "RecordType | str") -> "RecordType":
        """Convert a string or enum value into a RecordType."""
        if isinstance(value, cls):
            return value

        if isinstance(value, str):
            try:
                return cls(value.upper())
            except ValueError as exc:
                raise RecordValidationError(f"unsupported record type '{value}'") from exc

        raise RecordValidationError(f"unsupported record type '{value}'")
