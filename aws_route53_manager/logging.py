"""Central loguru configuration for the Route 53 manager CLI."""

import logging as stdlib_logging
import sys
from collections.abc import Callable
from typing import Any

from aws_route53_manager.errors import DependencyError

DEFAULT_LOG_LEVEL = "INFO"
SUPPORTED_LOG_LEVELS = (
    "TRACE",
    "DEBUG",
    "INFO",
    "SUCCESS",
    "WARNING",
    "ERROR",
    "CRITICAL",
)


class LoggingConfigurationError(DependencyError):
    """Raised when loguru is unavailable or cannot be configured."""


def _get_loguru_logger() -> Any:
    """Return the loguru logger or raise a clear configuration error."""
    try:
        from loguru import logger as loguru_logger
    except ModuleNotFoundError as exc:
        raise LoggingConfigurationError(
            "loguru is required for CLI logging. Install requirements.txt with a Python 3.10+ interpreter."
        ) from exc

    return loguru_logger


class _LoggerProxy:
    """Lazy proxy around loguru's global logger."""

    def __getattr__(self, name: str) -> Any:
        return getattr(_get_loguru_logger(), name)


logger = _LoggerProxy()


def _build_console_format(*, include_timestamps: bool, prefix: str | None = None, include_level_name: bool = False) -> str:
    """Build a concise console log format string."""
    parts: list[str] = []

    if include_timestamps:
        parts.append("<dim>{time:HH:mm:ss}</dim>")
    if prefix is not None:
        parts.append(prefix)
    elif include_level_name:
        parts.append("<dim>{level: <8}</dim>")

    parts.append("<level>{message}</level>")
    return " ".join(parts)


def _level_filter(levels: set[str]) -> Callable[[dict[str, Any]], bool]:
    """Build a loguru sink filter for a fixed set of level names."""

    def level_filter(record: dict[str, Any]) -> bool:
        return record["level"].name in levels

    return level_filter


class _InterceptHandler(stdlib_logging.Handler):
    """Route stdlib log records into loguru sinks configured by the CLI."""

    def emit(self, record: stdlib_logging.LogRecord) -> None:
        loguru_logger = _get_loguru_logger()

        try:
            level_name = loguru_logger.level(record.levelname).name
        except ValueError:
            level_name = record.levelname

        loguru_logger.opt(exception=record.exc_info).log(level_name, record.getMessage())


def _configure_library_logging(level: str) -> None:
    """Attach a stdlib logging handler for the package namespace."""
    package_logger = stdlib_logging.getLogger("aws_route53_manager")
    package_logger.handlers = [_InterceptHandler()]
    package_logger.setLevel(level)
    package_logger.propagate = False


def configure_logging(level: str = DEFAULT_LOG_LEVEL, *, include_timestamps: bool = False) -> None:
    """Configure the application logger for human-oriented console output."""
    loguru_logger = _get_loguru_logger()
    loguru_logger.remove()

    configured_level = level.upper()
    loguru_logger.add(
        sys.stdout,
        level=configured_level,
        filter=_level_filter({"INFO", "SUCCESS"}),
        format=_build_console_format(include_timestamps=include_timestamps),
    )
    loguru_logger.add(
        sys.stderr,
        level=configured_level,
        filter=_level_filter({"TRACE", "DEBUG"}),
        format=_build_console_format(
            include_timestamps=include_timestamps,
            include_level_name=True,
        ),
    )
    loguru_logger.add(
        sys.stderr,
        level=configured_level,
        filter=_level_filter({"WARNING"}),
        format=_build_console_format(
            include_timestamps=include_timestamps,
            prefix="<yellow>warning:</yellow>",
        ),
    )
    loguru_logger.add(
        sys.stderr,
        level=configured_level,
        filter=_level_filter({"ERROR", "CRITICAL"}),
        format=_build_console_format(
            include_timestamps=include_timestamps,
            prefix="<red>error:</red>",
        ),
    )
    _configure_library_logging(configured_level)
