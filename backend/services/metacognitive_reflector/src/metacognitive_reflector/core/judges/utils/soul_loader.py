"""
Judge Soul Integration - Shared soul loading utility.

This module provides common soul loading functionality used by all judges.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from maximus_core_service.consciousness.exocortex.soul.models import SoulConfiguration

logger = logging.getLogger(__name__)


def load_soul_config() -> Optional["SoulConfiguration"]:
    """
    Attempt to load soul configuration.

    Returns None if soul module not available (graceful degradation).
    This is used by all judges for soul integration.
    """
    try:
        from maximus_core_service.consciousness.exocortex.soul import SoulLoader

        return SoulLoader.load()
    except ImportError:
        logger.warning("Soul module not available - judge will operate without soul integration")
        return None
    except Exception as e:
        logger.warning(f"Failed to load soul config: {e}")
        return None

