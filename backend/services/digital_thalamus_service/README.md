# Digital Thalamus Service

**Port:** 8012
**Status:** Production-Ready
**Version:** 2.0.0
**Updated:** 2025-12-12

The Digital Thalamus acts as the **sensory gateway** for the NOESIS consciousness system, implementing Global Workspace Theory (GWT) for consciousness integration.

---

## Architecture

```
digital_thalamus_service/
├── src/digital_thalamus_service/
│   ├── thalamus_api.py       # FastAPI endpoints (main)
│   ├── attention_control.py  # Attention modulation
│   ├── global_workspace.py   # GWT broadcasting (Kafka + Redis)
│   ├── sensory_gating.py     # Input filtering
│   ├── signal_filtering.py   # Signal processing
│   ├── config.py             # Configuration
│   └── models/               # Data models
```

---

## Core Components

| Component | File | Function |
|-----------|------|----------|
| **Sensory Gating** | `sensory_gating.py` | Filters input based on relevance |
| **Signal Filtering** | `signal_filtering.py` | Normalizes raw signals |
| **Attention Control** | `attention_control.py` | Modulates processing priority |
| **Global Workspace** | `global_workspace.py` | Broadcasts to consciousness |

---

## API Endpoints

### Health & Status

```
GET /health                    → Service health check
GET /gating_status             → Current gating parameters
GET /attention_status          → Attention control state
GET /global_workspace_status   → GWT broadcasting status
```

### Sensory Processing

```
POST /ingest_sensory_data      → Submit sensory data for processing
```

**Request Body:**
```json
{
  "sensor_id": "visual_001",
  "sensor_type": "visual",
  "data": {"intensity": 0.8, "pattern": "threat"},
  "timestamp": "2025-12-12T10:30:00Z",
  "priority": 8
}
```

**Sensor Types:**
- `visual` - Visual input
- `auditory` - Audio signals
- `chemical` - Chemical sensors
- `somatosensory` - Touch/proprioception

---

## Global Workspace Integration

Implements GWT broadcasting via dual channels:

```
Raw Sensory Data → Gating → Filtering → Attention → Global Broadcast
                                                          ↓
                                              ┌───────────┴───────────┐
                                              ↓                       ↓
                                           Kafka              Redis (real-time)
                                    (system.consciousness)
```

High-salience events trigger ESGT ignition in the consciousness system.

---

## Configuration

```bash
# Environment Variables
KAFKA_BOOTSTRAP_SERVERS=kafka-immunity:9096
REDIS_URL=redis://redis:6379
```

---

## Quick Start

```bash
# Run service
cd backend/services/digital_thalamus_service
PYTHONPATH=src python -m uvicorn digital_thalamus_service.thalamus_api:app --port 8012

# Health check
curl http://localhost:8012/health

# Submit sensory data
curl -X POST http://localhost:8012/ingest_sensory_data \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "threat_detector",
    "sensor_type": "visual",
    "data": {"threat_level": 0.9},
    "priority": 9
  }'
```

---

## Related Documentation

- [Consciousness System](../maximus_core_service/src/maximus_core_service/consciousness/README.md)
- [ESGT Protocol](../maximus_core_service/src/maximus_core_service/consciousness/esgt/)
