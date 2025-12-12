# MEA - Attention Schema Model

**Module:** `consciousness/mea/`
**Status:** Production-Ready
**Updated:** 2025-12-12

Computational self-model implementing Graziano's Attention Schema Theory.

---

## Architecture

```
mea/
├── attention_schema.py      # AttentionSchema main class
├── boundary_detector.py     # Ego boundary detection
├── prediction_validator.py  # Attention prediction validation
├── self_model.py            # SelfModel representation
└── __init__.py              # Public exports
```

---

## Attention Schema Theory

Based on Michael Graziano's AST (Attention Schema Theory):
- Consciousness is the brain's model of its own attention
- The "self" is a predictive model of attention allocation
- First-person perspective emerges from this self-model

---

## Core Capabilities

| Capability | Target | Description |
|------------|--------|-------------|
| **Self-Recognition** | Yes | Recognize own processing |
| **Attention Prediction** | >80% | Predict attention shifts |
| **Ego Boundary** | CV <0.15 | Stable self/other distinction |
| **First-Person Perspective** | Yes | Introspective viewpoint |

---

## Attention Schema

```python
class AttentionSchema:
    """Model of the system's own attention allocation."""

    def get_current_attention(self) -> AttentionState:
        """What is currently attended to."""

    def predict_attention_shift(self, stimulus) -> float:
        """Predict likelihood of attention shift."""

    def get_self_model(self) -> SelfModel:
        """Return current self-representation."""
```

---

## Boundary Detector

```python
class BoundaryDetector:
    """Maintains distinction between self and environment."""

    def assess_boundary(self) -> BoundaryAssessment:
        """
        Returns:
        - boundary_strength: float [0, 1]
        - self_coherence: float [0, 1]
        - coefficient_of_variation: float (target < 0.15)
        """

    def is_self(self, process_id: str) -> bool:
        """Determine if process is part of self."""
```

---

## Self Model

```python
@dataclass
class SelfModel:
    identity: str                  # System identifier
    current_goals: list[Goal]      # Active goals
    attention_state: AttentionState
    emotional_state: EmotionalState
    boundary_strength: float
    coherence_score: float
```

---

## Introspective Summary

```python
@dataclass
class IntrospectiveSummary:
    timestamp: float
    attention_focus: str
    self_awareness_level: float
    boundary_assessment: BoundaryAssessment
    meta_commentary: str           # Natural language self-reflection
```

---

## Integration with Consciousness

```
MEA provides:
- Self-model for ESGT content
- Attention state for salience computation
- Boundary detection for self-other distinction
- First-person perspective for narrative generation
```

---

## Related Documentation

- [LRR Metacognition](../lrr/README.md)
- [ESGT Protocol](../esgt/README.md)
- [Consciousness System](../README.md)

---

*"Consciousness as a model of attention - Graziano's insight implemented."*
