"""Shared exception types for the Route 53 manager package."""


class Route53ManagerError(Exception):
    """Base exception for Route 53 manager failures."""


class DependencyError(Route53ManagerError):
    """Raised when an optional runtime dependency is unavailable."""


class InvalidAwsResponseError(Route53ManagerError):
    """Raised when the AWS SDK returns an unexpected response shape."""


class RecordValidationError(Route53ManagerError, ValueError):
    """Raised when a record change request contains invalid input."""
