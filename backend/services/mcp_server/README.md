# MAXIMUS MCP Server

> **Model Context Protocol server for MAXIMUS 2.0**
>
> Version: 2.0.0 | Status: Sprint 2 (In Progress) | CODE_CONSTITUTION: 100%

---

## Overview

MCP Server exposes MAXIMUS backend services (Tribunal, Tool Factory, Episodic Memory) via **Model Context Protocol** following **elite patterns** from Anthropic (Dezembro 2025).

### Key Features

- ✅ **FastAPI + FastMCP**: Dual protocol (REST + MCP)
- ✅ **Streamable HTTP**: Production-ready transport (replaces SSE)
- ✅ **Stateless Design**: Horizontal scaling with load balancers
- ✅ **Circuit Breaker**: Resilience against cascading failures
- ✅ **Rate Limiting**: Token bucket per tool
- ✅ **Structured Logging**: JSON logs with trace IDs
- ✅ **Connection Pooling**: HTTP/2 with keep-alive
- ✅ **Retry Logic**: Exponential backoff for transient failures

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│              MAXIMUS MCP SERVER                  │
│           (FastAPI + FastMCP)                    │
├──────────────────────────────────────────────────┤
│  REST API          │  MCP Protocol               │
│  /health           │  /mcp (Streamable HTTP)     │
│  /metrics          │                             │
├──────────────────────────────────────────────────┤
│  MIDDLEWARE                                      │
│  • Structured Logger (JSON + trace IDs)         │
│  • Rate Limiter (token bucket per tool)         │
│  • Circuit Breaker (per service)                │
├──────────────────────────────────────────────────┤
│  MCP TOOLS                                       │
│  • tribunal_evaluate / health / stats           │
│  • factory_generate / execute / list / delete   │
│  • memory_store / search / consolidate / context│
├──────────────────────────────────────────────────┤
│  HTTP CLIENTS (pooling + retry)                 │
│  • TribunalClient → metacognitive_reflector     │
│  • FactoryClient → tool_factory_service         │
│  • MemoryClient → episodic_memory               │
└──────────────────────────────────────────────────┘
```

---

## Installation

### Requirements

- Python 3.12+
- Backend services running:
  - `metacognitive_reflector` (port 8101)
  - `episodic_memory` (port 8103)
  - `tool_factory_service` (port 8105)

### Setup

```bash
cd backend/services/mcp_server

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure (optional)
cp .env.example .env
# Edit .env with service URLs
```

### Configuration

All settings via environment variables (12-factor app):

```bash
# Service config
MCP_SERVICE_PORT=8106
MCP_LOG_LEVEL=INFO

# Downstream services
MCP_TRIBUNAL_URL=http://localhost:8101
MCP_FACTORY_URL=http://localhost:8105
MCP_MEMORY_URL=http://localhost:8103

# Rate limiting
MCP_RATE_LIMIT_PER_TOOL=100
MCP_RATE_LIMIT_WINDOW=60

# Circuit breaker
MCP_CIRCUIT_BREAKER_THRESHOLD=5
MCP_CIRCUIT_BREAKER_TIMEOUT=30.0
```

---

## Usage

### Run Server

```bash
# Development
PYTHONPATH=. python main.py

# Production
uvicorn main:app --host 0.0.0.0 --port 8106 --workers 4
```

### Health Check

```bash
curl http://localhost:8106/health
```

### Metrics

```bash
curl http://localhost:8106/metrics
```

---

## MCP Tools

### Tribunal Tools

#### `tribunal_evaluate`
Evaluate execution in Tribunal of Judges.

```python
verdict = await tribunal_evaluate(
    execution_log="task: foo\nresult: bar",
    context={"service": "factory"}
)
# Returns: decision, consensus_score, verdicts, punishment
```

#### `tribunal_health`
Get Tribunal health status.

### Factory Tools

#### `factory_generate`
Generate new tool dynamically.

```python
spec = await factory_generate(
    name="double",
    description="Double a number",
    examples=[{"input": {"x": 2}, "expected": 4}]
)
# Returns: ToolSpec with validated code
```

#### `factory_execute`
Execute registered tool.

#### `factory_list`
List all registered tools.

#### `factory_delete`
Remove tool from registry.

### Memory Tools

#### `memory_store`
Store memory in MIRIX 6-type system.

```python
memory = await memory_store(
    content="Task completed successfully",
    memory_type="experience",
    importance=0.9,
    tags=["success"]
)
```

#### `memory_search`
Semantic search across memories.

#### `memory_consolidate`
Move high-importance memories to vault.

#### `memory_context`
Get relevant context for a task.

---

## Development

### Run Tests

```bash
# All tests
PYTHONPATH=. pytest tests/ -v

# With coverage
PYTHONPATH=. pytest tests/ --cov=. --cov-report=term-missing

# Specific test
PYTHONPATH=. pytest tests/test_config.py -v
```

### Code Quality

```bash
# Type checking
mypy --strict .

# File size check
find . -name "*.py" -exec wc -l {} \; | awk '$1 > 500 {print "FAIL: " $2}'

# Placeholder check
grep -r "TODO\|FIXME" . --include="*.py"
```

---

## CODE_CONSTITUTION Compliance

| Rule | Status | Evidence |
|------|--------|----------|
| Files <500 lines | ✅ | All files validated |
| 100% type hints | ✅ | `from __future__ import annotations` |
| Google docstrings | ✅ | All modules documented |
| Zero placeholders | ✅ | No TODOs/FIXMEs |
| Test coverage ≥80% | ⏳ | Target for Sprint 2 |

---

## Performance

### Latency (Target)

| Operation | p50 | p95 | p99 |
|-----------|-----|-----|-----|
| tribunal_evaluate | <500ms | <1s | <2s |
| factory_generate | <5s | <8s | <10s |
| memory_search | <100ms | <200ms | <500ms |

### Throughput (Target)

- **100 req/s** per tool (configurable via rate limiter)
- **Horizontal scaling**: Stateless design supports N instances

---

## Troubleshooting

### Circuit Breaker Open

```bash
# Check breaker status
curl http://localhost:8106/metrics

# Reset manually (dev only)
# Call internal reset endpoint
```

### Rate Limit Exceeded

```bash
# Check remaining tokens
curl http://localhost:8106/metrics

# Increase limits via env vars
export MCP_RATE_LIMIT_PER_TOOL=200
```

---

## References

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [Streamable HTTP Transport](https://modelcontextprotocol.io/docs/concepts/transports#streamable-http)
- [CODE_CONSTITUTION](../../docs/pre-docs/CODE_CONSTITUTION.md)

---

**Built with scientific rigor | Governed by CODE_CONSTITUTION | Powered by MAXIMUS 2.0**
