"""Command-line interface for Route 53 record management."""

import argparse
import sys

from .enums import RecordAction, RecordType
from .errors import RecordValidationError, Route53ManagerError
from .logging import (
    DEFAULT_LOG_LEVEL,
    SUPPORTED_LOG_LEVELS,
    LoggingConfigurationError,
    configure_logging,
    logger,
)
from .manager import Route53Manager
from .models import RecordChangeRequest

DEFAULT_ACTION = RecordAction.CREATE.value
DEFAULT_RECORD_TTL = 300
DEFAULT_RECORD_TYPE = RecordType.A.value
PROGRAM_NAME = "aws-route53-manager"


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="Manage Route 53 hosted zone DNS records.",
    )
    parser.add_argument(
        "record_name",
        metavar="record",
        help="Fully-qualified record name, e.g., app.example.com.",
    )
    parser.add_argument(
        "record_value",
        metavar="value",
        help="Record value: IPv4 address for A records, IPv6 address for AAAA records, DNS name for CNAME records.",
    )
    parser.add_argument(
        "--action",
        type=str.upper,
        choices=RecordAction.values(),
        default=DEFAULT_ACTION,
        help=f"Change action to submit, default: {DEFAULT_ACTION}.",
    )
    parser.add_argument(
        "--ttl",
        type=int,
        default=DEFAULT_RECORD_TTL,
        help=f"DNS record TTL in seconds, default: {DEFAULT_RECORD_TTL}.",
    )
    parser.add_argument(
        "--record-type",
        "--type",
        dest="record_type",
        type=str.upper,
        choices=RecordType.values(),
        default=DEFAULT_RECORD_TYPE,
        help=f"DNS record type, default: {DEFAULT_RECORD_TYPE}.",
    )
    parser.add_argument(
        "--log-level",
        type=str.upper,
        choices=SUPPORTED_LOG_LEVELS,
        default=DEFAULT_LOG_LEVEL,
        help=f"Console log verbosity, default: {DEFAULT_LOG_LEVEL}.",
    )
    parser.add_argument(
        "--log-timestamps",
        action="store_true",
        help="Include timestamps in console log output.",
    )
    return parser


def build_change_request(parsed_args: argparse.Namespace) -> RecordChangeRequest:
    """Convert parsed CLI arguments into a validated change request."""
    return RecordChangeRequest(
        action=parsed_args.action,
        record_name=parsed_args.record_name,
        record_value=parsed_args.record_value,
        ttl=parsed_args.ttl,
        record_type=parsed_args.record_type,
    )


def parse_arguments(args: list[str] | None = None) -> tuple[argparse.Namespace, RecordChangeRequest]:
    """Parse CLI arguments and return validated input data."""
    parser = build_parser()
    parsed_args = parser.parse_args(args)

    try:
        change_request = build_change_request(parsed_args)
    except RecordValidationError as exc:
        parser.error(str(exc))

    return parsed_args, change_request


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, submit the change, and return an exit code."""
    parsed_args, change_request = parse_arguments(argv)

    try:
        configure_logging(
            parsed_args.log_level,
            include_timestamps=parsed_args.log_timestamps,
        )
    except LoggingConfigurationError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1

    try:
        logger.debug(
            "Prepared {} request for {} ({})",
            change_request.action,
            change_request.record_name,
            change_request.record_type,
        )
        route53_manager = Route53Manager()
        change_result = route53_manager.submit_record_change(change_request)
    except Route53ManagerError as exc:
        logger.error("{}", exc)
        return 1

    logger.success(
        "Submitted {} request for {} in hosted zone {} (change id: {}, status: {})",
        change_request.action,
        change_request.record_name,
        change_result.hosted_zone_name,
        change_result.change_id or "unknown",
        change_result.status,
    )
    return 0
