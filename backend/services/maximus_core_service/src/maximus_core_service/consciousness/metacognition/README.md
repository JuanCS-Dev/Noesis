# Metacognition Monitor

**Module:** `consciousness/metacognition/`
**Status:** Production-Ready
**Updated:** 2025-12-12

Self-monitoring component for metacognitive awareness.

---

## Architecture

```
metacognition/
├── monitor.py               # MetacognitionMonitor main class
└── __init__.py              # Public exports
```

---

## Core Function

The Metacognition Monitor provides continuous self-observation:
- Monitors processing state
- Detects anomalies in reasoning
- Reports meta-level insights
- Feeds into consciousness narrative

---

## MetacognitionMonitor

```python
class MetacognitionMonitor:
    """Monitors and reports on internal cognitive processes."""

    def get_current_state(self) -> MetacognitiveState:
        """Return current metacognitive state."""

    def detect_cognitive_anomalies(self) -> list[Anomaly]:
        """Detect unusual patterns in processing."""

    def get_confidence_in_reasoning(self) -> float:
        """How confident is the system in its current reasoning."""

    def generate_meta_report(self) -> MetaReport:
        """Generate natural language meta-analysis."""
```

---

## Metacognitive State

```python
@dataclass
class MetacognitiveState:
    processing_load: float        # Current cognitive load
    confidence_level: float       # Overall confidence
    attention_coherence: float    # Attention stability
    reasoning_quality: float      # Self-assessed quality
    anomalies_detected: int       # Current anomaly count
```

---

## Integration

```
Metacognition Monitor feeds into:
- ConsciousnessBridge (narrative generation)
- ESGT (salience computation)
- Safety Protocol (anomaly detection)
```

---

## Related Documentation

- [LRR Recursive Reasoning](../lrr/README.md)
- [MEA Self-Model](../mea/README.md)
- [Consciousness System](../README.md)

---

*"Thinking about thinking - the essence of consciousness."*
