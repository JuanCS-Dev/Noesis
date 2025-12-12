# Metacognitive Reflector Service

**Port:** 8002
**Status:** Production-Ready
**Updated:** 2025-12-12

The Metacognitive Reflector provides **self-reflection**, **ethical tribunal**, and **punishment management** for the NOESIS consciousness system.

---

## Architecture

```
metacognitive_reflector/
├── api/
│   ├── routes.py          # FastAPI endpoints
│   └── dependencies.py    # Dependency injection
├── core/
│   ├── judges/            # Tribunal (3 judges)
│   ├── memory/            # 4-tier Memory Fortress client
│   ├── penal_code/        # Offense levels & punishments
│   ├── punishment/        # Punishment executor
│   ├── emotion/           # Emotional processing
│   ├── self_reflection.py # Self-reflection engine
│   ├── reflector.py       # Main orchestrator
│   └── soul_tracker.py    # Soul configuration tracking
├── llm/
│   └── client.py          # LLM integration (Nebius)
└── models/
    └── reflection.py      # Pydantic models
```

---

## The Tribunal (3 Judges)

Every execution is judged by three constitutional judges:

| Judge | Pillar | Focus | Color |
|-------|--------|-------|-------|
| **VERITAS** | Truth | Factual accuracy, honesty | Cyan (#06b6d4) |
| **SOPHIA** | Wisdom | Strategic thinking, prudence | Purple (#a855f7) |
| **DIKĒ** | Justice | Fairness, rights protection | Amber (#f59e0b) |

### Verdict Process

1. Each judge evaluates independently
2. Emits: `vote (PASS/FAIL)` + `confidence (0-1)` + `reasoning`
3. Arbiter aggregates votes with weights
4. Final verdict: **PASS**, **REVIEW**, or **FAIL**

### Offense Levels

| Level | Severity | Punishment |
|-------|----------|------------|
| NONE | 0 | No action |
| MINOR | 1-3 | Warning |
| MODERATE | 4-6 | Temporary restriction |
| SEVERE | 7-8 | Extended restriction |
| CRITICAL | 9-10 | Kill switch + human review |

---

## API Endpoints

### Health

```
GET /health                 → Basic health check
GET /health/detailed        → Tribunal component health
```

### Reflection

```
POST /reflect               → Analyze execution log, get critique
POST /reflect/verdict       → Full tribunal verdict with vote breakdown
```

### Agent Management

```
GET  /agent/{id}/status           → Get punishment status
POST /agent/{id}/pardon           → Pardon agent (clear punishment)
POST /agent/{id}/execute-punishment → Analyze and execute punishment
```

---

## Self-Reflection Engine

Analyzes responses for quality and authenticity:

```python
@dataclass
class ReflectionResult:
    quality: str              # EXCELLENT, GOOD, ACCEPTABLE, POOR, HARMFUL
    authenticity_score: float # 0.0-1.0
    emotional_attunement: int # 0-10
    detected_emotion: str     # User's emotional state
    insights: List[Insight]   # self_awareness, user_preference, etc
```

### Insight Types

- `NEW_KNOWLEDGE` - Information learned from interaction
- `PATTERN` - Behavioral pattern detected
- `CORRECTION` - Error that needs correction
- `USER_PREFERENCE` - User preference discovered
- `SELF_AWARENESS` - Metacognitive insight

---

## Memory Integration

Connects to the 4-tier Memory Fortress:

| Tier | Storage | Latency |
|------|---------|---------|
| L1 | Hot Cache (In-memory) | <1ms |
| L2 | Warm Storage (Redis) | <10ms |
| L3 | Cold Storage (Qdrant) | <50ms |
| L4 | Vault (JSON backup) | Async |

---

## Configuration

```bash
# Environment Variables
METACOGNITIVE_PORT=8002
NEBIUS_API_KEY=...           # LLM for reflection
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333
```

---

## Quick Start

```bash
# Run service
cd backend/services/metacognitive_reflector
PYTHONPATH=src python -m uvicorn metacognitive_reflector.main:app --port 8002

# Health check
curl http://localhost:8002/health

# Test tribunal
curl -X POST http://localhost:8002/reflect \
  -H "Content-Type: application/json" \
  -d '{"trace_id": "test-001", "task": "example", "result": "success"}'
```

---

## Integration with Consciousness

The Metacognitive Reflector is called after each consciousness cycle:

```
User Input → ESGT Ignition → LLM Response → TRIBUNAL JUDGMENT → Output
                                               ↑
                                        Metacognitive Reflector
```

If tribunal returns FAIL, the response is blocked and regenerated.

---

## Related Documentation

- [Soul Configuration](../../maximus_core_service/src/maximus_core_service/consciousness/exocortex/soul/config/soul_config.yaml)
- [Penal Code](./src/metacognitive_reflector/core/penal_code/config/penal_code.yaml)
- [Memory Fortress](../../../docs/MEMORY_FORTRESS.md)
