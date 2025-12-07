"""
Standalone Prefrontal Cortex Coverage Runner
"""

from __future__ import annotations


import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

modules_to_remove = [key for key in list(sys.modules.keys()) if key.startswith("consciousness")]
for mod in modules_to_remove:
    del sys.modules[mod]

import coverage

cov = coverage.Coverage(
    source=["consciousness.prefrontal_cortex"], omit=["*/test_*.py", "*/__pycache__/*", "*/tests/*"]
)
cov.start()

import pytest

result = pytest.main(
    [
        "-vs",
        "consciousness/test_prefrontal_cortex_100pct.py",
        "--tb=short",
        "-p",
        "no:cacheprovider",
        "-p",
        "no:cov",
        "-o",
        "addopts=",
    ]
)

cov.stop()
cov.save()

logger.info("=" * 80)
logger.info("PREFRONTAL CORTEX MODULE COVERAGE REPORT")
logger.info("=" * 80)
cov.report(show_missing=True)

sys.exit(result)
