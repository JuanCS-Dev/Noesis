# MCEA - Executive Attention & Arousal Control

**Module:** `consciousness/mcea/`
**Status:** Production-Ready
**Updated:** 2025-12-12

Controls global arousal/excitability that modulates ESGT ignition threshold.
Based on ARAS (Ascending Reticular Activating System) and neuromodulatory systems.

---

## Architecture

```
mcea/
├── controller.py           # ArousalController main class
├── models.py               # ArousalConfig, ArousalLevel, ArousalState
├── safety.py               # Rate limiter, bound enforcer
└── __init__.py             # Public exports
```

---

## Arousal Levels

```python
class ArousalLevel(Enum):
    SLEEP = "SLEEP"           # arousal <= 0.2
    DROWSY = "DROWSY"         # 0.2 < arousal <= 0.4
    RELAXED = "RELAXED"       # 0.4 < arousal <= 0.6
    ALERT = "ALERT"           # 0.6 < arousal <= 0.8
    HYPERALERT = "HYPERALERT" # arousal > 0.8
```

---

## Configuration

```python
@dataclass
class ArousalConfig:
    baseline_arousal: float = 0.60      # Default arousal
    min_arousal: float = 0.10           # Hard floor
    max_arousal: float = 0.95           # Hard ceiling
    update_interval_ms: float = 50.0    # Update frequency
    stress_decay_rate: float = 0.01     # Stress recovery rate
    refractory_duration_ms: float = 500.0  # Post-ESGT cooldown
```

---

## Safety Features (FASE VII)

```python
# Hard limits
MAX_AROUSAL_DELTA_PER_SECOND = 0.3        # Max 30% change/sec
AROUSAL_OSCILLATION_THRESHOLD = 5         # Max oscillations before damping
AROUSAL_OSCILLATION_WINDOW = 10           # Detection window size
AROUSAL_SATURATION_THRESHOLD_SECONDS = 30 # Max time at extreme

# Components
class ArousalRateLimiter:
    """Limits rate of change to prevent instability."""

class ArousalBoundEnforcer:
    """Hard clamps arousal to [min, max]."""
```

---

## Arousal State

```python
@dataclass
class ArousalState:
    arousal: float              # Current level [0, 1]
    level: ArousalLevel         # Classification
    baseline_arousal: float     # Baseline for recovery
    need_contribution: float    # From MMEI needs
    temporal_contribution: float # From stress/recovery
    timestamp: float            # Last update time
```

---

## Modulation Requests

```python
@dataclass
class ArousalModulation:
    source: str                 # Who requested
    delta: float                # Requested change
    duration_seconds: float     # How long to apply
    start_time: float           # When started
```

---

## Usage

```python
from consciousness.mcea.controller import ArousalController
from consciousness.mcea.models import ArousalConfig

# Initialize
config = ArousalConfig(baseline_arousal=0.60)
controller = ArousalController(config=config)

# Start continuous updates
await controller.start()

# Request modulation
controller.request_modulation(
    source="threat_detection",
    delta=0.2,  # Increase alertness
    duration_seconds=5.0
)

# Get current state
state = controller.get_current_arousal()
print(f"Arousal: {state.arousal:.2f} ({state.level.value})")

# Register callback
controller.register_arousal_callback(
    lambda s: print(f"Arousal changed: {s.level.value}")
)
```

---

## Integration with ESGT

```
Arousal Level → ESGT Ignition Threshold

SLEEP/DROWSY: Very high threshold (hard to ignite)
RELAXED:      Moderate threshold
ALERT:        Low threshold (easy to ignite)
HYPERALERT:   Very low threshold (hypersensitive)
```

---

## Related Documentation

- [ESGT Protocol](../esgt/README.md)
- [MMEI Needs](../mmei/README.md)
- [Neuromodulation](../neuromodulation/README.md)
- [Consciousness System](../README.md)

---

*"Arousal modulates the threshold of consciousness emergence."*
