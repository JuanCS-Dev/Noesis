"""Article V Guardian Registry.

Governance registration and validation functions.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-13
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


async def register_governance(
    governance_registry: dict[str, dict[str, Any]],
    autonomous_systems: dict[str, dict[str, Any]],
    system_id: str,
    governance_type: str,
    policies: list[str],
    controls: dict[str, Any],
) -> bool:
    """Register governance for an autonomous system.

    Args:
        governance_registry: Registry to store governance records
        autonomous_systems: Registry of autonomous systems
        system_id: Identifier of the autonomous system
        governance_type: Type of governance applied
        policies: List of applicable policies
        controls: Control mechanisms in place

    Returns:
        True if registration successful
    """
    governance_registry[system_id] = {
        "system_id": system_id,
        "governance_type": governance_type,
        "policies": policies,
        "controls": controls,
        "registered_at": datetime.utcnow().isoformat(),
        "validated": False,
    }

    if system_id in autonomous_systems:
        autonomous_systems[system_id]["has_governance"] = True

    return True


async def validate_governance_precedence(
    system_path: str,
) -> tuple[bool, str]:
    """Validate that governance was implemented before autonomy.

    Args:
        system_path: Path to the autonomous system

    Returns:
        Tuple of (is_valid, reason)
    """
    try:
        system_file = Path(system_path)
        module_path = system_file.parent

        governance_files = list(module_path.glob("*governance*.py"))
        policy_files = list(module_path.glob("*policy*.py"))

        if not governance_files and not policy_files:
            return False, "No governance files found in module"

        content = system_file.read_text()

        has_governance_import = (
            "from .governance" in content
            or "from .policy" in content
            or "import governance" in content
        )

        if not has_governance_import:
            return False, "Autonomous system does not import governance"

        return True, "Governance precedence validated"

    except Exception as e:
        return False, f"Validation error: {str(e)}"
