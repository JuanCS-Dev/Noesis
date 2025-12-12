# API Gateway Service

**Port:** 8000
**Status:** Production-Ready
**Updated:** 2025-12-12

Reverse proxy gateway that routes external requests to internal NOESIS microservices.

---

## Architecture

```
api_gateway/
├── src/api_gateway/
│   ├── core/
│   │   └── proxy.py        # Service routing logic
│   └── main.py             # FastAPI application
```

---

## Service Routing

### Local Development Mode

| Route | Service | Port |
|-------|---------|------|
| `/api/consciousness/*` | maximus_core_service | 8001 |
| `/api/memory/*` | episodic_memory | 8102 |
| `/api/reflect/*` | metacognitive_reflector | 8002 |
| `/api/ethics/*` | ethical_audit_service | 8006 |
| `/api/executive/*` | prefrontal_cortex_service | 8005 |

### Docker Mode

In Docker, services use internal DNS names on port 8000:

```python
services = {
    "maximus_core_service": "http://maximus_core:8000",
    "episodic_memory": "http://episodic_memory:8000",
    "metacognitive_reflector": "http://metacognitive_reflector:8000",
    "ethical_audit_service": "http://ethical_audit:8000",
    "prefrontal_cortex_service": "http://prefrontal_cortex:8000",
}
```

---

## Features

- **Request Forwarding**: Routes to appropriate backend service
- **Connection Pooling**: 20 keep-alive connections
- **Timeout Management**: 30s total, 10s connect
- **Error Handling**: 502 for upstream failures, 404 for unknown services

---

## API Endpoints

```
GET  /health                → Gateway health check
ANY  /api/{service}/*       → Forward to service
```

---

## Quick Start

```bash
# Run gateway
cd backend/services/api_gateway
PYTHONPATH=src python -m uvicorn api_gateway.main:app --port 8000

# Health check
curl http://localhost:8000/health

# Forward to consciousness
curl http://localhost:8000/api/consciousness/v1/health

# Forward to memory
curl http://localhost:8000/api/memory/v1/memories/stats
```

---

## Configuration

```bash
# Environment Variables
API_GATEWAY_PORT=8000
DOCKER_ENV=false           # Set to "true" in Docker

# Timeouts (in proxy.py)
REQUEST_TIMEOUT=30.0       # Total request timeout
CONNECT_TIMEOUT=10.0       # Connection timeout
MAX_KEEPALIVE=20           # Connection pool size
```

---

## Request Flow

```
Client Request
     │
     ▼
┌─────────────────┐
│  API Gateway    │  Port 8000
│  (FastAPI)      │
└────────┬────────┘
         │
    Route by path
         │
    ┌────┴────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│Maximus│ │Memory │ │Reflect│ │Ethics │
│ :8001 │ │ :8102 │ │ :8002 │ │ :8006 │
└───────┘ └───────┘ └───────┘ └───────┘
```

---

## Error Responses

| Code | Meaning |
|------|---------|
| 404 | Service not found in routing table |
| 502 | Upstream service unavailable |
| 500 | Internal gateway error |

---

## Related Documentation

- [Maximus Core](../maximus_core_service/src/maximus_core_service/consciousness/README.md)
- [Episodic Memory](../episodic_memory/README.md)
- [Metacognitive Reflector](../metacognitive_reflector/README.md)
