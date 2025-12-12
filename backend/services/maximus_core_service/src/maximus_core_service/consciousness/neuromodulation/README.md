# Neuromodulation System

**Module:** `consciousness/neuromodulation/`
**Status:** Production-Ready
**Updated:** 2025-12-12

Four neurochemical modulators coordinated with conflict resolution and safety features.

---

## Architecture

```
neuromodulation/
├── coordinator_hardened.py     # NeuromodulationCoordinator
├── modulator_base.py           # NeuromodulatorBase abstract class
├── dopamine_hardened.py        # DopamineModulator
├── serotonin_hardened.py       # SerotoninModulator
├── acetylcholine_hardened.py   # AcetylcholineModulator
├── norepinephrine_hardened.py  # NorepinephrineModulator
└── __init__.py                 # Public exports
```

---

## The 4 Modulators

| Modulator | Neurotransmitter | Function | Effect |
|-----------|------------------|----------|--------|
| **Dopamine** | DA | Reward & Motivation | Learning rate, goal pursuit |
| **Serotonin** | 5-HT | Stability & Impulse Control | Emotional regulation |
| **Acetylcholine** | ACh | Attention & Learning | Focus intensity |
| **Norepinephrine** | NE | Arousal & Vigilance | Alertness, stress response |

---

## Biological Inspiration

```
Multiple neuromodulators interact NON-LINEARLY in biological brains:

Antagonistic: DA ↔ 5-HT (reward-seeking vs impulse control)
Synergistic:  ACh + NE   (attention + arousal = focused alertness)
Homeostatic:  System prevents dominance by single modulator
```

---

## Coordinator Configuration

```python
@dataclass
class CoordinatorConfig:
    # Antagonistic interactions (negative = opposition)
    da_5ht_antagonism: float = -0.3   # DA↑ suppresses 5HT effect

    # Synergistic interactions (positive = enhancement)
    ach_ne_synergy: float = 0.2       # ACh↑ + NE↑ = enhanced effect

    # Conflict resolution
    conflict_threshold: float = 0.7
    conflict_reduction_factor: float = 0.5

    # Safety limits
    max_simultaneous_modulations: int = 3
```

---

## Modulator Configuration

```python
@dataclass
class ModulatorConfig:
    baseline: float = 0.5              # Equilibrium point
    min_level: float = 0.0             # HARD floor
    max_level: float = 1.0             # HARD ceiling
    decay_rate: float = 0.01           # Reuptake: 1%/s
    smoothing_factor: float = 0.2      # Temporal smoothing
    desensitization_threshold: float = 0.8
    desensitization_factor: float = 0.5
    max_change_per_step: float = 0.1   # Max 10%/cycle
```

---

## Safety Features (CRITICAL)

1. **Bounded Levels [0, 1]** - HARD CLAMP, no exceptions
2. **Desensitization** - Diminishing returns above 0.8
3. **Homeostatic Decay** - Return to baseline over time
4. **Temporal Smoothing** - Prevents sudden changes
5. **Max Change Per Step** - Maximum 10% per cycle
6. **Circuit Breaker** - If ≥3 modulators fail → kill switch
7. **Conflict Detection** - Detects antagonistic patterns
8. **Conflict Resolution** - Reduces magnitude of conflicts

---

## Usage

```python
from consciousness.neuromodulation.coordinator_hardened import (
    NeuromodulationCoordinator,
    ModulationRequest
)

# Initialize coordinator
coordinator = NeuromodulationCoordinator()

# Request modulations
requests = [
    ModulationRequest(modulator="dopamine", delta=0.2, source="reward"),
    ModulationRequest(modulator="norepinephrine", delta=0.1, source="alertness"),
]

# Coordinate (applies conflict resolution)
result = await coordinator.coordinate(requests)

# Get current levels
levels = coordinator.get_all_levels()
print(f"DA: {levels['dopamine']:.2f}, 5-HT: {levels['serotonin']:.2f}")
```

---

## Conflict Detection

```python
# Example: DA↑ while 5-HT↑ (antagonistic)
requests = [
    ModulationRequest(modulator="dopamine", delta=+0.3, source="reward"),
    ModulationRequest(modulator="serotonin", delta=+0.3, source="calm"),
]

# Coordinator detects conflict (DA ↔ 5-HT antagonism)
# Reduces both deltas by conflict_reduction_factor (0.5)
# Result: DA +0.15, 5-HT +0.15
```

---

## Related Documentation

- [MCEA Arousal](../mcea/README.md)
- [Safety Protocol](../safety/README.md)
- [Consciousness System](../README.md)

---

*"Coordinate modulations across 4 neuromodulators with biological fidelity."*
