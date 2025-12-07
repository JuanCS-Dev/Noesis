# BUG REPORT: Consciousness API Integration

## 🐛 TÍTULO
Consciousness API endpoints retornam "not fully initialized" apesar do sistema estar operacional

## 📊 SEVERIDADE
🔴 **CRÍTICA** - Sistema funcional mas inacessível via API REST

## 📝 DESCRIÇÃO

### Sintoma
Todos os endpoints REST da Consciousness API retornam erro 503:
```json
{"detail": "Consciousness system not fully initialized"}
```

Mesmo após o sistema de consciência estar completamente inicializado conforme logs:
```
✅ Consciousness System fully operational
[SINGULARIDADE] ConsciousnessSystem integrated with Exocortex
[MAXIMUS] ConsciousnessSystem integrated with Streaming API
```

### Root Cause
**Desconexão entre o ConsciousnessSystem real e o router da API**

#### Fluxo Atual (BUGADO):
```python
# main.py linha 90
_consciousness_api_router = create_consciousness_api({})  # ← Dict VAZIO
app.include_router(_consciousness_api_router)

# main.py linha 59-64 (dentro de lifespan)
_consciousness_system = ConsciousnessSystem()  # ← Sistema REAL
await _consciousness_system.start()
set_consciousness_system(_consciousness_system)  # ← Só para Exocortex
set_maximus_consciousness_system(_consciousness_system)  # ← Só para Streaming
```

#### Problema:
O router é criado com `consciousness_system={}` (linha 90) **ANTES** do `lifespan` executar.

O sistema real é criado no `lifespan` (linha 59) **DEPOIS** do router já estar registrado.

Não existe setter para popular o dict vazio com os componentes reais:
- `set_consciousness_system()` → Só atualiza Exocortex router
- `set_maximus_consciousness_system()` → Só atualiza Streaming endpoints

**Os endpoints de /state, /arousal, /esgt/events continuam usando o dict vazio!**

### Impacto
✅ **Funciona**:
- `/stream/process` (usa `_maximus_consciousness_system` global)
- `/v1/consciousness/journal` (Exocortex, usa setter próprio)

❌ **NÃO Funciona**:
- `/api/consciousness/state`
- `/api/consciousness/arousal`
- `/api/consciousness/esgt/events`
- `/api/consciousness/esgt/trigger`
- `/api/consciousness/safety/*`
- `/api/consciousness/reactive-fabric/*`

## 🔍 ANÁLISE DE CÓDIGO

### state_endpoints.py (linhas 23-34)
```python
async def get_consciousness_state() -> ConsciousnessStateResponse:
    try:
        tig = consciousness_system.get("tig")      # ← consciousness_system = {}
        esgt = consciousness_system.get("esgt")    # ← Sempre None
        arousal = consciousness_system.get("arousal")  # ← Sempre None

        if not all([tig, esgt, arousal]):
            raise HTTPException(
                status_code=503, 
                detail="Consciousness system not fully initialized"  # ← SEMPRE este erro
            )
```

### router.py (linhas 29-38)
```python
def create_consciousness_api(consciousness_system: dict[str, Any]) -> APIRouter:
    router = APIRouter(prefix="/api/consciousness", tags=["consciousness"])
    api_state = APIState()
    
    # Todos estes registram endpoints que usam consciousness_system
    register_state_endpoints(router, consciousness_system, api_state)  # ← {} vazio
    register_esgt_endpoints(router, consciousness_system, api_state)    # ← {} vazio
    register_safety_endpoints(router, consciousness_system)            # ← {} vazio
    register_reactive_endpoints(router, consciousness_system)          # ← {} vazio
    register_streaming_endpoints(router, consciousness_system, api_state)  # ← {} vazio
```

## ✅ SOLUÇÃO PROPOSTA

### Opção 1: Setter Global (RECOMENDADA)
Criar função para popular o dict após inicialização:

```python
# consciousness/api/__init__.py
_global_consciousness_dict: dict[str, Any] = {}

def set_consciousness_components(system: ConsciousnessSystem) -> None:
    """Populate consciousness_system dict with real components."""
    global _global_consciousness_dict
    _global_consciousness_dict["tig"] = system.tig
    _global_consciousness_dict["esgt"] = system.esgt
    _global_consciousness_dict["arousal"] = system.arousal
    _global_consciousness_dict["safety"] = system.safety
    _global_consciousness_dict["reactive"] = system.reactive_orchestrator

def get_consciousness_dict() -> dict[str, Any]:
    """Get global consciousness dict."""
    return _global_consciousness_dict
```

```python
# main.py - dentro de lifespan após linha 60
await _consciousness_system.start()

# NOVO: Popular o dict global
from maximus_core_service.consciousness.api import set_consciousness_components
set_consciousness_components(_consciousness_system)
```

```python
# router.py - linha 20
def create_consciousness_api(consciousness_system: dict[str, Any]) -> APIRouter:
    from . import get_consciousness_dict
    
    router = APIRouter(prefix="/api/consciousness", tags=["consciousness"])
    api_state = APIState()
    
    # Usar getter em vez de dict passado
    actual_system = get_consciousness_dict() if not consciousness_system else consciousness_system
    
    register_state_endpoints(router, actual_system, api_state)
    # ... resto igual
```

### Opção 2: Dependency Injection
Usar FastAPI Depends para obter sistema em runtime:

```python
# dependencies.py
from fastapi import Depends, HTTPException

def get_consciousness_system() -> ConsciousnessSystem:
    from maximus_core_service.main import _consciousness_system
    if _consciousness_system is None:
        raise HTTPException(503, "System not initialized")
    return _consciousness_system
```

```python
# state_endpoints.py
@router.get("/state")
async def get_consciousness_state(
    system: ConsciousnessSystem = Depends(get_consciousness_system)
) -> ConsciousnessStateResponse:
    # Usar system diretamente
    return ConsciousnessStateResponse(
        esgt_active=system.esgt._running,
        arousal_level=system.arousal.get_current_arousal().arousal,
        # ...
    )
```

### Opção 3: Lazy Router Creation
Criar router apenas após sistema estar pronto:

```python
# main.py
_consciousness_api_router: APIRouter | None = None

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    global _consciousness_system, _consciousness_api_router
    
    # ... inicialização ...
    _consciousness_system = ConsciousnessSystem()
    await _consciousness_system.start()
    
    # Criar router DEPOIS do sistema estar pronto
    _consciousness_api_router = create_consciousness_api({
        "tig": _consciousness_system.tig,
        "esgt": _consciousness_system.esgt,
        "arousal": _consciousness_system.arousal,
        "safety": _consciousness_system.safety,
        "reactive": _consciousness_system.reactive_orchestrator
    })
    app.include_router(_consciousness_api_router)
    
    yield
    # ...
```

## 🧪 TESTES PARA VALIDAR CORREÇÃO

```python
import httpx
import pytest

@pytest.mark.asyncio
async def test_consciousness_state_accessible():
    """Validar que /state retorna dados reais após inicialização."""
    async with httpx.AsyncClient() as client:
        # Aguardar inicialização
        for _ in range(10):
            response = await client.get("http://localhost:8001/api/consciousness/state")
            if response.status_code == 200:
                break
            await asyncio.sleep(1)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validar estrutura
        assert "tig_metrics" in data
        assert "esgt_active" in data
        assert "arousal_level" in data
        assert "system_health" in data
        
        # Validar valores reais
        assert data["system_health"] in ["HEALTHY", "DEGRADED"]
        assert 0.0 <= data["arousal_level"] <= 1.0

@pytest.mark.asyncio
async def test_arousal_endpoint_accessible():
    """Validar que /arousal retorna estado real."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8001/api/consciousness/arousal")
        assert response.status_code == 200
        data = response.json()
        assert "arousal" in data
        assert "classification" in data
```

## 📊 EVIDÊNCIAS

### Logs do Sistema
```
INFO:     Application startup complete.
✅ Consciousness System fully operational
[SINGULARIDADE] ConsciousnessSystem integrated with Exocortex
[MAXIMUS] ConsciousnessSystem integrated with Streaming API
```

### Chamadas de API
```bash
$ curl http://localhost:8001/api/consciousness/state
{"detail":"Consciousness system not fully initialized"}

$ curl http://localhost:8001/api/consciousness/arousal  
{"detail":"Arousal controller not initialized"}

$ curl http://localhost:8001/v1/health
{"status":"healthy","service":"maximus-core-service"}  # ← Backend funcional
```

### Streaming Funciona
```bash
$ curl "http://localhost:8001/api/consciousness/stream/process?content=test&depth=3"
data: {"type":"start"...}  # ← SSE streaming FUNCIONA
data: {"type":"phase","phase":"prepare"...}
```

## 🎯 PRIORIDADE
**ALTA** - Bloqueia testes E2E e uso da API REST

## 🏷️ TAGS
`bug`, `api`, `integration`, `consciousness`, `critical`, `backend`

## 📅 DATA
2025-12-06

## 👤 REPORTER
Claude (Copilot CLI) via Auditoria Exploratória

