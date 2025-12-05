"""Skill Learning Integration Mixin.

Provides skill learning integration methods for MaximusIntegrated.

FASE 6 integration: HSAS service for skill acquisition.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


class SkillLearningMixin:
    """Mixin providing skill learning integration methods."""

    async def execute_learned_skill(
        self,
        skill_name: str,
        context: dict[str, Any],
        mode: str = "hybrid",
    ) -> dict[str, Any]:
        """Execute a learned skill via HSAS service.

        Args:
            skill_name: Name of skill to execute
            context: Execution context (state, parameters)
            mode: Execution mode (model_free/model_based/hybrid)

        Returns:
            Execution result with success, reward, and neuromodulation updates

        Integration Points:
        - Dopamine: Skill reward -> RPE -> Learning rate modulation
        - Predictive Coding: Skill outcome vs prediction -> Free Energy
        - HCL: Skill execution affects system state
        """
        if not self.skill_learning_available:
            return {
                "available": False,
                "message": "Skill Learning requires HSAS service (port 8023)",
                "success": False,
            }

        try:
            result = await self.skill_learning.execute_skill(
                skill_name=skill_name, context=context, mode=mode
            )

            rpe = result.total_reward

            modulated_lr = self.neuromodulation.dopamine.modulate_learning_rate(
                base_learning_rate=0.01, rpe=rpe
            )

            if not result.success:
                self.neuromodulation.norepinephrine.process_error_signal(
                    error_magnitude=abs(rpe), requires_vigilance=True
                )

            if self.predictive_coding_available and "outcome" in context:
                prediction_error = abs(
                    result.total_reward - context.get("expected_reward", 0.0)
                )

                await self.process_prediction_error(
                    prediction_error=prediction_error, layer="l4"
                )

            return {
                "available": True,
                "skill_name": skill_name,
                "success": result.success,
                "steps_executed": result.steps_executed,
                "total_reward": result.total_reward,
                "execution_time": result.execution_time,
                "errors": result.errors,
                "neuromodulation": {
                    "rpe": rpe,
                    "modulated_learning_rate": modulated_lr,
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "available": True,
                "success": False,
                "error": str(e),
            }

    async def learn_skill_from_demonstration(
        self,
        skill_name: str,
        demonstration: list,
        expert_name: str = "human",
    ) -> dict[str, Any]:
        """Learn new skill from expert demonstration (imitation learning).

        Args:
            skill_name: Name for new skill
            demonstration: List of (state, action) pairs
            expert_name: Name of expert demonstrator

        Returns:
            Learning result

        Implements:
        - Imitation Learning via HSAS service
        - Dopamine boost for successful learning (intrinsic reward)
        - Memory consolidation of new skill
        """
        if not self.skill_learning_available:
            return {
                "available": False,
                "message": "Skill Learning requires HSAS service (port 8023)",
                "success": False,
            }

        try:
            success = await self.skill_learning.learn_from_demonstration(
                skill_name=skill_name,
                demonstration=demonstration,
                expert_name=expert_name,
            )

            if success:
                intrinsic_reward = 1.0
                self.neuromodulation.dopamine.modulate_learning_rate(
                    base_learning_rate=0.01, rpe=intrinsic_reward
                )

                await self.memory_system.store_memory(
                    memory_type="skill",
                    content=f"Learned skill: {skill_name} from {expert_name}",
                    metadata={
                        "skill_name": skill_name,
                        "expert": expert_name,
                        "demonstration_steps": len(demonstration),
                    },
                )

            return {
                "available": True,
                "success": success,
                "skill_name": skill_name,
                "expert": expert_name,
                "demonstration_steps": len(demonstration),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "available": True,
                "success": False,
                "error": str(e),
            }

    async def compose_skill_from_primitives(
        self,
        skill_name: str,
        primitive_sequence: list,
        description: str = "",
    ) -> dict[str, Any]:
        """Compose new skill from sequence of primitives.

        Args:
            skill_name: Name for composed skill
            primitive_sequence: List of primitive skill names
            description: Skill description

        Returns:
            Composition result

        Implements:
        - Hierarchical skill composition
        - Creativity bonus (serotonin for novel compositions)
        - Memory consolidation of composed skill
        """
        if not self.skill_learning_available:
            return {
                "available": False,
                "message": "Skill Learning requires HSAS service (port 8023)",
                "success": False,
            }

        try:
            success = await self.skill_learning.compose_skill(
                skill_name=skill_name,
                primitive_sequence=primitive_sequence,
                description=description,
            )

            creativity_score = 0.0
            if success:
                creativity_score = min(len(primitive_sequence) / 10.0, 1.0)
                self.neuromodulation.serotonin.process_system_stability(
                    stability_metrics={
                        "creativity": creativity_score,
                        "novel_composition": True,
                    }
                )

                await self.memory_system.store_memory(
                    memory_type="skill",
                    content=f"Composed skill: {skill_name}",
                    metadata={
                        "skill_name": skill_name,
                        "primitives": primitive_sequence,
                        "description": description,
                    },
                )

            return {
                "available": True,
                "success": success,
                "skill_name": skill_name,
                "primitives": primitive_sequence,
                "creativity_score": creativity_score,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "available": True,
                "success": False,
                "error": str(e),
            }

    def get_skill_learning_state(self) -> dict[str, Any]:
        """Get current Skill Learning system state.

        Returns:
            Dict with skill library, statistics, and HSAS service status
        """
        if not self.skill_learning_available:
            return {
                "available": False,
                "message": "Skill Learning requires HSAS service (port 8023)",
            }

        try:
            state = self.skill_learning.export_state()

            return {
                "available": True,
                "hsas_service_url": state["hsas_url"],
                "learned_skills_count": state["learned_skills_count"],
                "cached_skills": state["cached_skills"],
                "skill_statistics": state["skill_stats"],
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "available": True,
                "error": str(e),
            }
