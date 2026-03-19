"""Compatibility checks for the Python 3.10 baseline."""

import ast
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_SOURCE_PATHS = (
    PROJECT_ROOT / "aws_route53_manager",
    PROJECT_ROOT / "tests",
)


class Python310CompatibilityTests(unittest.TestCase):
    """Ensure the tracked source continues to parse as Python 3.10 code."""

    def test_python_files_parse_with_python310_grammar(self) -> None:
        python_files = sorted(path for source_path in PYTHON_SOURCE_PATHS for path in source_path.rglob("*.py"))
        self.assertTrue(python_files, "No Python files were found for compatibility checks.")

        for path in python_files:
            with self.subTest(path=path.relative_to(PROJECT_ROOT).as_posix()):
                source = path.read_text(encoding="utf-8")
                ast.parse(source, filename=str(path), feature_version=(3, 10))
