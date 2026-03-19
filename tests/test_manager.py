"""Unit tests for Route 53 service interactions."""

import unittest

from aws_route53_manager.enums import RecordAction, RecordType
from aws_route53_manager.errors import InvalidAwsResponseError, Route53ManagerError
from aws_route53_manager.manager import Route53Manager
from aws_route53_manager.models import RecordChangeRequest


class FakeRoute53Client:
    """Simple fake Route 53 client used by manager tests."""

    def __init__(self, list_responses: list[object], change_response: object | None = None) -> None:
        self.list_responses = list(list_responses)
        self.change_response = change_response
        self.list_calls: list[dict[str, object]] = []
        self.change_calls: list[dict[str, object]] = []

    def list_hosted_zones_by_name(self, **kwargs: object) -> object:
        self.list_calls.append(kwargs)
        return self.list_responses.pop(0)

    def change_resource_record_sets(self, **kwargs: object) -> object:
        self.change_calls.append(kwargs)
        return self.change_response


class Route53ManagerTests(unittest.TestCase):
    """Validate hosted zone selection and strict response parsing."""

    def test_list_hosted_zones_returns_most_specific_first(self) -> None:
        client = FakeRoute53Client(
            [
                {
                    "HostedZones": [
                        {"Id": "/hostedzone/Z1", "Name": "example.com."},
                    ],
                    "IsTruncated": True,
                    "NextDNSName": "dev.example.com.",
                    "NextHostedZoneId": "/hostedzone/Z2",
                },
                {
                    "HostedZones": [
                        {"Id": "/hostedzone/Z2", "Name": "dev.example.com."},
                    ],
                    "IsTruncated": False,
                },
            ]
        )

        manager = Route53Manager(client=client)
        hosted_zones = manager.list_hosted_zones()

        self.assertEqual([zone.name for zone in hosted_zones], ["dev.example.com", "example.com"])

    def test_list_hosted_zones_rejects_malformed_responses(self) -> None:
        client = FakeRoute53Client([{"HostedZones": {"bad": "payload"}, "IsTruncated": False}])
        manager = Route53Manager(client=client)

        with self.assertRaises(InvalidAwsResponseError):
            manager.list_hosted_zones()

    def test_find_best_hosted_zone_uses_longest_matching_zone(self) -> None:
        client = FakeRoute53Client(
            [
                {
                    "HostedZones": [
                        {"Id": "/hostedzone/Z1", "Name": "example.com."},
                        {"Id": "/hostedzone/Z2", "Name": "dev.example.com."},
                    ],
                    "IsTruncated": False,
                }
            ]
        )

        manager = Route53Manager(client=client)
        hosted_zone = manager.find_best_hosted_zone("api.dev.example.com")

        self.assertEqual(hosted_zone.id, "Z2")

    def test_find_best_hosted_zone_raises_when_no_zone_matches(self) -> None:
        client = FakeRoute53Client(
            [
                {
                    "HostedZones": [
                        {"Id": "/hostedzone/Z1", "Name": "example.com."},
                    ],
                    "IsTruncated": False,
                }
            ]
        )

        manager = Route53Manager(client=client)

        with self.assertRaises(Route53ManagerError):
            manager.find_best_hosted_zone("app.otherdomain.com")

    def test_submit_record_change_returns_parsed_change_result(self) -> None:
        client = FakeRoute53Client(
            [
                {
                    "HostedZones": [
                        {"Id": "/hostedzone/Z1", "Name": "example.com."},
                    ],
                    "IsTruncated": False,
                }
            ],
            change_response={"ChangeInfo": {"Id": "/change/C123", "Status": "PENDING"}},
        )
        manager = Route53Manager(client=client)
        request = RecordChangeRequest(
            action=RecordAction.UPSERT,
            record_name="app.example.com",
            record_value="203.0.113.10",
            ttl=300,
            record_type=RecordType.A,
        )

        result = manager.submit_record_change(request)

        self.assertEqual(result.change_id, "C123")
        self.assertEqual(result.hosted_zone_name, "example.com")
