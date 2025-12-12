# Episodic Memory Service

**Port:** 8102
**Database:** Qdrant (Vector DB)
**Status:** Production-Ready
**Updated:** 2025-12-12

Persistent memory storage for the NOESIS consciousness system. Implements a **4-tier Memory Fortress** architecture with semantic search capabilities.

---

## Architecture

```
episodic_memory/
├── api/
│   └── routes.py           # FastAPI endpoints
├── core/
│   ├── qdrant_client.py    # Vector database client
│   ├── entity_index.py     # Entity extraction & indexing
│   ├── memory_store.py     # Memory CRUD operations
│   ├── persistent_store.py # Disk persistence
│   ├── hierarchy.py        # 4-tier cache hierarchy
│   └── context_builder.py  # Context assembly for LLM
└── models/
    └── memory.py           # Memory data models
```

---

## Memory Types (MIRIX)

| Type | Purpose | Persistence | Priority |
|------|---------|-------------|----------|
| **CORE** | Identity, immutable facts | Permanent | 5 (highest) |
| **EPISODIC** | Specific events, experiences | Decayable | 10 |
| **SEMANTIC** | General knowledge, facts | Long-term | 8 |
| **PROCEDURAL** | Skills, how-to knowledge | Long-term | 5 |
| **RESOURCE** | External references | Medium-term | 3 |
| **VAULT** | High-confidence, consolidated | Permanent | 5 |

---

## 4-Tier Memory Fortress

```
┌─────────────────────────────────────────────────────────────┐
│  L1: HOT CACHE (In-Memory LRU)                             │
│  Latency: <1ms | Max: 1000 entries | TTL: 300s             │
│  Contents: CORE + VAULT (critical memories)                 │
├─────────────────────────────────────────────────────────────┤
│  L2: WARM STORAGE (Redis + AOF)                            │
│  Latency: <10ms | Persistence: AOF log                     │
│  Contents: Recent EPISODIC + SEMANTIC                      │
├─────────────────────────────────────────────────────────────┤
│  L3: COLD STORAGE (Qdrant via HTTP)                        │
│  Latency: <50ms | Semantic search enabled                  │
│  Contents: All memory types, vector embeddings             │
├─────────────────────────────────────────────────────────────┤
│  L4: VAULT BACKUP (JSON + Checksums)                       │
│  Sync: Every 5 min | Path: data/vault/                     │
│  Contents: Disaster recovery snapshots                     │
└─────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### Health

```
GET /health                         → Service health check
```

### Memory CRUD

```
POST   /v1/memories                 → Store new memory
GET    /v1/memories/{id}            → Get memory by ID
DELETE /v1/memories/{id}            → Delete memory
GET    /v1/memories/type/{type}     → Get memories by type
GET    /v1/memories/stats           → Memory statistics
```

### Search & Context

```
POST /v1/memories/search            → Semantic search (vector similarity)
POST /v1/memories/context           → Build LLM context from memories
```

### Maintenance

```
POST /v1/memories/consolidate       → Move old memories to VAULT
POST /v1/memories/decay             → Apply forgetting curve
POST /v1/memories/sync              → Sync with persistent storage
```

---

## Qdrant Configuration

```python
# Collection: maximus_episodic_memory
# Vector size: 1536 (OpenAI embeddings)
# Distance: Cosine similarity
# Quantization: int8 (99th percentile) → 3x memory reduction

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "maximus_episodic_memory"
VECTOR_SIZE = 1536
```

---

## Entity Index

Automatic entity extraction for fast retrieval:

```python
# Extracts:
# - Proper nouns (capitalized words)
# - Technical terms
# - Quoted strings
# - Keywords

# Creates inverted index:
# entity → [memory_id_1, memory_id_2, ...]

# Storage: data/entity_index.json
```

---

## Memory Decay (Forgetting Curve)

Implements Ebbinghaus forgetting curve:

```python
# Decay formula
retention = e^(-t/S)

# Where:
# t = time since last access
# S = memory strength (based on access count)

# Memories below threshold are candidates for:
# 1. Consolidation to VAULT (if high value)
# 2. Deletion (if low value)
```

---

## Quick Start

```bash
# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Run service
cd backend/services/episodic_memory
PYTHONPATH=src python -m uvicorn episodic_memory.main:app --port 8102

# Health check
curl http://localhost:8102/health

# Store memory
curl -X POST http://localhost:8102/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "content": "User prefers dark mode",
    "type": "SEMANTIC",
    "importance": 0.8
  }'

# Search
curl -X POST http://localhost:8102/v1/memories/search \
  -H "Content-Type: application/json" \
  -d '{"query": "user preferences", "limit": 5}'
```

---

## Configuration

```bash
# Environment Variables
EPISODIC_MEMORY_PORT=8102
QDRANT_URL=http://localhost:6333
EMBEDDING_MODEL=text-embedding-ada-002
DATA_DIR=./data
```

---

## Guarantees

| Metric | Target |
|--------|--------|
| L1 Latency | <1ms |
| L3 Latency | <50ms |
| Durability | 99.99% |
| Recovery Time | <30s |
| Checksum Pass | 100% |

---

## Integration with Consciousness

```
Consciousness Pipeline:
1. User input received
2. Context built from relevant memories
3. ESGT ignition with memory context
4. LLM generates response
5. New memories stored (insights, facts learned)
6. Memories consolidated periodically
```

---

## Related Documentation

- [Memory Fortress](../../../docs/MEMORY_FORTRESS.md)
- [Metacognitive Reflector](../metacognitive_reflector/README.md)
- [Consciousness System](../maximus_core_service/src/maximus_core_service/consciousness/README.md)
