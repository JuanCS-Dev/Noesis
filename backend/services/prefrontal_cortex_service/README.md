# Prefrontal Cortex Service

**Port:** 8005
**Status:** Production-Ready
**Version:** 2.0.0
**Updated:** 2025-12-12

The Prefrontal Cortex Service provides **executive functions** for NOESIS: decision-making, task prioritization, impulse inhibition, and emotional state monitoring.

---

## Architecture

```
prefrontal_cortex_service/
├── src/prefrontal_cortex_service/
│   ├── main.py                       # FastAPI app
│   ├── api/
│   │   └── routes.py                 # API endpoints
│   ├── core/
│   │   ├── decision_engine.py        # Decision making
│   │   └── task_prioritizer.py       # Task queue management
│   ├── emotional_state_monitor.py    # Emotion tracking
│   ├── impulse_inhibition.py         # Impulse control
│   ├── rational_decision_validator.py # Rationality checks
│   └── models/                       # Data models
```

---

## Core Components

| Component | Function |
|-----------|----------|
| **Decision Engine** | Evaluates options, makes rational decisions |
| **Task Prioritizer** | Manages task queue with priority ordering |
| **Emotional State Monitor** | Tracks current emotional state |
| **Impulse Inhibition** | Prevents impulsive/harmful actions |
| **Rational Decision Validator** | Validates decision rationality |

---

## API Endpoints

### Core Routes (prefix: /v1)

```
GET  /v1/health                → Service health check
POST /v1/decide                → Make decision based on context
POST /v1/tasks                 → Add task to queue
GET  /v1/tasks                 → Get prioritized task list
PATCH /v1/tasks/{task_id}      → Update task status
```

### Legacy Routes (api_legacy.py)

```
GET  /health                   → Health check
GET  /consciousness_events     → Recent consciousness events
POST /strategic_plan           → Generate strategic plan
POST /make_decision            → Make executive decision
GET  /emotional_state          → Current emotional state
GET  /impulse_inhibition_level → Impulse inhibition level
```

---

## Decision Engine

Makes decisions using multiple factors:

```python
class Decision:
    decision_id: str
    action: str
    confidence: float      # 0.0-1.0
    reasoning: str
    alternatives: List[str]
    risk_assessment: float
```

**Decision Process:**
1. Evaluate context and goals
2. Generate alternatives
3. Assess risks for each option
4. Apply impulse inhibition
5. Validate rationality
6. Return decision with confidence

---

## Task Prioritization

```python
class Task:
    task_id: str
    description: str
    priority: int          # 1-10 (10 = highest)
    status: str            # pending, in_progress, completed
    deadline: Optional[datetime]
    dependencies: List[str]
```

Tasks are automatically prioritized by:
- Urgency (deadline proximity)
- Importance (priority level)
- Dependencies (blocked tasks deprioritized)

---

## Quick Start

```bash
# Run service
cd backend/services/prefrontal_cortex_service
PYTHONPATH=src python -m uvicorn prefrontal_cortex_service.main:app --port 8005

# Health check
curl http://localhost:8005/v1/health

# Make decision
curl -X POST http://localhost:8005/v1/decide \
  -H "Content-Type: application/json" \
  -d '{
    "context": "User requesting potentially harmful action",
    "options": ["allow", "deny", "ask_clarification"],
    "constraints": {"safety": "high"}
  }'

# Add task
curl -X POST http://localhost:8005/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Review user feedback",
    "priority": 7
  }'

# Get tasks
curl http://localhost:8005/v1/tasks
```

---

## Integration with Consciousness

The Prefrontal Cortex integrates with the consciousness system:

```
Consciousness → Prefrontal Cortex → Decision → Action
                      ↓
              Impulse check
              Rationality validation
              Emotional consideration
```

---

## Related Documentation

- [Consciousness System](../maximus_core_service/src/maximus_core_service/consciousness/README.md)
- [Ethical Audit Service](../ethical_audit_service/README.md)
