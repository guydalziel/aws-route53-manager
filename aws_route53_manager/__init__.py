"""Route 53 record management package."""

from importlib.metadata import PackageNotFoundError, version as package_version

from aws_route53_manager.enums import RecordAction, RecordType
from aws_route53_manager.errors import (
    DependencyError,
    InvalidAwsResponseError,
    RecordValidationError,
    Route53ManagerError,
)
from aws_route53_manager.manager import Route53Manager
from aws_route53_manager.models import HostedZone, RecordChangeRequest, RecordChangeResult


def _resolve_package_version() -> str:
    """Return the installed or generated package version."""

    try:
        from aws_route53_manager._version import version
    except ImportError:
        try:
            return package_version("aws-route53-manager")
        except PackageNotFoundError:
            return "0+unknown"

    return version


__version__ = _resolve_package_version()

__all__ = [
    "DependencyError",
    "HostedZone",
    "InvalidAwsResponseError",
    "RecordAction",
    "RecordChangeRequest",
    "RecordChangeResult",
    "RecordType",
    "RecordValidationError",
    "Route53Manager",
    "Route53ManagerError",
    "__version__",
]
