"""Skip all tests in archived_broken_fixtures directory."""
from __future__ import annotations

import pytest

# Skip all tests in this directory - fixtures are broken/obsolete
collect_ignore_glob = ["test_*.py"]
