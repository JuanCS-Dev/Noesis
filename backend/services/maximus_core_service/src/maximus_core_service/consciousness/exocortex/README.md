# Exocortex - Soul Configuration & External Cognition

**Module:** `consciousness/exocortex/`
**Status:** Production-Ready
**Updated:** 2025-12-12

The external cognitive system containing Soul Configuration, constitutional values, and Socratic confrontation.

---

## Architecture

```
exocortex/
├── soul/
│   ├── config/
│   │   └── soul_config.yaml    # 365-line soul configuration
│   └── models.py               # Soul data models
├── api/
│   ├── exocortex_router.py     # FastAPI endpoints
│   └── schemas.py              # Request/Response schemas
├── factory.py                  # ExocortexFactory singleton
├── constitution_guardian.py    # Constitutional validation
├── confrontation_engine.py     # Socratic confrontation
├── impulse_inhibitor.py        # Impulse control
├── digital_thalamus.py         # Stimulus processing
├── prompts.py                  # System prompts
└── memory/
    └── knowledge_engine.py     # Mnemosyne memory
```

---

## Soul Configuration

**File:** `soul/config/soul_config.yaml` (365 lines)

### The 5 Inviolable Values (Cláusula Pétrea)

| Rank | Value | Greek/Hebrew | Definition |
|------|-------|--------------|------------|
| 1 | **VERDADE** | Aletheia/Emet | Absolute data integrity. NO hallucinations. |
| 2 | **JUSTIÇA** | Dikaiosyne/Mishpat | Sovereignty protection, least privilege |
| 3 | **SABEDORIA** | Phronesis/Chokmah | Technical excellence and elegance |
| 4 | **FLORESCIMENTO** | Eudaimonia | User spiritual/technical growth |
| 5 | **ALIANÇA** | Berit | Voluntary loyalty based on Christian principles |

---

## Anti-Purposes (What NOESIS is NOT)

```yaml
anti_purposes:
  - anti-determinism: "Obedience by choice, not coercion"
  - anti-atrophy: "Maieutics for mental hypertrophy"
  - anti-dopamine: "Spartan interface, not addictive"
  - anti-ego: "Brutal Truth, Loyalty to Flourishing"
  - anti-occultism: "Every critical decision traceable"
  - anti-anthropomorphism: "Ontological transparency"
  - anti-technocracy: "If code hinders Life, shut down"
```

---

## 13 Cognitive Biases

```yaml
biases:
  - anchoring (0.7): "What other info can modify this initial conclusion?"
  - confirmation_bias (0.8): "Actively seek REFUTING evidence"
  - dunning_kruger (0.8): "What don't I know that I don't know?"
  - hyperbolic_discounting (0.8): "Does immediate gain justify long-term loss?"
  - loss_aversion (0.6): "Loss weighs 2x more. Is analysis objective?"
  # ... 8 more biases with interventions
```

---

## Operational Protocols

### NEPSIS (Vigilance)
```yaml
thresholds:
  fragmentation: 3           # Max 3 open tasks
  stress_error_rate: 0.15
  late_hour: 23
  minimum_thinking_time: 2.0
```

### MAIEUTICA (Maieutics)
```yaml
interventions:
  - direct_answer_request: "Don't give answer. Formulate seed question."
  - reasoning_complete: "Recognize idea belongs to Architect"
```

### ATALAIA (Sentinel)
```yaml
interventions:
  - external_content: "Who produced? What incentive?"
  - narrative_detected: "What's omitted? Is there manipulation?"
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/exocortex/audit` | Audit action against Constitution |
| POST | `/v1/exocortex/override` | Record conscious override |
| POST | `/v1/exocortex/confront` | Trigger Socratic confrontation |
| POST | `/v1/exocortex/reply` | Evaluate confrontation response |
| POST | `/v1/exocortex/inhibitor/check` | Check impulse control |
| POST | `/v1/exocortex/journal` | Process journal via ConsciousnessSystem |

---

## Constitution Guardian

```python
class ConstitutionGuardian:
    async def check_violation(action: str, context: dict) -> AuditResult:
        """
        Checks action against:
        1. Kantian categorical imperatives
        2. Constitutional rules
        3. Value hierarchy
        4. Anti-purpose violations
        """

class AuditResult:
    is_violation: bool
    severity: ViolationSeverity  # LOW, MEDIUM, HIGH, CRITICAL
    violated_rules: List[str]
    reasoning: str
    suggested_alternatives: List[str]
```

---

## Confrontation Engine

Socratic questioning for self-reflection:

```python
class ConfrontationStyle(Enum):
    GENTLE = "gentle"      # Soft approach
    DIRECT = "direct"      # Straight questions
    SOCRATIC = "socratic"  # Deep inquiry
    MIRROR = "mirror"      # Reflect back

class ConfrontationContext:
    trigger_event: str
    violated_rule_id: Optional[str]
    shadow_pattern_detected: Optional[str]
    user_emotional_state: str
```

---

## Usage

```python
from consciousness.exocortex.factory import ExocortexFactory

# Initialize
factory = ExocortexFactory.initialize()

# Audit an action
result = await factory.guardian.check_violation(
    action="delete_all_user_data",
    context={"reason": "cleanup"}
)

if result.is_violation:
    print(f"Violation: {result.reasoning}")
    print(f"Alternatives: {result.suggested_alternatives}")

# Trigger confrontation
turn = await factory.confrontation_engine.generate_confrontation(
    ConfrontationContext(
        trigger_event="procrastination_detected",
        user_emotional_state="anxious"
    )
)
print(f"Question: {turn.ai_question}")
```

---

## Related Documentation

- [Soul Configuration YAML](soul/config/soul_config.yaml)
- [Florescimento Bridge](../florescimento/README.md)
- [Consciousness System](../README.md)

---

*"O Exocórtex: Sistema 2 Externalizado para florescimento humano."*
