# ESGT - Global Workspace Ignition Protocol

**Module:** `consciousness/esgt/`
**Status:** Production-Ready
**Updated:** 2025-12-12

Implements **GWD (Global Workspace Dynamics)** consciousness emergence via 5-phase protocol.
Based on Dehaene et al. (2021) "Toward a computational theory of conscious processing."

---

## Architecture

```
esgt/
├── coordinator.py          # Main ESGTCoordinator class
├── kuramoto.py             # Kuramoto oscillator network
├── kuramoto_models.py      # Oscillator configuration
├── models.py               # SalienceScore, TriggerConditions, ESGTEvent
├── enums.py                # ESGTPhase, SalienceLevel enums
├── phase_operations.py     # 5-phase protocol implementation
├── trigger_validation.py   # Trigger condition validation
├── arousal_integration.py  # Arousal modulation integration
├── pfc_integration.py      # Prefrontal cortex integration
├── safety.py               # Frequency limiter
├── health_metrics.py       # Health metrics mixin
├── attention_helpers.py    # Attention computation helpers
└── spm/                    # Salience Priority Map
```

---

## The 5-Phase Protocol

```
┌─────────────────────────────────────────────────────────────┐
│                   ESGT IGNITION PROTOCOL                    │
└─────────────────────────────────────────────────────────────┘

1. PREPARE (0-100ms)
   ├─ Validate triggers (salience ≥ 0.65, resources, temporal gating)
   ├─ Recruit TIG nodes (content-based selection)
   └─ Initialize Kuramoto oscillators

2. SYNCHRONIZE (100-200ms)
   ├─ Start phase coupling
   ├─ Build topology (small-world network)
   ├─ Kuramoto.update() with coupling
   └─ Monitor coherence growth

3. BROADCAST (200-300ms)
   ├─ Reach target coherence (0.70+)
   ├─ Global workspace activation
   ├─ Bind information globally
   └─ Compute achieved_coherence = r(t)

4. SUSTAIN (300-400ms)
   ├─ Maintain synchronization
   ├─ Continue Kuramoto dynamics
   ├─ Record coherence_history
   └─ Monitor for anomalies

5. DISSOLVE (400-450ms)
   ├─ Graceful desynchronization
   ├─ Reduce coupling strength
   ├─ Reset oscillator phases
   └─ Prepare for next ignition
```

---

## Kuramoto Network

Phase synchronization via Kuramoto oscillators (gamma band ~40Hz):

```python
# Order Parameter (coherence)
r(t) = (1/N) |Σⱼ exp(iθⱼ)|

# Coherence Levels
r = 0.0  → Incoherence (random phases)
r ≥ 0.70 → Consciousness threshold
r = 1.0  → Perfect synchronization

# Configuration
@dataclass
class OscillatorConfig:
    natural_frequency: float = 40.0  # Hz (Gamma band)
    coupling_strength: float = 1.0   # K (Kuramoto coupling)
    phase_noise: float = 0.01        # Jitter
    dt: float = 0.001                # Integration timestep
```

---

## Trigger Conditions

```python
@dataclass
class TriggerConditions:
    min_salience: float = 0.60       # Minimum salience for ignition
    max_tig_latency_ms: float = 5.0  # Max TIG node latency
    min_available_nodes: int = 8     # Min nodes available
    min_cpu_capacity: float = 0.40   # Min CPU headroom
    refractory_period_ms: float = 200.0  # Cooldown between ignitions
    max_esgt_frequency_hz: float = 5.0   # Max ignition rate
    min_arousal_level: float = 0.40  # Minimum arousal for ignition
```

---

## Salience Score

Multi-factor salience computation:

```python
@dataclass
class SalienceScore:
    novelty: float = 0.0      # How unexpected (25%)
    relevance: float = 0.0    # Goal alignment (30%)
    urgency: float = 0.0      # Time criticality (30%)
    confidence: float = 1.0   # Prediction confidence (15%)

    def compute_total() -> float:
        return 0.25*novelty + 0.30*relevance + 0.30*urgency + 0.15*confidence
```

---

## Safety Limits (Hard)

```python
# ESGTCoordinator class constants
MAX_FREQUENCY_HZ = 10.0           # Max 10 ignitions/second
MAX_CONCURRENT_EVENTS = 3         # Max simultaneous events
MIN_COHERENCE_THRESHOLD = 0.50    # Min coherence for success
DEGRADED_MODE_THRESHOLD = 0.65    # Below this = degraded mode
```

---

## Usage

```python
from consciousness.esgt.coordinator import ESGTCoordinator, SalienceScore
from consciousness.tig.fabric import TIGFabric

# Initialize
tig = TIGFabric(TopologyConfig(node_count=100))
await tig.initialize()

esgt = ESGTCoordinator(tig_fabric=tig)
await esgt.start()

# Trigger ignition
salience = SalienceScore(novelty=0.8, relevance=0.9, urgency=0.7)
event = await esgt.initiate_esgt(salience, {"content": "important input"})

if event.success:
    print(f"Ignition successful! Coherence: {event.achieved_coherence:.3f}")
```

---

## Related Documentation

- [TIG Fabric](../tig/README.md)
- [MCEA Arousal](../mcea/README.md)
- [Safety Protocol](../safety/README.md)
- [Consciousness System](../README.md)

---

*"The moment of ignition - when distributed neural activity converges into unified conscious experience."*
