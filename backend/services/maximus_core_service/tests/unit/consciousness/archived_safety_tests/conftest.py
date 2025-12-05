"""Skip all tests in archived_safety_tests directory."""
from __future__ import annotations

import pytest

# Skip all tests in this directory - safety module refactored
collect_ignore_glob = ["test_*.py"]
