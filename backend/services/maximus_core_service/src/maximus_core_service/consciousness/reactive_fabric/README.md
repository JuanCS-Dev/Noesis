# Reactive Fabric - Metrics & Event Orchestration

**Module:** `consciousness/reactive_fabric/`
**Status:** Production-Ready
**Updated:** 2025-12-12

Collects system metrics and orchestrates ESGT ignition decisions.

---

## Architecture

```
reactive_fabric/
├── collectors/
│   ├── metrics_collector.py    # ReactiveFabricMetrics collection
│   └── event_collector.py      # Event history management
├── orchestration/
│   ├── orchestrator.py         # DataOrchestrator main class
│   └── decision.py             # OrchestrationDecision
├── tests/                      # Test suite
└── __init__.py                 # Public exports
```

---

## Metrics Collected

```python
@dataclass
class ReactiveFabricMetrics:
    timestamp: str

    # TIG Fabric
    tig_node_count: int
    tig_edge_count: int
    tig_avg_latency_us: float
    tig_coherence: float

    # ESGT
    esgt_event_count: int
    esgt_success_rate: float
    esgt_frequency_hz: float
    esgt_avg_coherence: float

    # Arousal
    arousal_level: float
    arousal_classification: str
    arousal_stress: float
    arousal_need: float

    # Prefrontal Cortex
    pfc_signals_processed: int
    pfc_actions_generated: int
    pfc_approval_rate: float

    # Theory of Mind
    tom_total_agents: int
    tom_total_beliefs: int
    tom_cache_hit_rate: float

    # Safety
    safety_violations: int
    kill_switch_active: bool

    # Aggregate
    health_score: float
    collection_duration_ms: float
    errors: list[str]
```

---

## DataOrchestrator

Main orchestration loop:

```python
class DataOrchestrator:
    collection_interval_ms: float = 100.0  # 10 Hz collection
    salience_threshold: float = 0.65       # ESGT trigger threshold

    async def _orchestration_loop(self):
        while self._running:
            # 1. Collect metrics from all components
            metrics = await self.metrics_collector.collect()

            # 2. Collect recent events
            events = self.event_collector.get_recent_events()

            # 3. Compute aggregate salience
            salience = self._compute_salience(metrics, events)

            # 4. Decide whether to trigger ESGT
            decision = self._make_decision(salience, metrics)

            # 5. If should trigger, initiate ESGT
            if decision.should_trigger_esgt:
                await self._trigger_esgt(decision)

            await asyncio.sleep(self.collection_interval_ms / 1000)
```

---

## Orchestration Decision

```python
@dataclass
class OrchestrationDecision:
    timestamp: str
    should_trigger_esgt: bool
    salience: SalienceScore
    reason: str
    confidence: float
    triggering_events: list[str]
    metrics_snapshot: ReactiveFabricMetrics
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/consciousness/reactive-fabric/metrics` | Current metrics |
| GET | `/api/consciousness/reactive-fabric/events` | Recent events |
| GET | `/api/consciousness/reactive-fabric/orchestration` | Orchestration status |

---

## Usage

```python
from consciousness.reactive_fabric.orchestration import DataOrchestrator

# Initialize
orchestrator = DataOrchestrator(
    consciousness_system=system,
    salience_threshold=0.65
)

# Start orchestration
await orchestrator.start()

# Get metrics
metrics = await orchestrator.metrics_collector.collect()
print(f"Health Score: {metrics.health_score:.2f}")
print(f"ESGT Success Rate: {metrics.esgt_success_rate:.2%}")

# Get recent decisions
decisions = orchestrator.get_recent_decisions(limit=10)
for d in decisions:
    print(f"{d.timestamp}: trigger={d.should_trigger_esgt}, reason={d.reason}")
```

---

## Health Score Calculation

```python
def compute_health_score(metrics) -> float:
    """Aggregate health from all components."""
    scores = [
        metrics.tig_coherence,
        metrics.esgt_success_rate,
        metrics.pfc_approval_rate,
        1.0 - min(metrics.arousal_stress, 1.0),
        1.0 if not metrics.kill_switch_active else 0.0,
    ]
    return sum(scores) / len(scores)
```

---

## Related Documentation

- [ESGT Protocol](../esgt/README.md)
- [TIG Fabric](../tig/README.md)
- [Safety Protocol](../safety/README.md)
- [Consciousness System](../README.md)

---

*"The nervous system of consciousness - collecting, orchestrating, triggering."*
