"""Skip all tests in archived_obsolete_api directory."""
from __future__ import annotations

import pytest

# Skip all tests in this directory - API has changed
collect_ignore_glob = ["test_*.py"]
