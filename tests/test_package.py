"""Unit tests for package-level exports."""

import unittest

import aws_route53_manager


class PackageTests(unittest.TestCase):
    """Validate package metadata exposed at import time."""

    def test_package_exposes_string_version(self) -> None:
        self.assertIsInstance(aws_route53_manager.__version__, str)
        self.assertTrue(aws_route53_manager.__version__)
