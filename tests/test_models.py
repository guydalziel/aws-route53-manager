"""Unit tests for Route 53 domain models."""

import unittest

from aws_route53_manager.enums import RecordAction, RecordType
from aws_route53_manager.errors import InvalidAwsResponseError
from aws_route53_manager.models import HostedZone, RecordChangeRequest, RecordChangeResult


class HostedZoneTests(unittest.TestCase):
    """Validate hosted zone parsing behaviour."""

    def test_from_api_payload_normalises_fields(self) -> None:
        hosted_zone = HostedZone.from_api_payload(
            {"Id": "/hostedzone/Z123", "Name": "Example.com."}
        )

        self.assertEqual(hosted_zone.id, "Z123")
        self.assertEqual(hosted_zone.name, "example.com")

    def test_from_api_payload_rejects_invalid_payloads(self) -> None:
        with self.assertRaises(InvalidAwsResponseError):
            HostedZone.from_api_payload({"Id": 123, "Name": "example.com"})  # type: ignore[dict-item]

    def test_matches_record_normalises_case_and_trailing_dot(self) -> None:
        hosted_zone = HostedZone(id="Z123", name="example.com")

        self.assertTrue(hosted_zone.matches_record("App.Example.com."))


class RecordChangeRequestTests(unittest.TestCase):
    """Validate request normalisation at the model boundary."""

    def test_request_coerces_strings_to_enums_and_normalised_values(self) -> None:
        request = RecordChangeRequest(
            action="upsert",
            record_name="App.Example.com.",
            record_value="2001:db8::10",
            ttl="300",
            record_type="aaaa",
        )

        self.assertEqual(request.action, RecordAction.UPSERT)
        self.assertEqual(request.record_type, RecordType.AAAA)
        self.assertEqual(request.record_name, "app.example.com")
        self.assertEqual(request.record_value, "2001:db8::10")
        self.assertEqual(request.ttl, 300)

    def test_to_change_batch_uses_enum_values(self) -> None:
        request = RecordChangeRequest(
            action=RecordAction.CREATE,
            record_name="app.example.com",
            record_value="203.0.113.10",
            ttl=300,
            record_type=RecordType.A,
        )

        self.assertEqual(
            request.to_change_batch()["Changes"][0]["Action"],
            "CREATE",
        )


class RecordChangeResultTests(unittest.TestCase):
    """Validate change response parsing behaviour."""

    def test_from_api_response_requires_change_info(self) -> None:
        hosted_zone = HostedZone(id="Z123", name="example.com")

        with self.assertRaises(InvalidAwsResponseError):
            RecordChangeResult.from_api_response({}, hosted_zone)

    def test_from_api_response_parses_change_fields(self) -> None:
        hosted_zone = HostedZone(id="Z123", name="example.com")
        result = RecordChangeResult.from_api_response(
            {"ChangeInfo": {"Id": "/change/C123", "Status": "PENDING"}},
            hosted_zone,
        )

        self.assertEqual(result.change_id, "C123")
        self.assertEqual(result.status, "PENDING")

    def test_from_api_response_rejects_empty_change_fields(self) -> None:
        hosted_zone = HostedZone(id="Z123", name="example.com")

        with self.assertRaises(InvalidAwsResponseError):
            RecordChangeResult.from_api_response({"ChangeInfo": {"Id": "/change/", "Status": ""}}, hosted_zone)
