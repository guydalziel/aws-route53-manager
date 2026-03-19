"""AWS Route 53 service operations."""

import logging
from collections.abc import Mapping
from typing import Any

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ModuleNotFoundError:

    class BotoCoreError(Exception):
        """Fallback botocore error type when botocore is unavailable."""

    class ClientError(Exception):
        """Fallback client error type when botocore is unavailable."""

from .errors import (
    DependencyError,
    InvalidAwsResponseError,
    Route53ManagerError,
)
from .models import (
    HostedZone,
    RecordChangeRequest,
    RecordChangeResult,
)

logger = logging.getLogger(__name__)


class Route53Manager:
    """Submit single-record Route 53 changes to the best matching hosted zone."""

    def __init__(self, client: Any | None = None) -> None:
        self.client = client if client is not None else self._build_default_client()

    @staticmethod
    def _build_default_client() -> Any:
        """Create the default boto3 Route 53 client."""
        try:
            import boto3
        except ModuleNotFoundError as exc:
            raise DependencyError(
                "boto3 is required to submit Route 53 changes. Install the package dependencies."
            ) from exc

        logger.debug("Creating default boto3 Route 53 client")
        return boto3.client("route53")

    def list_hosted_zones(self) -> list[HostedZone]:
        """Return hosted zones sorted from most specific to least specific."""
        hosted_zones: list[HostedZone] = []
        next_dns_name = None
        next_hosted_zone_id = None

        logger.debug("Listing hosted zones from Route 53")
        while True:
            response = self._list_hosted_zones_page(next_dns_name, next_hosted_zone_id)
            page_hosted_zones, is_truncated, next_page = self._parse_list_hosted_zones_response(response)
            logger.debug("Retrieved %s hosted zone(s) from the current page", len(page_hosted_zones))
            hosted_zones.extend(page_hosted_zones)

            if not is_truncated:
                hosted_zones.sort(key=lambda zone: len(zone.name), reverse=True)
                logger.debug("Resolved %s hosted zone(s) in total", len(hosted_zones))
                return hosted_zones

            next_dns_name, next_hosted_zone_id = next_page

    def _list_hosted_zones_page(
        self,
        next_dns_name: str | None,
        next_hosted_zone_id: str | None,
    ) -> dict[str, Any]:
        """Fetch one page of hosted zones from Route 53."""
        request = {"MaxItems": "100"}
        if next_dns_name is not None:
            request["DNSName"] = next_dns_name
        if next_hosted_zone_id is not None:
            request["HostedZoneId"] = next_hosted_zone_id

        try:
            return self.client.list_hosted_zones_by_name(**request)
        except (ClientError, BotoCoreError) as exc:
            raise Route53ManagerError(f"Could not list hosted zones: {exc}") from exc

    def _parse_list_hosted_zones_response(
        self,
        response: object,
    ) -> tuple[list[HostedZone], bool, tuple[str | None, str | None]]:
        """Validate and normalise a list_hosted_zones_by_name response payload."""
        if not isinstance(response, Mapping):
            raise InvalidAwsResponseError("Route 53 hosted zone response must be a mapping.")

        hosted_zone_payloads = response.get("HostedZones")
        if not isinstance(hosted_zone_payloads, list):
            raise InvalidAwsResponseError("Route 53 hosted zone response is missing a HostedZones list.")

        is_truncated = response.get("IsTruncated")
        if not isinstance(is_truncated, bool):
            raise InvalidAwsResponseError("Route 53 hosted zone response is missing a boolean IsTruncated field.")

        next_page = (None, None)
        if is_truncated:
            next_dns_name = response.get("NextDNSName")
            next_hosted_zone_id = response.get("NextHostedZoneId")
            if not isinstance(next_dns_name, str) or not isinstance(next_hosted_zone_id, str):
                raise InvalidAwsResponseError(
                    "Route 53 returned a truncated hosted zone response without pagination markers."
                )
            next_page = (next_dns_name, next_hosted_zone_id)

        return self._parse_hosted_zone_payloads(hosted_zone_payloads), is_truncated, next_page

    @staticmethod
    def _parse_hosted_zone_payloads(hosted_zone_payloads: list[object]) -> list[HostedZone]:
        """Convert a hosted zone payload list into HostedZone objects."""
        hosted_zones: list[HostedZone] = []
        for hosted_zone_payload in hosted_zone_payloads:
            if not isinstance(hosted_zone_payload, Mapping):
                raise InvalidAwsResponseError("Route 53 hosted zone list contained a non-mapping entry.")
            hosted_zones.append(HostedZone.from_api_payload(hosted_zone_payload))

        return hosted_zones

    def find_best_hosted_zone(self, record_name: str) -> HostedZone:
        """Return the most specific hosted zone that can manage record_name."""
        logger.debug("Selecting the best hosted zone for %s", record_name)
        for hosted_zone in self.list_hosted_zones():
            if hosted_zone.matches_record(record_name):
                logger.debug(
                    "Matched %s to hosted zone %s (%s)",
                    record_name,
                    hosted_zone.name,
                    hosted_zone.id,
                )
                return hosted_zone

        raise Route53ManagerError(f"No hosted zone exists in this account for '{record_name}'")

    def submit_record_change(
        self,
        change_request: RecordChangeRequest,
    ) -> RecordChangeResult:
        """Submit a DNS record change and return the accepted change summary."""
        hosted_zone = self.find_best_hosted_zone(change_request.record_name)
        logger.debug(
            "Submitting %s %s record %s with TTL %s",
            change_request.action,
            change_request.record_type,
            change_request.record_name,
            change_request.ttl,
        )

        try:
            response = self.client.change_resource_record_sets(
                HostedZoneId=hosted_zone.id,
                ChangeBatch=change_request.to_change_batch(),
            )
        except (ClientError, BotoCoreError) as exc:
            raise Route53ManagerError(f"DNS change request failed: {exc}") from exc

        change_result = RecordChangeResult.from_api_response(response, hosted_zone)
        logger.debug(
            "Route 53 accepted change %s with status %s",
            change_result.change_id or "unknown",
            change_result.status,
        )
        return change_result
