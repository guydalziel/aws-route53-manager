"""Unit tests for the command-line interface."""

import argparse
import contextlib
import io
import unittest
from unittest.mock import MagicMock, patch

from aws_route53_manager.cli import PROGRAM_NAME, build_change_request, build_parser, main, parse_arguments
from aws_route53_manager.enums import RecordAction, RecordType
from aws_route53_manager.errors import Route53ManagerError
from aws_route53_manager.models import RecordChangeRequest, RecordChangeResult


class CliTests(unittest.TestCase):
    """Validate CLI parsing and exit behaviour."""

    def test_build_parser_uses_stable_program_name(self) -> None:
        parser = build_parser()

        self.assertEqual(parser.prog, PROGRAM_NAME)

    def test_build_change_request_constructs_validated_model(self) -> None:
        parsed_args = argparse.Namespace(
            action="UPSERT",
            record_name="App.Example.com.",
            record_value="203.0.113.10",
            ttl=300,
            record_type="A",
        )

        request = build_change_request(parsed_args)

        self.assertEqual(request.action, RecordAction.UPSERT)
        self.assertEqual(request.record_name, "app.example.com")
        self.assertEqual(request.record_type, RecordType.A)

    def test_parse_arguments_exits_on_invalid_input(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                parse_arguments(["app.example.com", "not-an-ip"])

        self.assertEqual(raised.exception.code, 2)

    @patch("aws_route53_manager.logging._get_loguru_logger")
    @patch("aws_route53_manager.cli.Route53Manager")
    @patch("aws_route53_manager.cli.configure_logging")
    def test_main_returns_zero_on_success(
        self,
        configure_logging_mock: MagicMock,
        route53_manager_class_mock: MagicMock,
        get_loguru_logger_mock: MagicMock,
    ) -> None:
        logger_mock = MagicMock()
        get_loguru_logger_mock.return_value = logger_mock
        route53_manager = route53_manager_class_mock.return_value
        route53_manager.submit_record_change.return_value = RecordChangeResult(
            change_id="C123",
            status="PENDING",
            hosted_zone_id="Z123",
            hosted_zone_name="example.com",
        )

        exit_code = main(["app.example.com", "203.0.113.10"])

        self.assertEqual(exit_code, 0)
        configure_logging_mock.assert_called_once()
        logger_mock.success.assert_called_once()

    @patch("aws_route53_manager.logging._get_loguru_logger")
    @patch("aws_route53_manager.cli.Route53Manager")
    @patch("aws_route53_manager.cli.configure_logging")
    def test_main_returns_one_on_route53_errors(
        self,
        configure_logging_mock: MagicMock,
        route53_manager_class_mock: MagicMock,
        get_loguru_logger_mock: MagicMock,
    ) -> None:
        logger_mock = MagicMock()
        get_loguru_logger_mock.return_value = logger_mock
        route53_manager = route53_manager_class_mock.return_value
        route53_manager.submit_record_change.side_effect = Route53ManagerError("boom")

        exit_code = main(["app.example.com", "203.0.113.10"])

        self.assertEqual(exit_code, 1)
        configure_logging_mock.assert_called_once()
        logger_mock.error.assert_called_once()
