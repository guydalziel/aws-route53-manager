"""Validation helpers for Route 53 record changes."""

import ipaddress

from .enums import RecordType
from .errors import RecordValidationError


class RecordInputValidator:
    """Validate and normalise CLI input for Route 53 record changes."""

    MAX_FQDN_LENGTH = 253
    MAX_LABEL_LENGTH = 63

    @classmethod
    def validate_ttl(cls, value: int | str) -> int:
        """Validate that a TTL is a non-negative integer."""
        if isinstance(value, bool):
            raise RecordValidationError(f"invalid TTL '{value}'")

        try:
            ttl = int(value)
        except (TypeError, ValueError) as exc:
            raise RecordValidationError(f"invalid TTL '{value}'") from exc

        if ttl < 0:
            raise RecordValidationError(f"invalid TTL '{value}'")

        return ttl

    @classmethod
    def validate_record_name(cls, record_name: str) -> str:
        """Validate a record name and allow a wildcard only in the first label."""
        return cls.validate_dns_name(record_name, allow_wildcard=True)

    @classmethod
    def validate_record_value(cls, record_type: RecordType | str, record_value: str) -> str:
        """Validate and normalise a record value for the requested record type."""
        if not isinstance(record_value, str):
            raise RecordValidationError("record value must be a string")

        normalised_record_type = RecordType.coerce(record_type)
        cleaned_value = record_value.strip()
        if not cleaned_value:
            raise RecordValidationError("record value cannot be empty")

        match normalised_record_type:
            case RecordType.A:
                return cls.validate_ipv4_address(cleaned_value)
            case RecordType.AAAA:
                return cls.validate_ipv6_address(cleaned_value)
            case RecordType.CNAME:
                return cls.validate_cname_target(cleaned_value)
            case _:
                raise RecordValidationError(f"unsupported record type '{record_type}'")

    @classmethod
    def validate_cname_target(cls, record_value: str) -> str:
        """Validate a CNAME target as a non-wildcard fully-qualified DNS name."""
        return cls.validate_dns_name(record_value, allow_wildcard=False)

    @classmethod
    def validate_dns_name(cls, value: str, allow_wildcard: bool) -> str:
        """Validate and normalise a DNS name."""
        if not isinstance(value, str):
            raise RecordValidationError("DNS names must be strings")

        normalised_name = cls.normalise_dns_name(value)

        if not normalised_name or len(normalised_name) > cls.MAX_FQDN_LENGTH:
            raise RecordValidationError(f"invalid FQDN '{value}'")

        labels = normalised_name.split(".")
        if len(labels) < 2:
            raise RecordValidationError(f"invalid FQDN '{value}'")

        for index, label in enumerate(labels):
            if allow_wildcard and index == 0 and label == "*":
                continue

            if not cls.is_valid_dns_label(label):
                raise RecordValidationError(f"invalid FQDN '{value}'")

        return normalised_name

    @classmethod
    def validate_ipv4_address(cls, value: str) -> str:
        """Validate an IPv4 address and return its canonical dotted-decimal form."""
        if not isinstance(value, str):
            raise RecordValidationError("IPv4 addresses must be strings")

        try:
            return str(ipaddress.IPv4Address(value))
        except ipaddress.AddressValueError as exc:
            raise RecordValidationError(f"invalid IPv4 address '{value}'") from exc

    @classmethod
    def validate_ipv6_address(cls, value: str) -> str:
        """Validate an IPv6 address and return its canonical representation."""
        if not isinstance(value, str):
            raise RecordValidationError("IPv6 addresses must be strings")

        try:
            return str(ipaddress.IPv6Address(value))
        except ipaddress.AddressValueError as exc:
            raise RecordValidationError(f"invalid IPv6 address '{value}'") from exc

    @classmethod
    def normalise_dns_name(cls, value: str) -> str:
        """Normalise a DNS name for comparisons and AWS API payloads."""
        if not isinstance(value, str):
            raise RecordValidationError("DNS names must be strings")

        return value.strip().rstrip(".").lower()

    @classmethod
    def is_valid_dns_label(cls, label: str) -> bool:
        """Return True when label is a valid DNS label for this utility."""
        if not label or len(label) > cls.MAX_LABEL_LENGTH:
            return False

        if label[0] == "-" or label[-1] == "-":
            return False

        for character in label:
            if character in "-_":
                continue

            if not (character.isascii() and character.isalnum()):
                return False

        return True
