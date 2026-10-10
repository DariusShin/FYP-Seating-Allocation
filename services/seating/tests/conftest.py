"""Production test configuration.

Production v4 tests build their own requests from the shared synthetic fixture
in research/fixtures; the repository root must be importable for that module
and still holds the shared historical data fixtures read by some tests.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT
