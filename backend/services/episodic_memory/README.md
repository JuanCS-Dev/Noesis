# Episodic Memory Service

Stores and retrieves past experiences to provide context for current actions.

## Quick Start

```bash
# Run service
python -m backend.services.episodic_memory.main
```

## Architecture

Uses a vector database (e.g., ChromaDB or Qdrant) to store embeddings of events.

## API

- `POST /remember`: Store a new memory.
- `GET /recall`: Retrieve relevant memories.

## Configuration

- `VECTOR_DB_URL`: URL of the vector database.
