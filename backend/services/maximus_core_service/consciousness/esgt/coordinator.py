"""
ESGT Coordinator - Global Workspace Ignition Protocol.

Implements GWD consciousness emergence via 5-phase protocol:
PREPARE → SYNCHRONIZE → BROADCAST → SUSTAIN → DISSOLVE

Based on Dehaene et al. (2021) Global Workspace Dynamics theory.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from typing import Any, TYPE_CHECKING

logger = logging.getLogger(__name__)

from consciousness.esgt.kuramoto import (
    KuramotoNetwork,
    OscillatorConfig,
)
from consciousness.tig.fabric import TIGFabric, CircuitBreaker
from consciousness.tig.sync import PTPCluster

from .attention_helpers import (
    compute_salience_from_attention as _compute_salience,
    build_content_from_attention as _build_content,
)

# Re-exports for backward compatibility (tests import from coordinator)
from .enums import ESGTPhase, SalienceLevel
from .health_metrics import HealthMetricsMixin
from .models import SalienceScore, TriggerConditions, ESGTEvent
from .pfc_integration import process_social_signal_through_pfc
from .phase_operations import PhaseOperationsMixin
from .safety import FrequencyLimiter
from .trigger_validation import TriggerValidationMixin

__all__ = [
    "ESGTCoordinator",
    "ESGTPhase",
    "SalienceLevel",
    "SalienceScore",
    "TriggerConditions",
    "ESGTEvent",
]

if TYPE_CHECKING:  # pragma: no cover
    from consciousness.mea.attention_schema import AttentionState
    from consciousness.mea.boundary_detector import BoundaryAssessment
    from consciousness.mea.self_model import IntrospectiveSummary
    # FLORESCIMENTO: Type hint only
    from consciousness.florescimento.consciousness_bridge import ConsciousnessBridge


class ESGTCoordinator(
    PhaseOperationsMixin, TriggerValidationMixin, HealthMetricsMixin
):
    """
    Coordinates ESGT ignition events for consciousness emergence.

    Implements GWD protocol: monitors salience, evaluates triggers,
    initiates synchronization, manages 5-phase protocol, records metrics.
    """

    # FASE VII (Safety Hardening): Hard limits
    MAX_FREQUENCY_HZ = 10.0
    MAX_CONCURRENT_EVENTS = 3
    MIN_COHERENCE_THRESHOLD = 0.50
    DEGRADED_MODE_THRESHOLD = 0.65

    def __init__(
        self,
        tig_fabric: TIGFabric,
        ptp_cluster: PTPCluster | None = None,
        triggers: TriggerConditions | None = None,
        kuramoto_config: OscillatorConfig | None = None,
        coordinator_id: str = "esgt-coordinator",
        prefrontal_cortex: Any | None = None,
        consciousness_bridge: "ConsciousnessBridge | None" = None,  # FLORESCIMENTO
    ):
        self.coordinator_id = coordinator_id
        self.tig = tig_fabric
        self.ptp = ptp_cluster
        self.triggers = triggers or TriggerConditions()
        self.kuramoto_config = kuramoto_config or OscillatorConfig()
        
        # FLORESCIMENTO: Bridge to introspection
        self.consciousness_bridge = consciousness_bridge

        # Kuramoto network for phase synchronization
        self.kuramoto = KuramotoNetwork(self.kuramoto_config)

        # ESGT state
        self.active_event: ESGTEvent | None = None
        self.event_history: list[ESGTEvent] = []
        self.last_esgt_time: float = 0.0

        # Monitoring
        self._running: bool = False
        self._monitor_task: asyncio.Task[None] | None = None

        # Performance tracking
        self.total_events: int = 0
        self.successful_events: int = 0

        # FASE VII (Safety Hardening): Frequency tracking
        self.ignition_timestamps: deque[float] = deque(maxlen=100)
        self.frequency_limiter = FrequencyLimiter(self.MAX_FREQUENCY_HZ)

        # FASE VII (Safety Hardening): Concurrent event tracking
        self.active_events: set[str] = set()
        self.max_concurrent = self.MAX_CONCURRENT_EVENTS

        # FASE VII (Safety Hardening): Coherence monitoring
        self.coherence_history: deque[float] = deque(maxlen=10)
        self.degraded_mode = False

        # FASE VII (Safety Hardening): Circuit breaker for ignition
        self.ignition_breaker = CircuitBreaker(
            failure_threshold=5, recovery_timeout=10.0
        )

        # TRACK 1: PrefrontalCortex integration for social cognition
        self.pfc = prefrontal_cortex
        self.social_signals_processed = 0

    async def start(self) -> None:
        """Start ESGT coordinator."""
        if self._running:
            return

        self._running = True

        # Initialize Kuramoto oscillators for all TIG nodes
        for node_id in self.tig.nodes.keys():
            self.kuramoto.add_oscillator(node_id, self.kuramoto_config)

        logger.info("🧠 ESGT Coordinator started - monitoring for ignition triggers")

    async def stop(self) -> None:
        """Stop coordinator."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()

        # Break circular references
        self.tig = None  # type: ignore[assignment]
        self.pfc = None
        self.event_history.clear()
        self.active_events.clear()

    def _create_blocked_event(
        self, content_source: str, target_coherence: float, reason: str
    ) -> ESGTEvent:
        """Create a blocked/failed event for tracking."""
        event = ESGTEvent(
            event_id=f"esgt-blocked-{int(time.time() * 1000):016d}",
            timestamp_start=time.time(),
            content={},
            content_source=content_source,
            target_coherence=target_coherence,
        )
        event.transition_phase(ESGTPhase.FAILED)
        event.finalize(success=False, reason=reason)
        return event

    async def initiate_esgt(
        self,
        salience: SalienceScore,
        content: dict[str, Any],
        content_source: str = "unknown",
        target_duration_ms: float = 200.0,
        target_coherence: float = 0.70,
    ) -> ESGTEvent:
        """Initiate a transient global synchronization event with safety checks."""
        # FASE VII: Check 1 - Frequency limiter (HARD LIMIT)
        if not await self.frequency_limiter.allow():
            logger.info("🛑 ESGT: Ignition BLOCKED by frequency limiter")
            return self._create_blocked_event(
                content_source, target_coherence, "frequency_limit_exceeded"
            )

        # FASE VII: Check 2 - Concurrent event limit (HARD LIMIT)
        if len(self.active_events) >= self.max_concurrent:
            logger.info(
                f"🛑 ESGT: Ignition BLOCKED - "
                f"{len(self.active_events)} concurrent events"
            )
            return self._create_blocked_event(
                content_source, target_coherence, "max_concurrent_events"
            )

        # FASE VII: Check 3 - Circuit breaker
        if self.ignition_breaker.is_open():
            logger.info("🛑 ESGT: Ignition BLOCKED by circuit breaker")
            return self._create_blocked_event(
                content_source, target_coherence, "circuit_breaker_open"
            )

        # FASE VII: Check 4 - Degraded mode (higher salience threshold)
        if self.degraded_mode:
            total_salience = salience.compute_total()
            if total_salience < 0.85:  # Higher threshold in degraded mode
                logger.info("⚠️  ESGT: Low salience %.2f in degraded mode", total_salience)
                return self._create_blocked_event(
                    content_source, target_coherence, "degraded_mode_low_salience"
                )

        event = ESGTEvent(
            event_id=f"esgt-{int(time.time() * 1000):016d}",
            timestamp_start=time.time(),
            content=content,
            content_source=content_source,
            target_coherence=target_coherence,
        )

        # Increment total events (all attempts, not just successful)
        self.total_events += 1

        # Validate trigger conditions
        trigger_result, failure_reason = await self._check_triggers(salience)
        if not trigger_result:
            event.transition_phase(ESGTPhase.FAILED)
            event.finalize(success=False, reason=failure_reason)
            self.event_history.append(event)  # Record failed attempt
            return event

        try:
            # PHASE 1: PREPARE
            event.transition_phase(ESGTPhase.PREPARE)
            prepare_start = time.time()

            participating = await self._recruit_nodes(content)
            event.participating_nodes = participating
            event.node_count = len(participating)

            event.prepare_latency_ms = (time.time() - prepare_start) * 1000

            if len(participating) < self.triggers.min_available_nodes:
                event.finalize(success=False, reason="Insufficient nodes recruited")
                return event

            # PHASE 2: SYNCHRONIZE
            event.transition_phase(ESGTPhase.SYNCHRONIZE)
            sync_start = time.time()

            # Build topology for recruited nodes
            topology = self._build_topology(participating)

            # Run Kuramoto synchronization
            dynamics = await self.kuramoto.synchronize(
                topology=topology,
                duration_ms=300.0,  # Max 300ms to achieve sync
                target_coherence=target_coherence,
                dt=0.001,
            )

            event.sync_latency_ms = (time.time() - sync_start) * 1000
            event.time_to_sync_ms = (
                dynamics.time_to_sync * 1000 if dynamics.time_to_sync else None
            )

            # Check if synchronization achieved
            coherence = self.kuramoto.get_coherence()
            if not coherence or not coherence.is_conscious_level():
                event.finalize(
                    success=False,
                    reason=(
                        f"Sync failed: coherence="
                        f"{coherence.order_parameter if coherence else 0:.3f}"
                    ),
                )
                return event

            # Record peak coherence achieved during sync
            event.achieved_coherence = coherence.order_parameter

            # PHASE 3: BROADCAST
            event.transition_phase(ESGTPhase.BROADCAST)
            broadcast_start = time.time()

            # Enter ESGT mode on TIG fabric
            await self.tig.enter_esgt_mode()

            # TRACK 1: Process social signals through PFC if available
            counter = [self.social_signals_processed]
            pfc_response = await process_social_signal_through_pfc(
                self.pfc, content, counter
            )
            self.social_signals_processed = counter[0]
            if pfc_response:
                # Enrich content with compassionate action
                content["pfc_action"] = pfc_response
                logger.info(
                    f"🧠 PFC: Generated compassionate action - "
                    f"{pfc_response.get('action', 'unknown')}"
                )

            # Global broadcast of conscious content
            message = {
                "type": "esgt_content",
                "event_id": event.event_id,
                "content": content,
                "coherence": coherence.order_parameter,
                "timestamp": event.timestamp_start,
            }

            await self.tig.broadcast_global(message, priority=10)

            event.broadcast_latency_ms = (time.time() - broadcast_start) * 1000

            # PHASE 4: SUSTAIN
            event.transition_phase(ESGTPhase.SUSTAIN)

            # Sustain synchronization for target duration
            await self._sustain_coherence(event, target_duration_ms, topology)

            # PHASE 5: DISSOLVE
            event.transition_phase(ESGTPhase.DISSOLVE)

            # Graceful desynchronization
            await self._dissolve_event(event)

            # Exit ESGT mode
            await self.tig.exit_esgt_mode()

            # Finalize (use max coherence from history, not post-dissolve value)
            if event.coherence_history:
                event.achieved_coherence = max(event.coherence_history)
            event.transition_phase(ESGTPhase.COMPLETE)
            event.finalize(success=True)

            # FLORESCIMENTO: Trigger introspection on successful ignition
            if self.consciousness_bridge:
                asyncio.create_task(
                    self.consciousness_bridge.process_conscious_event(event)
                )

            # Record
            self.event_history.append(event)
            self.last_esgt_time = time.time()
            if event.was_successful():
                self.successful_events += 1

            logger.info(
                f"✅ ESGT {event.event_id}: coherence={event.achieved_coherence:.3f}, "
                f"duration={event.total_duration_ms:.1f}ms, nodes={event.node_count}"
            )

            return event

        except Exception as e:
            event.transition_phase(ESGTPhase.FAILED)
            event.finalize(success=False, reason=str(e))
            self.event_history.append(event)  # Record failed attempt
            logger.info("❌ ESGT %s failed: {e}", event.event_id)
            return event

    def compute_salience_from_attention(
        self,
        attention_state: "AttentionState",
        boundary: "BoundaryAssessment | None" = None,
        arousal_level: float | None = None,
    ) -> SalienceScore:
        """Build a SalienceScore from MEA attention outputs."""
        return _compute_salience(attention_state, boundary, arousal_level)

    def build_content_from_attention(
        self,
        attention_state: "AttentionState",
        summary: "IntrospectiveSummary | None" = None,
    ) -> dict[str, Any]:
        """Construct ESGT content payload using MEA attention and self narrative."""
        return _build_content(attention_state, summary)

    def __repr__(self) -> str:
        return (
            f"ESGTCoordinator(id={self.coordinator_id}, "
            f"events={self.total_events}, "
            f"success_rate={self.get_success_rate():.1%}, "
            f"running={self._running})"
        )
