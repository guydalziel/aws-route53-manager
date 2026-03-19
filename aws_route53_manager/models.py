"""Route 53 domain models."""

from collections.abc import Mapping
from dataclasses import dataclass

from .enums import RecordAction, RecordType
from .errors import InvalidAwsResponseError


def _normalise_route53_resource_id(resource_id: str) -> str:
    """Trim Route 53 API path prefixes from identifiers."""
    return resource_id.strip().split("/")[-1]


def _normalise_dns_name(value: str) -> str:
    """Normalise a DNS name for comparisons and AWS API payloads."""
    return value.strip().rstrip(".").lower()


@dataclass(frozen=True, slots=True)
class HostedZone:
    """Normalised Route 53 hosted zone metadata."""

    id: str
    name: str

    @classmethod
    def from_api_payload(cls, hosted_zone_payload: Mapping[str, object]) -> "HostedZone":
        """Build a HostedZone from a Route 53 API response payload."""
        match hosted_zone_payload:
            case {"Id": str(raw_zone_id), "Name": str(raw_zone_name)}:
                zone_id = _normalise_route53_resource_id(raw_zone_id)
                zone_name = _normalise_dns_name(raw_zone_name)
            case _:
                raise InvalidAwsResponseError("Hosted zone payload is missing required string fields 'Id' and 'Name'.")

        if not zone_id or not zone_name:
            raise InvalidAwsResponseError("Hosted zone payload contained an empty identifier or name.")

        return cls(id=zone_id, name=zone_name)

    def matches_record(self, record_name: str) -> bool:
        """Return True when this hosted zone can manage record_name."""
        candidate_name = _normalise_dns_name(record_name)
        return candidate_name == self.name or candidate_name.endswith(f".{self.name}")


@dataclass(frozen=True, slots=True)
class RecordChangeRequest:
    """Normalised description of a single DNS record change."""

    action: RecordAction
    record_name: str
    record_value: str
    ttl: int
    record_type: RecordType

    def __post_init__(self) -> None:
        """Normalise and validate all request fields."""
        from .validation import RecordInputValidator

        normalised_action = RecordAction.coerce(self.action)
        normalised_record_type = RecordType.coerce(self.record_type)
        normalised_record_name = RecordInputValidator.validate_record_name(self.record_name)
        normalised_ttl = RecordInputValidator.validate_ttl(self.ttl)
        normalised_record_value = RecordInputValidator.validate_record_value(normalised_record_type, self.record_value)

        object.__setattr__(self, "action", normalised_action)
        object.__setattr__(self, "record_name", normalised_record_name)
        object.__setattr__(self, "record_value", normalised_record_value)
        object.__setattr__(self, "ttl", normalised_ttl)
        object.__setattr__(self, "record_type", normalised_record_type)

    def to_change_batch(self) -> dict[str, object]:
        """Build the Route 53 ChangeBatch payload for this record change."""
        return {
            "Changes": [
                {
                    "Action": self.action.value,
                    "ResourceRecordSet": {
                        "Name": self.record_name,
                        "Type": self.record_type.value,
                        "TTL": self.ttl,
                        "ResourceRecords": [{"Value": self.record_value}],
                    },
                }
            ]
        }


@dataclass(frozen=True, slots=True)
class RecordChangeResult:
    """Summary returned by Route 53 after a change request is accepted."""

    change_id: str
    status: str
    hosted_zone_id: str
    hosted_zone_name: str

    @classmethod
    def from_api_response(cls, response: Mapping[str, object], hosted_zone: HostedZone) -> "RecordChangeResult":
        """Build a change result from a Route 53 change_resource_record_sets response."""
        match response.get("ChangeInfo"):
            case {"Id": str(raw_change_id), "Status": str(status)}:
                change_id = _normalise_route53_resource_id(raw_change_id)
            case _:
                raise InvalidAwsResponseError("Route 53 change response is missing required ChangeInfo.Id or ChangeInfo.Status fields.")

        if not change_id or not status:
            raise InvalidAwsResponseError("Route 53 change response contained an empty change identifier or status.")

        return cls(
            change_id=change_id,
            status=status,
            hosted_zone_id=hosted_zone.id,
            hosted_zone_name=hosted_zone.name,
        )
