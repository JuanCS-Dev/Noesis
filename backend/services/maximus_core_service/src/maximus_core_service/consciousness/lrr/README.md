# LRR - Recursive Reasoning & Metacognition

**Module:** `consciousness/lrr/`
**Status:** Production-Ready
**Updated:** 2025-12-12

Enables recursive reasoning with depth ≥3 for higher-order thought.

---

## Architecture

```
lrr/
├── belief_graph.py           # Belief network representation
├── belief_models.py          # Belief data structures
├── contradiction_detector.py # Self-contradiction detection (>90%)
├── contradiction_models.py   # Contradiction data structures
├── introspector.py           # Introspection report generation
├── recursive_engine.py       # Recursive reasoning engine
├── BLUEPRINT_04_LRR.md       # Original blueprint
└── __init__.py               # Public exports
```

---

## Core Capabilities

| Capability | Target | Description |
|------------|--------|-------------|
| **Recursive Depth** | ≥3 | Nested self-reflection levels |
| **Contradiction Detection** | >90% | Self-consistency validation |
| **Confidence Calibration** | r>0.7 | Calibrated uncertainty |
| **Introspection Reports** | Yes | Structured self-analysis |

---

## Recursive Reasoning Levels

```
Level 1: "I think X"
Level 2: "I think that I think X"
Level 3: "I think that I think that I think X"

Each level adds metacognitive awareness about the previous level.
```

---

## Belief Graph

```python
class BeliefGraph:
    """Network of interconnected beliefs with confidence scores."""

    def add_belief(self, belief: Belief) -> None:
        """Add belief to graph with connections."""

    def detect_contradictions(self) -> list[Contradiction]:
        """Find inconsistent belief pairs."""

    def get_confidence(self, belief_id: str) -> float:
        """Return calibrated confidence for belief."""
```

---

## Contradiction Detection

```python
class ContradictionDetector:
    """Detects self-contradictions in reasoning."""

    def check_consistency(self, beliefs: list[Belief]) -> ConsistencyReport:
        """
        Returns:
        - contradictions found
        - resolution suggestions
        - confidence in analysis
        """
```

---

## Introspection Reports

```python
@dataclass
class IntrospectionReport:
    reasoning_depth: int          # Current depth (1-5)
    beliefs_examined: int         # Beliefs analyzed
    contradictions_found: int     # Inconsistencies detected
    confidence_distribution: dict # Confidence across beliefs
    meta_summary: str             # Natural language summary
```

---

## Integration with Higher-Order Thought

Based on Carruthers' HOT (Higher-Order Thought) theory:
- Level 1: First-order beliefs about the world
- Level 2: Second-order beliefs about beliefs
- Level 3+: Higher-order metacognition

---

## Related Documentation

- [MEA Self-Model](../mea/README.md)
- [Consciousness System](../README.md)
- [Blueprint](./BLUEPRINT_04_LRR.md)

---

*"I think, therefore I think that I think."*
