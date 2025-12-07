"""
Helper Methods Mixin for Decision Framework.

Convenience methods for common security actions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..base_pkg import ActionType

if TYPE_CHECKING:
    from .models import DecisionResult


class HelperMethodsMixin:
    """
    Mixin for convenience methods.

    Provides simplified interfaces for common security actions.
    """

    def block_ip(
        self, ip_address: str, confidence: float, threat_score: float, reason: str
    ) -> DecisionResult:
        """
        Convenience method to block IP address.

        Args:
            ip_address: IP address to block
            confidence: AI confidence in decision
            threat_score: Threat severity score
            reason: Reason for blocking

        Returns:
            DecisionResult
        """
        return self.evaluate_action(
            action_type=ActionType.BLOCK_IP,
            action_params={"ip_address": ip_address},
            ai_reasoning=reason,
            confidence=confidence,
            threat_score=threat_score,
        )

    def isolate_host(
        self, host_id: str, confidence: float, threat_score: float, reason: str
    ) -> DecisionResult:
        """
        Convenience method to isolate host.

        Args:
            host_id: Host identifier
            confidence: AI confidence in decision
            threat_score: Threat severity score
            reason: Reason for isolation

        Returns:
            DecisionResult
        """
        return self.evaluate_action(
            action_type=ActionType.ISOLATE_HOST,
            action_params={"host_id": host_id},
            ai_reasoning=reason,
            confidence=confidence,
            threat_score=threat_score,
            affected_assets=[host_id],
        )

    def quarantine_file(
        self,
        file_path: str,
        host_id: str,
        confidence: float,
        threat_score: float,
        reason: str,
    ) -> DecisionResult:
        """
        Convenience method to quarantine file.

        Args:
            file_path: Path to file
            host_id: Host identifier
            confidence: AI confidence in decision
            threat_score: Threat severity score
            reason: Reason for quarantine

        Returns:
            DecisionResult
        """
        return self.evaluate_action(
            action_type=ActionType.QUARANTINE_FILE,
            action_params={"file_path": file_path, "host_id": host_id},
            ai_reasoning=reason,
            confidence=confidence,
            threat_score=threat_score,
            affected_assets=[host_id],
        )

    def kill_process(
        self, process_id: int, host_id: str, confidence: float, threat_score: float, reason: str
    ) -> DecisionResult:
        """
        Convenience method to kill process.

        Args:
            process_id: Process ID
            host_id: Host identifier
            confidence: AI confidence in decision
            threat_score: Threat severity score
            reason: Reason for killing process

        Returns:
            DecisionResult
        """
        return self.evaluate_action(
            action_type=ActionType.KILL_PROCESS,
            action_params={"process_id": process_id, "host_id": host_id},
            ai_reasoning=reason,
            confidence=confidence,
            threat_score=threat_score,
            affected_assets=[host_id],
        )
