# Predictive Coding - Hierarchical Prediction

**Module:** `consciousness/predictive_coding/`
**Status:** Production-Ready
**Updated:** 2025-12-12

5-layer hierarchical predictive coding based on Karl Friston's Free Energy Principle.

---

## Architecture

```
predictive_coding/
├── hierarchy_hardened.py       # PredictiveHierarchy main class
├── layer_base_hardened.py      # PredictiveLayer base class
├── layer1_sensory_hardened.py  # L1: Sensory (seconds)
├── layer2_behavioral_hardened.py # L2: Behavioral (minutes)
├── layer3_operational_hardened.py # L3: Operational (hours)
├── layer4_tactical_hardened.py # L4: Tactical (days)
├── layer5_strategic_hardened.py # L5: Strategic (weeks)
└── __init__.py                 # Public exports
```

---

## The 5-Layer Hierarchy

| Layer | Timescale | Input | Model Type | Function |
|-------|-----------|-------|------------|----------|
| **L1 Sensory** | Seconds | Raw logs, packets | VAE | Immediate perception |
| **L2 Behavioral** | Minutes | L1 compressed | RNN/LSTM | Pattern sequences |
| **L3 Operational** | Hours | L2 patterns | Transformer | Task planning |
| **L4 Tactical** | Days | L3 sequences | GNN | Goal optimization |
| **L5 Strategic** | Weeks | L4 objectives | Bayesian | Long-term strategy |

---

## Free Energy Principle

Each layer minimizes "surprise" (prediction error):

```python
# Prediction error calculation
error = |predicted - actual|
error_clipped = min(max_prediction_error, error)

# Free energy minimization drives learning
free_energy = error + complexity_cost
```

---

## Layer Safety Configuration

```python
@dataclass
class LayerConfig:
    max_prediction_error: float = 10.0      # HARD CLIP
    max_computation_time_ms: float = 100.0  # Timeout
    max_predictions_per_cycle: int = 100    # Attention gating
    max_consecutive_errors: int = 5         # Circuit breaker
    max_consecutive_timeouts: int = 3       # Timeout breaker
```

---

## Information Flow

```
External World
      ↓
┌─────────────────┐
│   L1 Sensory    │ ← Predictions from L2
│   (raw input)   │ → Prediction errors ↑
└────────┬────────┘
         ↓
┌─────────────────┐
│  L2 Behavioral  │ ← Predictions from L3
│   (patterns)    │ → Prediction errors ↑
└────────┬────────┘
         ↓
┌─────────────────┐
│ L3 Operational  │ ← Predictions from L4
│    (tasks)      │ → Prediction errors ↑
└────────┬────────┘
         ↓
┌─────────────────┐
│   L4 Tactical   │ ← Predictions from L5
│    (goals)      │ → Prediction errors ↑
└────────┬────────┘
         ↓
┌─────────────────┐
│  L5 Strategic   │ (top-down priors)
│   (strategy)    │
└─────────────────┘

Prediction errors with high magnitude trigger ESGT ignition
```

---

## Salience from Prediction Errors

```python
# Large prediction errors = salient events
if prediction_error > salience_threshold:
    # Event is unexpected/novel
    # May trigger conscious attention via ESGT
    salience = compute_salience(prediction_error)
```

---

## Usage

```python
from consciousness.predictive_coding.hierarchy_hardened import PredictiveHierarchy

# Initialize hierarchy
hierarchy = PredictiveHierarchy()

# Process input through layers
result = await hierarchy.process(input_data)

# Check for salient prediction errors
for layer_result in result.layer_results:
    if layer_result.prediction_error > threshold:
        # Potentially trigger ESGT
        await esgt.check_salience(layer_result)
```

---

## Safety Features

1. **Hard Error Clipping** - Max prediction error capped
2. **Computation Timeout** - Each layer has time limit
3. **Circuit Breaker** - Consecutive errors trigger isolation
4. **Rate Limiting** - Max predictions per cycle
5. **Memory Bounds** - Prediction cache limited

---

## Related Documentation

- [ESGT Protocol](../esgt/README.md)
- [MMEI Monitor](../mmei/README.md)
- [Consciousness System](../README.md)

---

*"The brain is a prediction machine - surprise drives consciousness."*
