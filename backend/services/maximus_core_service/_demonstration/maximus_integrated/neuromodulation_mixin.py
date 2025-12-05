"""Neuromodulation Integration Mixin.

Provides neuromodulation integration methods for MaximusIntegrated.

FASE 5 integration: Dopamine, Serotonin, Norepinephrine, Acetylcholine.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


class NeuromodulationMixin:
    """Mixin providing neuromodulation integration methods."""

    def get_neuromodulated_parameters(self) -> dict[str, Any]:
        """Get all neuromodulated parameters for adaptive behavior.

        Returns modulation values for:
        - Learning rate (Dopamine): for HCL/RL agent
        - Attention threshold (Acetylcholine): for AttentionSystem salience
        - Arousal gain (Norepinephrine): for threat response amplification
        - Exploration temperature (Serotonin): for ReasoningEngine
        """
        base_learning_rate = 0.01
        base_foveal_threshold = 0.6

        modulated_lr = self.neuromodulation.get_modulated_learning_rate(
            base_learning_rate
        )
        exploration_rate = self.neuromodulation.serotonin.get_exploration_rate()
        attention_gain = self.neuromodulation.norepinephrine.get_attention_gain()
        salience_threshold = self.neuromodulation.acetylcholine.get_salience_threshold()

        # Map exploration rate to temperature
        modulated_temperature = 0.3 + (exploration_rate / 0.3) * 0.7

        # Adjust attention threshold based on ACh salience threshold
        modulated_attention_threshold = 0.8 - (salience_threshold - 0.3) * (0.4 / 0.4)

        return {
            "learning_rate": modulated_lr,
            "attention_threshold": modulated_attention_threshold,
            "arousal_gain": attention_gain,
            "temperature": modulated_temperature,
            "raw_neuromodulation": {
                "dopamine_level": self.neuromodulation.dopamine.level,
                "serotonin_level": self.neuromodulation.serotonin.level,
                "norepinephrine_level": self.neuromodulation.norepinephrine.level,
                "acetylcholine_level": self.neuromodulation.acetylcholine.level,
                "exploration_rate": exploration_rate,
                "salience_threshold": salience_threshold,
            },
        }

    async def process_outcome(
        self,
        expected_reward: float,
        actual_reward: float,
        success: bool,
    ) -> dict[str, Any]:
        """Process task outcome through neuromodulation system.

        Updates dopamine (RPE) and serotonin (mood) based on results.

        Args:
            expected_reward: Expected reward/quality (0-1)
            actual_reward: Actual reward/quality (0-1)
            success: Whether the task succeeded

        Returns:
            Dict with RPE, motivation, and updated neuromodulation state
        """
        result = self.neuromodulation.process_reward(
            expected_reward=expected_reward,
            actual_reward=actual_reward,
            success=success,
        )

        updated_params = self.get_neuromodulated_parameters()
        result["updated_parameters"] = updated_params

        return result

    async def respond_to_threat(
        self,
        threat_severity: float,
        threat_type: str = "unknown",
    ) -> dict[str, Any]:
        """Respond to detected threats through neuromodulation.

        Activates norepinephrine system to increase arousal and attention.

        Args:
            threat_severity: Severity of threat (0-1)
            threat_type: Type of threat (e.g., 'intrusion', 'anomaly')

        Returns:
            Dict with arousal level and attention gain
        """
        self.neuromodulation.respond_to_threat(threat_severity)

        arousal_level = self.neuromodulation.norepinephrine.get_arousal_level()
        attention_gain = self.neuromodulation.norepinephrine.get_attention_gain()

        updated_params = self.get_neuromodulated_parameters()
        self.attention_system.salience_scorer.foveal_threshold = updated_params[
            "attention_threshold"
        ]

        return {
            "threat_severity": threat_severity,
            "threat_type": threat_type,
            "arousal_level": arousal_level,
            "attention_gain": attention_gain,
            "updated_attention_threshold": updated_params["attention_threshold"],
        }

    def get_neuromodulation_state(self) -> dict[str, Any]:
        """Get current neuromodulation state and global modulation parameters."""
        global_state = self.neuromodulation.get_global_state()
        modulated_params = self.get_neuromodulated_parameters()

        return {
            "global_state": {
                "dopamine": global_state.dopamine,
                "serotonin": global_state.serotonin,
                "norepinephrine": global_state.norepinephrine,
                "acetylcholine": global_state.acetylcholine,
                "overall_mood": global_state.overall_mood,
                "cognitive_load": global_state.cognitive_load,
            },
            "modulated_parameters": modulated_params,
            "timestamp": datetime.now().isoformat(),
        }
