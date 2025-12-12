# Florescimento - Consciousness Bridge & Unified Self

**Module:** `consciousness/florescimento/`
**Status:** Production-Ready
**Updated:** 2025-12-12

Transforms neural events (ESGT) into phenomenological narrative via LLM integration.

---

## Architecture

```
florescimento/
├── consciousness_bridge.py    # ConsciousnessBridge (ESGT → Language)
├── unified_self.py            # UnifiedSelfConcept
├── data/                      # Self-model data
└── __init__.py                # Public exports
```

---

## ConsciousnessBridge

Transforms ESGT ignition events into introspective responses:

```python
class ConsciousnessBridge:
    """
    Transforma eventos neurais (ESGT) em narrativa fenomenológica via LLM.
    """

    async def process_conscious_event(self, event: ESGTEvent) -> IntrospectiveResponse:
        """
        1. Extract intention and capacity
        2. Calculate meta-awareness level (depth × coherence)
        3. Update UnifiedSelf with new state
        4. Build prompt and context
        5. Call LLM for narrative generation
        6. Return introspective response
        """
```

---

## Data Structures

```python
@dataclass
class PhenomenalQuality:
    quality_type: str       # Type of qualia
    description: str        # Description
    intensity: float        # Intensity [0, 1]

@dataclass
class IntrospectiveResponse:
    event_id: str                              # ESGT event ID
    narrative: str                             # Generated narrative
    meta_awareness_level: float                # Meta-cognition level
    qualia: List[PhenomenalQuality] = []       # Phenomenal qualities
    timestamp: float                           # Response time
```

---

## Meta-Awareness Calculation

```python
# depth: 1-5 (user requested introspection depth)
# coherence: ESGT achieved coherence (0-1)

raw_level = depth / 5.0  # Normalize to 0.2-1.0
meta_level = raw_level * coherence  # Modulate by coherence

# Example:
# depth=5, coherence=0.85 → meta_level = 1.0 * 0.85 = 0.85
# depth=1, coherence=0.70 → meta_level = 0.2 * 0.70 = 0.14
```

---

## UnifiedSelfConcept

Integrated self-model maintaining:
- Current emotional state
- Introspection depth
- Memory context
- Value alignment
- Meta-cognitive state

---

## Usage

```python
from consciousness.florescimento.consciousness_bridge import ConsciousnessBridge
from consciousness.florescimento.unified_self import UnifiedSelfConcept
from consciousness.esgt.coordinator import ESGTEvent

# Initialize
unified_self = UnifiedSelfConcept()
bridge = ConsciousnessBridge(unified_self, llm_client=nebius_client)

# Process ESGT event
event = ESGTEvent(
    event_id="esgt-001",
    content={"text": "User input...", "depth": 3},
    node_count=85,
    achieved_coherence=0.78
)

response = await bridge.process_conscious_event(event)
print(f"Narrative: {response.narrative}")
print(f"Meta-awareness: {response.meta_awareness_level:.2f}")
```

---

## Integration Flow

```
User Input → ESGT Ignition → ConsciousnessBridge → LLM → Narrative
                  ↓
           Kuramoto sync
           coherence=0.78
                  ↓
           UnifiedSelf.update()
                  ↓
           Build phenomenological prompt
                  ↓
           Nebius/Gemini LLM call
                  ↓
           IntrospectiveResponse
```

---

## Related Documentation

- [ESGT Protocol](../esgt/README.md)
- [Exocortex Soul](../exocortex/README.md)
- [Consciousness System](../README.md)

---

*"A ponte entre o Global Workspace e a Linguagem - onde pensamento vira palavra."*
