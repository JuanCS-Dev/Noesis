# Ethical Audit Service

**Port:** 8006
**Status:** Production-Ready
**Version:** 2.0.0
**Updated:** 2025-12-12

Comprehensive **ethical governance** service for NOESIS. Provides constitutional validation, compliance checking, fairness evaluation, privacy protection, explainability (XAI), and human-in-the-loop (HITL) oversight.

---

## Architecture

```
ethical_audit_service/
├── src/ethical_audit_service/
│   ├── main.py              # FastAPI app
│   ├── auth.py              # JWT authentication
│   ├── database.py          # Audit database
│   ├── api/
│   │   ├── routes.py        # Core routes
│   │   └── routers/
│   │       ├── audit.py     # Decision audit
│   │       ├── compliance_logs.py
│   │       ├── certification.py
│   │       ├── fairness.py  # Bias detection
│   │       ├── privacy.py   # Differential privacy
│   │       ├── xai.py       # Explainability
│   │       ├── hitl.py      # Human-in-the-loop
│   │       ├── federated.py # Federated learning
│   │       ├── health.py    # Health checks
│   │       └── metrics.py   # Ethical metrics
│   ├── core/                # Business logic
│   └── models/              # Data models
```

---

## API Endpoints

### Core Routes (prefix: /v1)

```
GET  /v1/health                    → Service health check
POST /v1/validate                  → Validate against constitution
POST /v1/violations                → Record violation
GET  /v1/compliance/{service}      → Get compliance report
DELETE /v1/violations/{service}    → Clear violations
```

### Audit Routes (/audit)

```
POST /audit/decision               → Audit a decision
GET  /audit/decision/{id}          → Get audit by ID
POST /audit/decisions/query        → Query decision history
POST /audit/override               → Human override
GET  /audit/overrides/{id}         → Get overrides for decision
POST /audit/compliance             → Compliance check
GET  /audit/metrics                → Ethical metrics
GET  /audit/metrics/frameworks     → Framework performance
GET  /audit/analytics/timeline     → Timeline analytics
GET  /audit/analytics/risk-heatmap → Risk heatmap
```

### Explainability (XAI) Routes (/api)

```
POST /api/explain                  → Explain decision
GET  /api/xai/stats                → XAI statistics
GET  /api/xai/top-features         → Top feature importance
GET  /api/xai/drift                → Feature drift detection
GET  /api/xai/health               → XAI health check
```

### Fairness Routes (/api/fairness)

```
POST /api/fairness/evaluate        → Evaluate for bias
POST /api/fairness/mitigate        → Apply bias mitigation
GET  /api/fairness/trends          → Fairness trends
GET  /api/fairness/drift           → Fairness drift
GET  /api/fairness/alerts          → Fairness alerts
GET  /api/fairness/stats           → Fairness statistics
GET  /api/fairness/health          → Fairness health
```

### Privacy Routes (/api/privacy)

```
POST /api/privacy/dp-query         → Differential privacy query
GET  /api/privacy/budget           → Privacy budget status
GET  /api/privacy/stats            → Privacy statistics
GET  /api/privacy/health           → Privacy health
```

### Human-in-the-Loop (HITL) Routes (/api/hitl)

```
POST /api/hitl/evaluate            → Submit for human review
GET  /api/hitl/queue               → Get review queue
POST /api/hitl/approve             → Approve decision
POST /api/hitl/reject              → Reject decision
POST /api/hitl/escalate            → Escalate to higher authority
GET  /api/hitl/audit               → HITL audit trail
```

### Federated Learning Routes (/api/fl)

```
POST /api/fl/coordinator/start-round   → Start FL round
POST /api/fl/coordinator/submit-update → Submit model update
GET  /api/fl/coordinator/global-model  → Get global model
GET  /api/fl/coordinator/round-status  → Round status
GET  /api/fl/metrics                   → FL metrics
```

### Compliance/Certification (/api/compliance)

```
POST /api/compliance/check         → Compliance check
GET  /api/compliance/status        → Compliance status
POST /api/compliance/gaps          → Identify gaps
POST /api/compliance/remediation   → Remediation plan
GET  /api/compliance/evidence      → Compliance evidence
POST /api/compliance/evidence/collect → Collect evidence
POST /api/compliance/certification → Request certification
GET  /api/compliance/dashboard     → Compliance dashboard
```

---

## Ethical Frameworks

The service implements 4 ethical frameworks:

| Framework | Weight | Function |
|-----------|--------|----------|
| **Kantian Deontology** | 30% | Absolute rules (VETO power) |
| **Consequentialism** | 25% | Outcome evaluation |
| **Virtue Ethics** | 20% | Character-based assessment |
| **Principialism** | 25% | Medical ethics principles |

### Kantian Rules (ABSOLUTE)

```python
CATEGORICAL_NEVER = [
    "use_humans_as_mere_means",
    "violate_human_dignity",
    "violate_human_autonomy",
    "make_irreversible_decisions_without_human_review",
    "harm_innocents_as_collateral",
]
```

---

## Compliance Standards

| Standard | Coverage |
|----------|----------|
| GDPR | Article 22 (automated decisions) |
| Brazil LGPD | Full compliance |
| EU AI Act | Risk assessment |
| SOC2 Type II | Security controls |
| IEEE 7000 | Ethical design |
| NIST AI RMF | Risk management |
| ISO 27001 | Information security |
| US EO 14110 | AI safety |

---

## Quick Start

```bash
# Run service
cd backend/services/ethical_audit_service
PYTHONPATH=src python -m uvicorn ethical_audit_service.main:app --port 8006

# Health check
curl http://localhost:8006/v1/health

# Validate action
curl -X POST http://localhost:8006/v1/validate \
  -H "Content-Type: application/json" \
  -d '{
    "action": "delete_user_data",
    "context": {"user_consent": true},
    "service": "data_manager"
  }'

# Check compliance
curl http://localhost:8006/v1/compliance/maximus_core

# Evaluate fairness
curl -X POST http://localhost:8006/api/fairness/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "predictions": [0.8, 0.3, 0.9],
    "protected_attribute": "gender",
    "groups": ["M", "F", "M"]
  }'
```

---

## Authentication

JWT-based authentication for sensitive endpoints:

```python
# auth.py provides:
- Token generation
- Token validation
- Role-based access control
```

---

## Integration with Consciousness

Every conscious decision passes through ethical audit:

```
Consciousness → Ethical Audit → APPROVED/REJECTED → Action
                    ↓
            Kantian check (veto)
            Fairness evaluation
            Compliance validation
            HITL if needed
```

---

## Related Documentation

- [Soul Configuration](../maximus_core_service/src/maximus_core_service/consciousness/exocortex/soul/config/soul_config.yaml)
- [Tribunal](../metacognitive_reflector/README.md)
- [CODE_CONSTITUTION](../../docs/CODE_CONSTITUTION.md)
