"""
Planning Mixin for Response Orchestrator.

Contains response action generation and execution order planning.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .models import ActionType, ResponseAction, ResponsePriority


class PlanningMixin:
    """Mixin providing response planning capabilities."""

    total_actions: int

    async def _generate_response_actions(
        self,
        threat_category: str,
        entities: Dict[str, Any],
        priority: ResponsePriority,
        mitre_tactics: List[str] = None
    ) -> List[ResponseAction]:
        """Generate appropriate response actions for threat."""
        actions = []

        # Network-based threats
        if "ip" in entities:
            actions.append(ResponseAction(
                action_type=ActionType.BLOCK_IP,
                target={"ip": entities["ip"]},
                parameters={"duration_minutes": 60},
                priority=priority,
                reversible=True
            ))

            if priority == ResponsePriority.CRITICAL:
                actions.append(ResponseAction(
                    action_type=ActionType.UPDATE_FIREWALL,
                    target={"ip": entities["ip"]},
                    parameters={"rule": "deny_all"},
                    priority=priority
                ))

        # Host-based threats
        if "hostname" in entities:
            if priority in [ResponsePriority.CRITICAL, ResponsePriority.HIGH]:
                actions.append(ResponseAction(
                    action_type=ActionType.ISOLATE_HOST,
                    target={"hostname": entities["hostname"]},
                    parameters={"allow_management": True},
                    priority=priority,
                    reversible=True
                ))

        # Process threats
        if "process" in entities or "pid" in entities:
            actions.append(ResponseAction(
                action_type=ActionType.KILL_PROCESS,
                target=entities,
                priority=priority,
                reversible=False
            ))

        # File threats
        if "file_path" in entities or "file_hash" in entities:
            actions.append(ResponseAction(
                action_type=ActionType.QUARANTINE_FILE,
                target=entities,
                priority=priority,
                reversible=True
            ))

        # User threats
        if "user" in entities or "username" in entities:
            if priority == ResponsePriority.CRITICAL:
                actions.append(ResponseAction(
                    action_type=ActionType.DISABLE_USER,
                    target=entities,
                    priority=priority,
                    reversible=True
                ))
            else:
                actions.append(ResponseAction(
                    action_type=ActionType.FORCE_LOGOUT,
                    target=entities,
                    priority=priority
                ))

        # Critical threats - emergency response
        if priority == ResponsePriority.CRITICAL:
            if threat_category in ["EXFILTRATION", "COMMAND_CONTROL"]:
                actions.append(ResponseAction(
                    action_type=ActionType.ACTIVATE_KILL_SWITCH,
                    target={"system": "all"},
                    parameters={"severity": "high"},
                    priority=ResponsePriority.CRITICAL,
                    requires_approval=True
                ))

            # Enable data diode for critical data protection
            actions.append(ResponseAction(
                action_type=ActionType.ENABLE_DATA_DIODE,
                target={"direction": "outbound"},
                priority=ResponsePriority.CRITICAL,
                reversible=True
            ))

        # Add defensive actions
        if threat_category == "RECONNAISSANCE":
            actions.append(ResponseAction(
                action_type=ActionType.DEPLOY_HONEYPOT,
                target={"type": "decoy_service"},
                parameters={"port": entities.get("port", 22)},
                priority=priority
            ))

        # Credential-based threats
        if threat_category == "CREDENTIAL_ACCESS":
            actions.append(ResponseAction(
                action_type=ActionType.ROTATE_CREDENTIALS,
                target={"scope": "affected_users"},
                priority=priority
            ))

        self.total_actions += len(actions)

        return actions

    def _plan_execution_order(
        self,
        actions: List[ResponseAction]
    ) -> Tuple[List[str], List[List[str]]]:
        """Plan the execution order of actions."""
        # Group by dependencies
        critical_actions = []
        high_actions = []
        medium_actions = []
        low_actions = []

        for action in actions:
            if action.priority == ResponsePriority.CRITICAL:
                critical_actions.append(action.action_id)
            elif action.priority == ResponsePriority.HIGH:
                high_actions.append(action.action_id)
            elif action.priority == ResponsePriority.MEDIUM:
                medium_actions.append(action.action_id)
            else:
                low_actions.append(action.action_id)

        # Execution order: critical first, then high, medium, low
        execution_order = critical_actions + high_actions + medium_actions + low_actions

        # Parallel groups - same priority can run in parallel
        parallel_groups = []
        if critical_actions:
            parallel_groups.append(critical_actions)
        if high_actions:
            parallel_groups.append(high_actions)
        if medium_actions:
            parallel_groups.append(medium_actions)
        if low_actions:
            parallel_groups.append(low_actions)

        return execution_order, parallel_groups
