"""Core FL coordinator implementation."""

from __future__ import annotations

import logging
import random
from datetime import datetime
from typing import Any

import numpy as np

from ..aggregation import (
    AggregationResult,
    AggregationStrategy,
    DPAggregator,
    FedAvgAggregator,
    SecureAggregator,
)
from ..base import ClientInfo, FLMetrics, FLRound, FLStatus, ModelUpdate
from .models import CoordinatorConfig

logger = logging.getLogger(__name__)


class FLCoordinator:
    """Central coordinator for federated learning."""

    def __init__(self, config: CoordinatorConfig) -> None:
        """Initialize FL coordinator."""
        self.config = config
        self.fl_config = config.fl_config

        self.global_model_weights: dict[str, np.ndarray] | None = None
        self.current_round: FLRound | None = None
        self.round_history: list[FLRound] = []
        self.registered_clients: dict[str, ClientInfo] = {}
        self.metrics = FLMetrics()

        self.aggregator = self._create_aggregator()

        self.best_accuracy = 0.0
        self.rounds_without_improvement = 0

        logger.info(
            "FL Coordinator initialized with %s using %s",
            config.fl_config.model_type.value,
            config.fl_config.aggregation_strategy.value,
        )

    def _create_aggregator(self):
        """Create aggregator based on configuration."""
        strategy = self.fl_config.aggregation_strategy

        if strategy == AggregationStrategy.FEDAVG:
            return FedAvgAggregator()
        if strategy == AggregationStrategy.SECURE:
            return SecureAggregator(threshold=self.fl_config.min_clients)
        if strategy == AggregationStrategy.DP_FEDAVG:
            return DPAggregator(
                epsilon=self.fl_config.dp_epsilon,
                delta=self.fl_config.dp_delta,
                clip_norm=self.fl_config.dp_clip_norm,
            )
        raise ValueError(f"Unknown aggregation strategy: {strategy}")

    def register_client(self, client_info: ClientInfo) -> bool:
        """Register a new client."""
        if client_info.client_id in self.registered_clients:
            logger.warning("Client %s already registered, updating info", client_info.client_id)

        self.registered_clients[client_info.client_id] = client_info
        self.metrics.total_clients = len(self.registered_clients)
        self.metrics.active_clients = sum(1 for c in self.registered_clients.values() if c.active)

        logger.info(
            "Registered client %s (%s) with %s samples",
            client_info.client_id,
            client_info.organization,
            client_info.total_samples,
        )

        return True

    def unregister_client(self, client_id: str) -> bool:
        """Unregister a client."""
        if client_id not in self.registered_clients:
            logger.warning("Cannot unregister unknown client %s", client_id)
            return False

        del self.registered_clients[client_id]
        self.metrics.total_clients = len(self.registered_clients)
        self.metrics.active_clients = sum(1 for c in self.registered_clients.values() if c.active)

        logger.info("Unregistered client %s", client_id)
        return True

    def set_global_model(self, weights: dict[str, np.ndarray]) -> None:
        """Set the initial global model weights."""
        self.global_model_weights = weights
        logger.info("Set global model with %s parameters", sum(w.size for w in weights.values()))

    def get_global_model(self) -> dict[str, np.ndarray] | None:
        """Get current global model weights."""
        return self.global_model_weights

    def start_round(self) -> FLRound:
        """Start a new federated learning round."""
        if self.current_round and self.current_round.status in [
            FLStatus.WAITING_FOR_CLIENTS,
            FLStatus.TRAINING,
            FLStatus.AGGREGATING,
        ]:
            raise RuntimeError(
                f"Cannot start new round: current round {self.current_round.round_id} "
                f"is still {self.current_round.status.value}"
            )

        if self.global_model_weights is None:
            raise RuntimeError("Global model not initialized")

        active_clients = [client_id for client_id, info in self.registered_clients.items() if info.active]

        if len(active_clients) < self.fl_config.min_clients:
            raise RuntimeError(f"Not enough active clients: {len(active_clients)} < {self.fl_config.min_clients}")

        selected_clients = self._select_clients(active_clients)

        round_id = len(self.round_history) + 1
        self.current_round = FLRound(
            round_id=round_id,
            status=FLStatus.WAITING_FOR_CLIENTS,
            config=self.fl_config,
            selected_clients=selected_clients,
            global_model_version=self.fl_config.model_version,
        )

        logger.info("Started round %s with %s clients: %s", round_id, len(selected_clients), selected_clients)

        return self.current_round

    def _select_clients(self, active_clients: list[str]) -> list[str]:
        """Select clients for the current round."""
        num_to_select = min(
            int(len(active_clients) * self.fl_config.client_fraction),
            self.fl_config.max_clients,
        )
        num_to_select = max(num_to_select, self.fl_config.min_clients)
        selected = random.sample(active_clients, num_to_select)
        return selected

    def receive_update(self, update: ModelUpdate) -> bool:
        """Receive a model update from a client."""
        if self.current_round is None:
            raise RuntimeError("No round in progress")

        if self.current_round.status not in [FLStatus.WAITING_FOR_CLIENTS, FLStatus.TRAINING]:
            raise RuntimeError(
                f"Round {self.current_round.round_id} not accepting updates: {self.current_round.status.value}"
            )

        if update.client_id not in self.current_round.selected_clients:
            raise RuntimeError(f"Client {update.client_id} not selected for round {self.current_round.round_id}")

        if update.round_id != self.current_round.round_id:
            raise RuntimeError(f"Update round ID {update.round_id} != current round {self.current_round.round_id}")

        if any(u.client_id == update.client_id for u in self.current_round.received_updates):
            logger.warning("Duplicate update from client %s, replacing", update.client_id)
            self.current_round.received_updates = [
                u for u in self.current_round.received_updates if u.client_id != update.client_id
            ]

        self.current_round.received_updates.append(update)
        self.current_round.status = FLStatus.TRAINING

        logger.info(
            "Received update from %s (%s samples, %.1fs) - %s/%s received",
            update.client_id,
            update.num_samples,
            update.computation_time,
            len(self.current_round.received_updates),
            len(self.current_round.selected_clients),
        )

        if len(self.current_round.received_updates) >= self.fl_config.min_clients:
            logger.info("Minimum updates received (%s), ready to aggregate", self.fl_config.min_clients)

        return True

    def aggregate_updates(self) -> AggregationResult:
        """Aggregate received updates into global model."""
        if self.current_round is None:
            raise RuntimeError("No round in progress")

        if len(self.current_round.received_updates) < self.fl_config.min_clients:
            raise RuntimeError(
                f"Not enough updates: {len(self.current_round.received_updates)} < {self.fl_config.min_clients}"
            )

        self.current_round.status = FLStatus.AGGREGATING

        logger.info(
            "Aggregating %s updates for round %s",
            len(self.current_round.received_updates),
            self.current_round.round_id,
        )

        agg_result = self.aggregator.aggregate(self.current_round.received_updates)

        self.global_model_weights = agg_result.aggregated_weights
        self.fl_config.model_version += 1

        self.current_round.aggregation_result = agg_result.to_dict()
        self.current_round.metrics = agg_result.metadata.get("average_client_metrics", {})

        logger.info(
            "Aggregation complete: %s clients, %s samples, %.2fs",
            agg_result.num_clients,
            agg_result.total_samples,
            agg_result.aggregation_time,
        )

        return agg_result

    def complete_round(self) -> FLRound:
        """Complete the current round."""
        if self.current_round is None:
            raise RuntimeError("No round in progress")

        if self.current_round.aggregation_result is None:
            raise RuntimeError("Cannot complete round: aggregation not done")

        self.current_round.status = FLStatus.COMPLETED
        self.current_round.end_time = datetime.utcnow()

        self.round_history.append(self.current_round)
        self._update_metrics()

        completed_round = self.current_round
        self.current_round = None

        logger.info(
            "Round %s completed in %.1fs - participation: %.1f%%",
            completed_round.round_id,
            completed_round.get_duration_seconds(),
            completed_round.get_participation_rate() * 100,
        )

        return completed_round

    def _update_metrics(self) -> None:
        """Update coordinator metrics after round completion."""
        if not self.round_history:
            return

        self.metrics.total_rounds = len(self.round_history)

        participation_rates = [r.get_participation_rate() for r in self.round_history]
        self.metrics.average_participation_rate = np.mean(participation_rates)

        durations = [r.get_duration_seconds() for r in self.round_history if r.get_duration_seconds() is not None]
        if durations:
            self.metrics.average_round_duration = np.mean(durations)

        self.metrics.total_samples_trained = sum(r.get_total_samples() for r in self.round_history)
        self.metrics.last_updated = datetime.utcnow()

    def has_converged(self) -> bool:
        """Check if training has converged."""
        return self.metrics.convergence_status

    def should_stop(self) -> bool:
        """Check if training should stop."""
        if self.metrics.total_rounds >= self.config.max_rounds:
            logger.info("Max rounds (%s) reached", self.config.max_rounds)
            return True

        if self.has_converged():
            logger.info("Model has converged")
            return True

        return False

    def get_metrics(self) -> FLMetrics:
        """Get current FL metrics."""
        return self.metrics
