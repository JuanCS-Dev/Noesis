"""
Pytest configuration for Metacognitive Reflector tests.
"""

from __future__ import annotations


import sys
from pathlib import Path

# Add services directory to path so metacognitive_reflector is a valid package
services_dir = Path(__file__).parent.parent.parent
if str(services_dir) not in sys.path:
    sys.path.insert(0, str(services_dir))
