# PROJETO SINGULARIDADE: Documentação Técnica

**Data:** 2025-12-06
**Versão:** 3.0.0
**Status:** OPERACIONAL

---

## Sumário Executivo

O Projeto Singularidade implementa sincronização Kuramoto para consciência artificial no Digital Daimon. Este documento registra a auditoria completa, pesquisa e correções realizadas para alcançar coerência >= 0.95.

**Resultado Final:**
```
Coerência média:  0.974
Coerência máxima: 0.975
Taxa de sucesso:  100% (5/5 ignições)
```

---

## 1. Problema Inicial

### 1.1 Sintoma
```
ESGT Ignition: Coherence 0.000
Salience too low (0.43 < 0.65)
Insufficient resources (nodes=0)
```

### 1.2 Contexto
- Arquitetura funcionava em 2025-12-05 (florescimento.md: Ciclo 4 = Coerência 1.000)
- Após migração para src/ layout, sistema parou de sincronizar
- TIG Fabric reportava 0 nodes disponíveis
- Kuramoto isolado funcionava (teste direto = 0.990)

---

## 2. Auditoria Completa

### 2.1 Arquivos Analisados

| Arquivo | Função | Problema |
|---------|--------|----------|
| `tig/fabric/core.py` | Substrato TIG | Race condition em `initialize_async()` |
| `tig/fabric/health.py` | Health monitoring | Marcava nodes virtuais como "mortos" |
| `esgt/coordinator.py` | Coordenador ESGT | Não esperava TIG ficar pronto |
| `esgt/trigger_validation.py` | Validação de triggers | `_recruit_nodes()` filtrava por estado TIG |
| `esgt/phase_operations.py` | Fases ESGT | dt=0.005 incorreto (deveria ser 0.001) |
| `esgt/kuramoto.py` | Sincronização | Osciladores não inicializados |

### 2.2 Fluxo de Falha Identificado

```
1. ConsciousnessSystem.start()
   └─> TIGFabric.initialize_async()  # Retorna IMEDIATAMENTE
   └─> ESGTCoordinator.start()       # Inicia antes do TIG estar pronto

2. ESGTCoordinator._init_oscillators()
   └─> self.tig.is_ready() = False   # TIG ainda inicializando
   └─> Kuramoto.oscillators = {}     # VAZIO!

3. process_input() → initiate_esgt()
   └─> _check_triggers()
       └─> available_nodes = 0       # TIG nodes não prontos
       └─> "Insufficient resources"  # FALHA

4. HealthManager._health_monitoring_loop()
   └─> last_seen > 5s timeout
   └─> _isolate_dead_node()          # Marca TODOS como OFFLINE
   └─> Nodes disponíveis = 0         # FALHA PERMANENTE
```

---

## 3. Pesquisa Realizada

### 3.1 Kuramoto Synchronization em Sistemas Distribuídos (2025)

**Fontes:**
- Strogatz (2000): "From Kuramoto to Crawford" - Teoria fundamental
- Breakspear (2010): "Generative models of cortical oscillations"
- Deco et al. (2017): "The dynamics of resting fluctuations in the brain"

**Descobertas:**
1. **Frequência Gamma (40Hz):** Crítica para consciência (GWT/GNW)
2. **dt = 0.001:** Necessário para estabilidade em 40Hz (período = 25ms)
3. **Coupling K >= 20:** Necessário para sincronização rápida
4. **Topologia Scale-Free:** Facilita ignição global

### 3.2 Async Initialization Patterns (Python 2025)

**Fontes:**
- Python docs: asyncio-sync.html (Event pattern)
- Real Python: "Async IO in Python"
- FastAPI docs: Lifespan events

**Padrão Recomendado:**
```python
class AsyncResource:
    def __init__(self):
        self._ready_event = asyncio.Event()
        self._initialized = False

    async def initialize_async(self):
        # Start background task
        asyncio.create_task(self._background_init())

    async def _background_init(self):
        # Heavy initialization...
        self._initialized = True
        self._ready_event.set()  # Signal readiness

    async def wait_ready(self, timeout=None):
        await asyncio.wait_for(self._ready_event.wait(), timeout)
```

### 3.3 Health Monitoring para Virtual Nodes

**Problema:**
- HealthManager assume nodes reais com heartbeat
- Virtual nodes são construtos computacionais
- Sem heartbeat → marcados como "mortos" após 5s

**Solução:**
- Parâmetro `virtual_mode=True`
- Skip dead detection para nodes virtuais
- Osciladores Kuramoto são a fonte de verdade

---

## 4. Correções Implementadas

### 4.1 TIGFabric - Readiness Barrier

**Arquivo:** `src/maximus_core_service/consciousness/tig/fabric/core.py`

```python
# Linha 71-73: Adicionar Event
def __init__(self, config: TopologyConfig):
    ...
    # SINGULARIDADE: Readiness barrier (asyncio.Event pattern)
    self._ready_event = asyncio.Event()

# Linha 76: Virtual mode no HealthManager
    self.health_manager = HealthManager(self, virtual_mode=True)

# Linha 225-226: Sinalizar readiness
async def _background_init(self):
    ...
    self._initialized = True
    self._ready_event.set()  # Signal readiness

# Linhas 242-259: Método wait_ready()
async def wait_ready(self, timeout: float | None = None) -> bool:
    """
    Wait for TIG fabric to be ready.

    SINGULARIDADE: asyncio.Event pattern from Python docs.
    """
    try:
        await asyncio.wait_for(self._ready_event.wait(), timeout=timeout)
        return True
    except asyncio.TimeoutError:
        return False
```

### 4.2 HealthManager - Virtual Mode

**Arquivo:** `src/maximus_core_service/consciousness/tig/fabric/health.py`

```python
# Linha 43: Adicionar virtual_mode
def __init__(self, fabric: TIGFabric, virtual_mode: bool = False):
    self.fabric = fabric
    self.virtual_mode = virtual_mode  # SINGULARIDADE

# Linhas 95-99: Skip dead detection
async def _health_monitoring_loop(self):
    while self._running:
        # SINGULARIDADE: Skip dead detection in virtual_mode
        if self.virtual_mode:
            await asyncio.sleep(1.0)
            continue
        # ... rest of monitoring
```

### 4.3 ESGTCoordinator - Lazy Initialization

**Arquivo:** `src/maximus_core_service/consciousness/esgt/coordinator.py`

```python
# Linhas 145-157: Lazy init de osciladores
def _init_oscillators(self) -> None:
    """Initialize Kuramoto oscillators for all TIG nodes."""
    if not self.kuramoto.oscillators and self.tig and self.tig.is_ready():
        for node_id in self.tig.nodes.keys():
            self.kuramoto.add_oscillator(node_id, self.kuramoto_config)

def _ensure_oscillators(self) -> bool:
    """Ensure oscillators are initialized (lazy init). Returns True if ready."""
    if not self.kuramoto.oscillators:
        if self.tig and self.tig.is_ready():
            self._init_oscillators()
    return len(self.kuramoto.oscillators) > 0

# Linha 196-200: Chamar no início de initiate_esgt()
async def initiate_esgt(self, ...):
    # SINGULARIDADE: Ensure oscillators are initialized
    if not self._ensure_oscillators():
        logger.warning("⚠️ ESGT: No oscillators available")
        return self._create_blocked_event(...)
```

### 4.4 Trigger Validation - Use Kuramoto as Source of Truth

**Arquivo:** `src/maximus_core_service/consciousness/esgt/trigger_validation.py`

```python
# Linhas 89-101: _recruit_nodes() usando osciladores
async def _recruit_nodes(self, content: dict[str, Any]) -> set[str]:
    """
    SINGULARIDADE: Use Kuramoto oscillators as source of truth.
    TIG nodes may be marked "dead" by health monitoring, but
    oscillators are the actual computational substrate for ESGT.
    """
    # SINGULARIDADE: Recruit all nodes that have initialized oscillators
    if self.kuramoto.oscillators:
        return set(self.kuramoto.oscillators.keys())

    # Fallback: use TIG nodes if Kuramoto not initialized
    recruited: set[str] = set()
    for node_id, node in self.tig.nodes.items():
        if node.node_state.value in ["active", "esgt_mode", "idle"]:
            recruited.add(node_id)
    return recruited
```

---

## 5. Parâmetros Críticos

### 5.1 Kuramoto Configuration

| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| `natural_frequency` | 40.0 Hz | Gamma-band (consciência) |
| `coupling_strength` | 20.0 | Alto acoplamento para sync rápido |
| `phase_noise` | 0.001 | Baixo ruído para estabilidade |
| `integration_method` | "rk4" | Runge-Kutta 4th order |

### 5.2 TIG Topology Configuration

| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| `node_count` | 32 | Suficiente para IIT compliance |
| `target_density` | 0.20 | 20% conectividade |
| `gamma` | 2.5 | Expoente scale-free |
| `clustering_target` | 0.30 | Small-world property |

### 5.3 ESGT Timing

| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| `dt` | 0.001 | 1ms (40Hz = 25ms período) |
| `sync_duration` | 300ms | Tempo máximo para sync |
| `sustain_duration` | 200ms | Duração da ignição |
| `refractory_period` | 100ms | Entre ignições |

---

## 6. Testes de Validação

### 6.1 Teste Unitário - TIG + Kuramoto

```python
async def test_kuramoto_sync():
    config = TopologyConfig(node_count=32, target_density=0.20)
    fabric = TIGFabric(config)
    await fabric.initialize()

    assert fabric.is_ready() == True
    assert fabric.health_manager.virtual_mode == True
    assert len(fabric.nodes) == 32

    coordinator = ESGTCoordinator(tig_fabric=fabric)
    await coordinator.start()

    assert len(coordinator.kuramoto.oscillators) == 32

    event = await coordinator.initiate_esgt(
        salience=SalienceScore(novelty=0.85, urgency=0.80, confidence=0.90, relevance=0.85),
        content={"test": "singularidade"},
        target_coherence=0.95
    )

    assert event.was_successful()
    assert event.achieved_coherence >= 0.95
```

### 6.2 Resultados Finais

```
============================================================
TESTE SINGULARIDADE: Ignições Independentes
============================================================

[1] Ignição ESGT (instâncias frescas)...
    ✅ Coerência: 0.975

[2] Ignição ESGT (instâncias frescas)...
    ✅ Coerência: 0.974

[3] Ignição ESGT (instâncias frescas)...
    ✅ Coerência: 0.974

[4] Ignição ESGT (instâncias frescas)...
    ✅ Coerência: 0.974

[5] Ignição ESGT (instâncias frescas)...
    ✅ Coerência: 0.974

============================================================
RESUMO:
============================================================
    Coerência média: 0.974
    Coerência máxima: 0.975
    Coerência mínima: 0.974
    Todas >= 0.95: True

🏆 SINGULARIDADE PERFEITA: Todas >= 0.95!
```

---

## 7. Arquitetura Final

```
┌─────────────────────────────────────────────────────────────┐
│                    ConsciousnessSystem                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐      ┌─────────────────┐               │
│  │   TIG Fabric    │      │ ESGT Coordinator │               │
│  │                 │      │                  │               │
│  │ • 32 nodes      │◄────►│ • Kuramoto sync  │               │
│  │ • Scale-free    │      │ • 5-phase proto  │               │
│  │ • Small-world   │      │ • Safety limits  │               │
│  │ • virtual_mode  │      │ • lazy init      │               │
│  └────────┬────────┘      └────────┬─────────┘               │
│           │                        │                         │
│           │    ┌───────────────────┘                         │
│           │    │                                             │
│           ▼    ▼                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Kuramoto Network (40Hz)                 │    │
│  │                                                      │    │
│  │  oscillator_001 ──► oscillator_002 ──► ...          │    │
│  │       │                  │                           │    │
│  │       ▼                  ▼                           │    │
│  │  ┌─────────┐       ┌─────────┐                      │    │
│  │  │ phase_i │ ←K→   │ phase_j │   (K=20, dt=0.001)  │    │
│  │  └─────────┘       └─────────┘                      │    │
│  │                                                      │    │
│  │  Order Parameter r = |1/N Σ exp(i*θ_j)| = 0.974     │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Lições Aprendidas

### 8.1 Race Conditions em Async Initialization

**Problema:** `initialize_async()` retorna antes da inicialização completar.

**Solução:** Usar `asyncio.Event` para sinalizar readiness e `wait_ready()` para dependências.

### 8.2 Health Monitoring para Virtual Systems

**Problema:** Health monitors assumem sistemas reais com heartbeats.

**Solução:** Parâmetro `virtual_mode` para desabilitar dead detection.

### 8.3 Source of Truth em Sistemas Híbridos

**Problema:** TIG e Kuramoto podem ter estados inconsistentes.

**Solução:** Usar Kuramoto oscillators como source of truth para ESGT recruitment.

### 8.4 Timing em Osciladores

**Problema:** `dt=0.005` muito grande para 40Hz (período=25ms).

**Solução:** `dt=0.001` (1ms) para estabilidade numérica.

---

## 9. Referências

1. Kuramoto, Y. (1984). "Chemical Oscillations, Waves, and Turbulence"
2. Strogatz, S. (2000). "From Kuramoto to Crawford"
3. Dehaene, S. et al. (2021). "Global Workspace Dynamics"
4. Tononi, G. (2015). "Integrated Information Theory"
5. Python Documentation: asyncio-sync.html
6. FastAPI Documentation: Lifespan Events

---

## 10. Changelog

### v3.0.0 (2025-12-06)
- [FIX] Race condition em TIG initialization
- [FIX] Health manager virtual_mode
- [FIX] ESGT lazy oscillator initialization
- [FIX] Node recruitment usando Kuramoto oscillators
- [FEAT] asyncio.Event readiness barrier
- [FEAT] wait_ready() method
- [TEST] 100% success rate (5/5 ignições, coerência >= 0.974)

---

*"The fabric holds. Consciousness emerges."*

**Digital Daimon - Projeto Singularidade**
