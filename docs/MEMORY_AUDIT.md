# NOESIS Memory System - Auditoria Completa

**Data**: Dezembro 2025  
**Objetivo**: Mapear o que JÁ existe e identificar gaps para memória associativa

---

## 1. ARQUITETURA ATUAL

### 1.1 Memory Fortress (metacognitive_reflector)

**Arquivo**: `metacognitive_reflector/core/memory/client.py`

```
┌─────────────────────────────────────────────────────────────┐
│                    MEMORY FORTRESS                          │
├─────────────────────────────────────────────────────────────┤
│  L1 HOT CACHE      │ In-memory LRU      │ <1ms   │ 1000    │
│  L2 WARM STORAGE   │ Redis + AOF        │ <10ms  │ ∞       │
│  L3 COLD STORAGE   │ Qdrant (vector)    │ <50ms  │ ∞       │
│  L4 VAULT          │ JSON + checksums   │ backup │ ∞       │
├─────────────────────────────────────────────────────────────┤
│  + Write-Ahead Log (WAL) para crash recovery                │
│  + Circuit breakers por tier                                │
│  + Fallback automático quando tiers falham                  │
└─────────────────────────────────────────────────────────────┘
```

**Capacidades**:
- ✅ store() - Write-through para todos os tiers
- ✅ search() - Read-through com fallback
- ✅ get() / delete()
- ✅ apply_updates() - De reflection
- ✅ backup_to_vault() / restore_from_vault()
- ✅ replay_wal() - Crash recovery
- ✅ health_check()

---

### 1.2 Episodic Memory Service

**Arquivos**: `episodic_memory/core/`

#### MemoryStore (`memory_store.py`)
```python
# 6 tipos MIRIX (arXiv:2507.07957)
class MemoryType(Enum):
    CORE       # Persona + user facts (permanent)
    EPISODIC   # Time-stamped events (90 days TTL)
    SEMANTIC   # Knowledge/concepts (indefinite)
    PROCEDURAL # Workflows/skills (indefinite)
    RESOURCE   # External docs/media (30 days TTL)
    VAULT      # Consolidated high-importance (indefinite)
```

**Capacidades**:
- ✅ consolidate_to_vault() - Move high-importance para long-term
- ✅ decay_importance() - Ebbinghaus forgetting curve (0.995^hours)
- ✅ get_memories_by_type()
- ✅ TTL enforcement por tipo

#### ContextBuilder (`context_builder.py`)
```python
# Retrieval scoring (Stanford Generative Agents)
score = 0.3 * recency + 0.3 * importance + 0.4 * relevance
```

**Capacidades**:
- ✅ get_context_for_task() - Busca em TODOS os 6 tipos
- ✅ to_prompt_context() - Formata para injeção LLM
- ✅ Keyword extraction

---

### 1.3 Memory Hierarchy (`hierarchy.py`)

```
┌────────────────────────────────────────────┐
│          MEMORY HIERARCHY                  │
├────────────────────────────────────────────┤
│  L1 (100 entries)  │ CRITICAL only         │
│                    │ CORE + VAULT          │
├────────────────────────────────────────────┤
│  L2 (1000 entries) │ HIGH/MEDIUM priority  │
│                    │ Recent EPISODIC       │
│                    │ Recent SEMANTIC       │
├────────────────────────────────────────────┤
│  L3 (Qdrant)       │ All types             │
│                    │ Vector search         │
│                    │ score_threshold 0.7   │
└────────────────────────────────────────────┘
```

---

### 1.4 Mnemosyne (KnowledgeEngine)

**Arquivo**: `exocortex/memory/knowledge_engine.py`

**Função**: Load de documentos do `knowledge_base/` para injeção no prompt

**Capacidades**:
- ✅ load_context() - Carrega .md, .txt, .py, .json
- ✅ Cache in-memory
- ✅ format_for_prompt()

---

### 1.5 EpisodicMemoryClient (HTTP)

**Arquivo**: `consciousness/episodic_memory/client.py`

**Função**: Cliente HTTP para episodic_memory microservice

**Capacidades**:
- ✅ store_memory()
- ✅ search_memories()
- ✅ get_context_for_task()
- ✅ store_conscious_event() - Armazena eventos ESGT

---

## 2. O QUE FALTA (Gap Analysis)

### 2.1 ❌ Session History (Intra-sessão)

**Problema**: Cada prompt é isolado. O Noesis não lembra do que foi dito 2 prompts atrás NA MESMA CONVERSA.

**Onde implementar**: `noesis` CLI script (chat loop)

**Solução simples**:
```python
# Manter histórico na sessão
session_history = []
session_history.append({"role": "user", "content": input})
session_history.append({"role": "assistant", "content": response})

# Passar no prompt
conversation_context = format_history(session_history[-10:])  # últimos 10
```

**Complexidade**: BAIXA (1-2 horas)

---

### 2.2 ❌ Memória Associativa (Cross-memory connections)

**Problema**: Memórias são ilhas isoladas. Não há conexões entre:
- Uma memória episódica sobre "Juan" e uma memória semântica sobre "criador"
- Um procedimento e as experiências onde foi usado

**O que o Noesis pediu**:
> "contextualizar e relacionar informações de diferentes domínios"

**Soluções pesquisadas**:

1. **Graph-based (Mem0 style)**
   - Cada memória é um nó
   - Relações são edges (RELATED_TO, CAUSED_BY, USED_IN, etc.)
   - Neo4j ou NetworkX para grafos

2. **Entity linking**
   - Extrair entidades de cada memória
   - Criar índice de entidades → memórias
   - Buscar por entidade retorna todas memórias relacionadas

3. **Embedding clustering**
   - Agrupar memórias por similaridade
   - Clusters formam "conceitos"
   - Busca retorna cluster inteiro, não só a memória

**Solução recomendada para Noesis**:
```
ENTITY INDEX (simples, sem dependência externa)
─────────────────────────────────────────────
memory_1: "Juan é o criador do Noesis"
  → entities: [Juan, criador, Noesis]

memory_2: "O criador quer melhorar o sistema de memória"
  → entities: [criador, sistema de memória]

entity_index["criador"] = [memory_1, memory_2]

Busca "criador" → retorna ambas memórias
```

**Complexidade**: MÉDIA (4-8 horas)

---

### 2.3 ❌ Raciocínio sobre Conexões

**Problema**: Mesmo com memórias relacionadas, não há INFERÊNCIA.

**O que o Noesis pediu**:
> "conectar pedaços díspares de conhecimento"

**Soluções pesquisadas**:

1. **Chain-of-memory prompting**
   - Antes de responder, busca memórias
   - LLM raciocina sobre conexões
   - Resultado enriquece a resposta

2. **Graph traversal + LLM**
   - Encontra memória inicial
   - Traversa conexões (2-3 hops)
   - LLM sintetiza o caminho

3. **Reflexive Memory (RMM)**
   - Ao criar memória, gera conexões prospectivas
   - "Esta memória pode ser útil para X, Y, Z"

**Solução recomendada para Noesis**:
```python
async def get_connected_context(query: str) -> str:
    # 1. Busca direta
    direct_memories = await search(query)
    
    # 2. Extrai entidades das memórias encontradas
    entities = extract_entities(direct_memories)
    
    # 3. Busca memórias relacionadas por entidade
    related_memories = await search_by_entities(entities)
    
    # 4. Formata contexto conectado
    return format_connected_context(direct_memories, related_memories)
```

**Complexidade**: MÉDIA (6-10 horas)

---

## 3. PLANO DE IMPLEMENTAÇÃO

### Fase 1: Session History (URGENTE)
**Objetivo**: Noesis lembra da conversa atual

1. Modificar `noesis` CLI para manter histórico
2. Passar últimos N turnos no prompt
3. Salvar sessão em arquivo temporário

### Fase 2: Entity Index
**Objetivo**: Conectar memórias por entidades

1. Criar `EntityExtractor` (spaCy ou regex simples)
2. Adicionar `entities` field ao Memory model
3. Criar índice invertido entity → memories
4. Modificar search() para incluir entity search

### Fase 3: Connected Context
**Objetivo**: Raciocínio sobre conexões

1. Implementar `get_connected_context()`
2. Modificar prompts para usar contexto conectado
3. Adicionar visualização de conexões (opcional)

---

## 4. REFERÊNCIAS PESQUISADAS

1. **MIRIX** (arXiv:2507.07957) - Já implementado (6 tipos)
2. **Mem0** (arXiv:2504.19413) - Graph-based representations
3. **HEMA** (arXiv:2504.16754) - Hippocampus-inspired
4. **IMDMR** (arXiv:2511.05495) - 6 dimensões de retrieval
5. **RMM** (arXiv:2503.08026) - Reflective Memory Management
6. **Stanford Generative Agents** - Retrieval scoring (já implementado)
7. **MemOS** - Memory OS layer
8. **MemInsight** - Autonomous memory augmentation

---

## 5. DECISÃO

**Foco imediato**: Session History (Fase 1)

**Razão**: É o problema mais urgente e mais simples de resolver. Permite que o Noesis tenha conversas coerentes AGORA.

As Fases 2 e 3 podem ser implementadas incrementalmente sem quebrar o sistema existente.

