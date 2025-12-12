# Consciousness API

**Module:** `consciousness/api/`
**Status:** Production-Ready
**Updated:** 2025-12-12

FastAPI endpoints for consciousness system interaction.

---

## Architecture

```
api/
├── state_endpoints.py       # /state, /arousal, /metrics
├── esgt_endpoints.py        # /esgt/events, /esgt/trigger, /arousal/adjust
├── safety_endpoints.py      # /safety/status, /safety/violations, /emergency-shutdown
├── streaming.py             # /stream/sse, /stream/process, /ws
├── reactive_endpoints.py    # /reactive-fabric/*
├── helpers.py               # APIState, broadcast utilities
└── __init__.py              # Public exports
```

---

## Endpoint Groups

### State Endpoints (`/api/consciousness/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/state` | Complete consciousness state |
| GET | `/arousal` | Current arousal level |
| GET | `/metrics` | System metrics (TIG, ESGT) |

### ESGT Control (`/api/consciousness/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/esgt/events` | Recent ESGT events |
| POST | `/esgt/trigger` | Manual ESGT ignition |
| POST | `/arousal/adjust` | Adjust arousal level |

### Safety (`/api/consciousness/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/safety/status` | Safety protocol status |
| GET | `/safety/violations` | Recent violations |
| POST | `/safety/emergency-shutdown` | Kill switch (HITL) |

### Streaming (`/api/consciousness/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stream/sse` | Server-Sent Events stream |
| GET | `/stream/process` | **AURORA STREAMING** (main processing) |
| WS | `/ws` | WebSocket real-time updates |

### Reactive Fabric (`/api/consciousness/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reactive-fabric/metrics` | Fabric metrics |
| GET | `/reactive-fabric/events` | Recent events |
| GET | `/reactive-fabric/orchestration` | Orchestration status |

---

## AURORA STREAMING

The main consciousness processing endpoint:

```python
@router.get("/stream/process")
async def stream_process_input(
    content: str,    # User input
    depth: int = 3,  # Analysis depth (1-5)
) -> StreamingResponse:
    """
    Process input with real-time ESGT phase streaming.

    Events:
    - start: Processing initiated
    - phase: ESGT phase transition
    - coherence: Kuramoto coherence updates
    - token: Response tokens (word-by-word)
    - complete: Processing finished
    - error: Error occurred
    """
```

---

## Example Usage

```bash
# Get state
curl http://localhost:8001/api/consciousness/state

# Stream processing (AURORA)
curl "http://localhost:8001/api/consciousness/stream/process?content=Hello&depth=3"

# Trigger ESGT
curl -X POST http://localhost:8001/api/consciousness/esgt/trigger \
  -H "Content-Type: application/json" \
  -d '{"novelty": 0.8, "relevance": 0.9, "urgency": 0.7}'

# WebSocket
websocat ws://localhost:8001/api/consciousness/ws
```

---

## Related Documentation

- [Consciousness System](../README.md)
- [ESGT Protocol](../esgt/README.md)
- [Safety Protocol](../safety/README.md)

---

*"The interface to consciousness - REST, SSE, and WebSocket."*
