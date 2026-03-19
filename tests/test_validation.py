"""Unit tests for record input validation."""

import unittest

from aws_route53_manager.enums import RecordType
from aws_route53_manager.errors import RecordValidationError
from aws_route53_manager.validation import RecordInputValidator


class RecordInputValidatorTests(unittest.TestCase):
    """Validate record parsing and normalisation helpers."""

    def test_validate_record_name_normalises_case_and_trailing_dot(self) -> None:
        self.assertEqual(
            RecordInputValidator.validate_record_name("App.Example.com."),
            "app.example.com",
        )

    def test_validate_record_name_allows_wildcard_in_first_label(self) -> None:
        self.assertEqual(
            RecordInputValidator.validate_record_name("*.example.com"),
            "*.example.com",
        )

    def test_validate_record_name_rejects_non_string_values(self) -> None:
        with self.assertRaises(RecordValidationError):
            RecordInputValidator.validate_record_name(123)  # type: ignore[arg-type]

    def test_validate_record_value_validates_ipv4_addresses(self) -> None:
        self.assertEqual(
            RecordInputValidator.validate_record_value(RecordType.A, "203.0.113.10"),
            "203.0.113.10",
        )

    def test_validate_record_value_validates_ipv6_addresses(self) -> None:
        self.assertEqual(
            RecordInputValidator.validate_record_value(RecordType.AAAA, "2001:db8::10"),
            "2001:db8::10",
        )

    def test_validate_record_value_validates_cname_targets(self) -> None:
        self.assertEqual(
            RecordInputValidator.validate_record_value(RecordType.CNAME, "Target.Example.com."),
            "target.example.com",
        )

    def test_validate_record_value_rejects_invalid_ipv6_addresses(self) -> None:
        with self.assertRaises(RecordValidationError):
            RecordInputValidator.validate_record_value(RecordType.AAAA, "not-an-ipv6")

    def test_validate_ttl_rejects_negative_values(self) -> None:
        with self.assertRaises(RecordValidationError):
            RecordInputValidator.validate_ttl(-1)

    def test_validate_ttl_rejects_boolean_values(self) -> None:
        with self.assertRaises(RecordValidationError):
            RecordInputValidator.validate_ttl(True)

    def test_validate_ttl_rejects_none(self) -> None:
        with self.assertRaises(RecordValidationError):
            RecordInputValidator.validate_ttl(None)  # type: ignore[arg-type]
