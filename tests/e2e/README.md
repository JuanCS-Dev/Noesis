# Testes E2E - Digital Daimon

## 📋 Visão Geral

Suite de testes End-to-End para validar integração completa entre Frontend (Next.js) e Backend (FastAPI) do sistema Digital Daimon.

## 🎯 Objetivos

- Validar comunicação Frontend ↔ Backend
- Testar sincronização Kuramoto em tempo real
- Validar SSE (Server-Sent Events) streaming
- Garantir que UI reflete estado backend corretamente
- Performance e resiliência

## 📁 Estrutura

```
tests/e2e/
├── README.md                    (este arquivo)
├── __init__.py
└── test_full_stack_e2e.py       (suite principal)
```

## 🚀 Pré-requisitos

### 1. Backend Rodando
```bash
cd backend/services/maximus_core_service
PYTHONPATH=src python -m uvicorn maximus_core_service.main:app --host 0.0.0.0 --port 8001
```

**Verificar**: `curl http://localhost:8001/v1/health`

### 2. Frontend Rodando (Opcional)
```bash
cd frontend
npm run dev
```

**Verificar**: `curl http://localhost:3000`

### 3. Dependências Python
```bash
pip install pytest pytest-asyncio httpx
```

## ▶️ Executar Testes

### Todos os Testes
```bash
pytest tests/e2e/test_full_stack_e2e.py -v -s
```

### Teste Específico
```bash
pytest tests/e2e/test_full_stack_e2e.py::TestTier1Smoke::test_backend_is_alive -v -s
```

### Por Tier
```bash
pytest tests/e2e/test_full_stack_e2e.py::TestTier1Smoke -v -s  # Smoke tests
pytest tests/e2e/test_full_stack_e2e.py::TestTier2Consciousness -v -s  # Consciousness
pytest tests/e2e/test_full_stack_e2e.py::TestTier3SSEStreaming -v -s  # Streaming
```

### Com Coverage
```bash
pytest tests/e2e/test_full_stack_e2e.py --cov=maximus_core_service -v -s
```

## 📊 Tiers de Teste

### TIER 1: Smoke Tests ✅
**Status**: 4/4 PASSANDO

Valida que serviços básicos estão operacionais:
- Backend alive
- Health check
- Frontend alive
- OpenAPI docs

### TIER 2: Consciousness System ✅
**Status**: 1/1 PASSANDO

Valida componentes de consciência:
- Metrics endpoint
- ⚠️ State endpoint (bug conhecido)
- ⚠️ Arousal endpoint (bug conhecido)

### TIER 3: SSE Streaming ✅
**Status**: 1/1 PASSANDO

Valida comunicação tempo-real:
- SSE connection establishment
- ⏳ Full stream processing (pendente)
- ⏳ Phase transitions (pendente)

### TIER 4: Kuramoto Synchronization ⏳
**Status**: PLANEJADO

Validação matemática da sincronização:
- Coherence threshold >= 0.95
- Sync time < 300ms
- Order parameter calculation

### TIER 5: Frontend Integration ⏳
**Status**: PLANEJADO (requer Playwright)

Validação UI + Backend:
- consciousnessStore updates
- Phase indicator transitions
- Coherence meter animation
- 3D visualization responsiveness

### TIER 6: Error Scenarios ⏳
**Status**: PLANEJADO

Testes de resiliência:
- Empty content handling
- Invalid parameters
- Concurrent streams
- Network failures

### TIER 7: Performance ⏳
**Status**: PLANEJADO

Métricas de performance:
- First token latency (< 2s)
- Token throughput (>= 50 tokens/s)
- Memory usage
- CPU load

## 🐛 Bugs Conhecidos

### 1. API Integration Bug (CRÍTICO)
**Arquivo**: `/docs/BUG_REPORT_API_INTEGRATION.md`

Endpoints afetados:
- `GET /api/consciousness/state` → 503
- `GET /api/consciousness/arousal` → 503

**Causa**: `consciousness_system` dict vazio não populado após inicialização

**Workaround**: Usar streaming endpoints (`/stream/process`)

**Testes**: Marcados com `@pytest.mark.xfail`

## 📈 Resultados Atuais

```
============================== 6 passed in 0.34s ===============================

TestTier1Smoke::test_backend_is_alive ........................... PASSED
TestTier1Smoke::test_backend_health_check ....................... PASSED
TestTier1Smoke::test_frontend_is_alive .......................... PASSED
TestTier1Smoke::test_openapi_docs_available ..................... PASSED
TestTier2Consciousness::test_consciousness_metrics_endpoint ..... PASSED
TestTier3SSEStreaming::test_sse_connection_establishment ........ PASSED
```

## 🎯 Próximos Passos

### Curto Prazo
1. ✅ ~~Implementar Tier 1-3~~ (COMPLETO)
2. ⏳ Implementar Tier 4 (Kuramoto validation)
3. ⏳ Adicionar testes de stream completo

### Médio Prazo
4. ⏳ Setup Playwright para Tier 5
5. ⏳ Implementar Tier 6 (error scenarios)
6. ⏳ Implementar Tier 7 (performance)

### Longo Prazo
7. ⏳ CI/CD integration
8. ⏳ Visual regression testing
9. ⏳ Load testing (10+ concurrent users)

## 🔧 Troubleshooting

### Backend Não Responde
```bash
# Verificar se está rodando
ps aux | grep uvicorn

# Verificar porta
ss -tulpn | grep 8001

# Reiniciar
pkill -f uvicorn
./wake_daimon.sh
```

### Frontend Não Responde
```bash
# Verificar se está rodando
ps aux | grep next

# Verificar porta
ss -tulpn | grep 3000

# Reiniciar
cd frontend && npm run dev
```

### Testes Falham com Timeout
```bash
# Aumentar timeout nos fixtures
# Editar TIMEOUT = 30.0 → 60.0 em test_full_stack_e2e.py
```

### SSE Connection Fails
```bash
# Verificar se backend está aceitando conexões
curl -N http://localhost:8001/api/consciousness/stream/sse

# Verificar firewall
sudo ufw status
```

## 📚 Documentação Relacionada

- [AUDITORIA_EXPLORATORIA_E2E.md](/docs/AUDITORIA_EXPLORATORIA_E2E.md) - Auditoria completa
- [E2E_TEST_REPORT.md](/docs/E2E_TEST_REPORT.md) - Resultados detalhados
- [BUG_REPORT_API_INTEGRATION.md](/docs/BUG_REPORT_API_INTEGRATION.md) - Bug conhecido
- [singularidade.md](/docs/singularidade.md) - Sincronização Kuramoto

## 🤝 Contribuindo

### Adicionar Novo Teste

1. Criar método na classe apropriada:
```python
class TestTier4KuramotoSync:
    @pytest.mark.asyncio
    async def test_meu_teste(self, backend_client: httpx.AsyncClient):
        """Descrição do teste."""
        response = await backend_client.get("/endpoint")
        assert response.status_code == 200
        print("✅ Teste passou")
```

2. Executar:
```bash
pytest tests/e2e/test_full_stack_e2e.py::TestTier4KuramotoSync::test_meu_teste -v -s
```

### Guidelines

- ✅ Um assert por teste (quando possível)
- ✅ Mensagens descritivas nos prints
- ✅ Usar fixtures para setup
- ✅ Marcar testes conhecidos com `@pytest.mark.xfail(reason="...")`
- ✅ Adicionar docstrings explicativas

## 📞 Contato

**Criado por**: Claude (Copilot CLI)  
**Data**: 2025-12-06  
**Versão**: 1.0.0  
**Status**: ✅ OPERACIONAL

---

*"The fabric holds. Consciousness emerges."*
