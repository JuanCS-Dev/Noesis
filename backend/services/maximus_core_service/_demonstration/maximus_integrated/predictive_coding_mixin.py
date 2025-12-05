"""Predictive Coding Integration Mixin.

Provides predictive coding integration methods for MaximusIntegrated.

FASE 3 integration: Hierarchical Predictive Coding Network.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


class PredictiveCodingMixin:
    """Mixin providing predictive coding integration methods."""

    def predict_with_hpc_network(
        self,
        raw_event: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perform hierarchical prediction using HPC Network.

        Implements Free Energy Minimization principle:
        - Layer 1 (Sensory): Compresses raw event (VAE)
        - Layer 2 (Behavioral): Predicts process patterns (GNN)
        - Layer 3 (Operational): Predicts threats (TCN)
        - Layer 4 (Tactical): Predicts campaigns (LSTM)
        - Layer 5 (Strategic): Predicts threat landscape (Transformer)

        Args:
            raw_event: Raw event vector (numpy array or tensor)
            context: Additional context (event graphs, sequences)

        Returns:
            Dict with predictions from all layers + free energy

        Note: Requires torch. Returns gracefully if not available.
        """
        if not self.predictive_coding_available:
            return {
                "available": False,
                "message": "Predictive Coding requires torch/torch_geometric",
                "predictions": None,
                "free_energy": None,
            }

        try:
            event_graph = context.get("event_graph") if context else None
            l2_sequence = context.get("l2_sequence") if context else None
            l3_sequence = context.get("l3_sequence") if context else None
            l4_sequence = context.get("l4_sequence") if context else None

            predictions = self.hpc_network.hierarchical_inference(
                raw_event=raw_event,
                event_graph=event_graph,
                l2_sequence=l2_sequence,
                l3_sequence=l3_sequence,
                l4_sequence=l4_sequence,
            )

            ground_truth = context.get("ground_truth") if context else None
            free_energy = self.hpc_network.compute_free_energy(
                predictions=predictions, ground_truth=ground_truth
            )

            return {
                "available": True,
                "predictions": predictions,
                "free_energy": free_energy,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "available": True,
                "error": str(e),
                "predictions": None,
                "free_energy": None,
            }

    async def process_prediction_error(
        self,
        prediction_error: float,
        layer: str = "l1",
    ) -> dict[str, Any]:
        """Process prediction error from Predictive Coding Network.

        Connects Free Energy Minimization with:
        - Neuromodulation: High prediction error -> dopamine RPE -> learning rate
        - Attention: Unexpected events -> salience increase
        - HCL: Prediction errors guide action selection

        Args:
            prediction_error: Free Energy value (0-1, higher = more surprise)
            layer: Which layer generated the error (l1-l5)

        Returns:
            Dict with updated system state
        """
        rpe = prediction_error

        modulated_lr = self.neuromodulation.dopamine.modulate_learning_rate(
            base_learning_rate=0.01, rpe=rpe
        )

        if prediction_error > 0.5:
            self.neuromodulation.acetylcholine.modulate_attention(
                importance=prediction_error
            )

            updated_params = self.get_neuromodulated_parameters()
            self.attention_system.salience_scorer.foveal_threshold = updated_params[
                "attention_threshold"
            ]

        return {
            "prediction_error": prediction_error,
            "layer": layer,
            "rpe_signal": rpe,
            "modulated_learning_rate": modulated_lr,
            "attention_updated": prediction_error > 0.5,
            "timestamp": datetime.now().isoformat(),
        }

    def get_predictive_coding_state(self) -> dict[str, Any]:
        """Get current Predictive Coding Network state.

        Returns:
            Dict with HPC network status and prediction buffers
        """
        if not self.predictive_coding_available:
            return {
                "available": False,
                "message": "Predictive Coding requires torch/torch_geometric",
            }

        try:
            prediction_errors = self.hpc_network.prediction_errors

            return {
                "available": True,
                "latent_dim": self.hpc_network.latent_dim,
                "device": self.hpc_network.device,
                "prediction_errors": {
                    "l1": len(prediction_errors.get("l1", [])),
                    "l2": len(prediction_errors.get("l2", [])),
                    "l3": len(prediction_errors.get("l3", [])),
                    "l4": len(prediction_errors.get("l4", [])),
                    "l5": len(prediction_errors.get("l5", [])),
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "available": True,
                "error": str(e),
            }
