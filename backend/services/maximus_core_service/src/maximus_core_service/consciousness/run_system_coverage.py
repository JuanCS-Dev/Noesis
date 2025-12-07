"""
Standalone System Coverage Runner - Solves import timing issue
"""

from __future__ import annotations


import sys
import os

# Set PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# CRITICAL: Remove any previously imported consciousness modules
modules_to_remove = [key for key in list(sys.modules.keys()) if key.startswith("consciousness")]
for mod in modules_to_remove:
    del sys.modules[mod]

# Now start coverage BEFORE any consciousness imports
import coverage

cov = coverage.Coverage(
    source=["consciousness.system"], omit=["*/test_*.py", "*/__pycache__/*", "*/tests/*"]
)
cov.start()

# NOW import and run pytest
import pytest

result = pytest.main(
    [
        "-vs",
        "consciousness/test_system_100pct.py",
        "--tb=short",
        "-p",
        "no:cacheprovider",
        "-p",
        "no:cov",
        "-o",
        "addopts=",
    ]
)

# Stop coverage and report
cov.stop()
cov.save()

logger.info("=" * 80)
logger.info("SYSTEM MODULE COVERAGE REPORT")
logger.info("=" * 80)
cov.report(show_missing=True)

sys.exit(result)
