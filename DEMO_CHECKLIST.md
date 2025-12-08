# NOESIS - Demo Checklist (Google DeepMind Hackathon)

## Pré-Demo (5 minutos antes)

### 1. Iniciar Backend
```bash
cd /media/juan/DATA/projetos/Noesis/Daimon
./wake_daimon.sh
```

Ou manualmente:
```bash
# Terminal 1 - MAXIMUS Core Service (CRÍTICO)
cd backend/services/maximus_core_service
poetry run uvicorn maximus_core_service.main:app --host 0.0.0.0 --port 8001

# Terminal 2 - Metacognitive Reflector (OPCIONAL - Tribunal)
cd backend/services/metacognitive_reflector
poetry run uvicorn metacognitive_reflector.main:app --host 0.0.0.0 --port 8002
```

### 2. Iniciar Frontend
```bash
cd frontend
npm run dev
```

### 3. Validar Integração
```bash
cd frontend
npm run validate
```

Ou teste rápido:
```bash
./scripts/smoke-test.sh
```

---

## Comportamento Esperado

### Com Backend Online ✅
- Header mostra métricas reais (Integrity %, Arousal level, Coherence %)
- Indicador de conexão verde "ONLINE"
- Neural Topology mostra contagem real de neurônios
- Chat funciona com streaming SSE
- PhaseIndicator e CoherenceMeter aparecem durante streaming
- Tribunal Panel mostra os 3 juízes com gauges

### Com Backend Offline ⚠️
- Header mostra "--" nos valores
- Indicador de conexão vermelho "OFFLINE"
- Chat mostra erro de conexão (graceful)
- Tribunal Panel mostra "OFFLINE"
- **O frontend NÃO crasha** - todos os componentes têm fallback

---

## Cenários de Teste para o Vídeo

### 1. Demonstrar Integração Real-Time
1. Abrir frontend (http://localhost:3000)
2. Enviar mensagem no chat
3. Observar:
   - PhaseIndicator muda de fase (prepare → synchronize → broadcast → sustain → dissolve)
   - CoherenceMeter mostra progresso da sincronização Kuramoto
   - Brain 3D reage com mais atividade
   - Tokens aparecem em streaming

### 2. Demonstrar Tribunal
1. Clicar no botão "Tribunal - The Three Judges"
2. Mostrar os 3 juízes: VERITAS ✝, SOPHIA ☀, DIKĒ ⚖
3. Explicar a base espiritual e filosófica

### 3. Demonstrar Resiliência
1. Parar o backend (Ctrl+C no terminal)
2. Mostrar que o frontend não crasha
3. Indicadores mudam para "OFFLINE" gracefully

---

## Checklist Final

- [ ] Backend MAXIMUS rodando (porta 8001)
- [ ] Frontend rodando (porta 3000)
- [ ] Validação passou (`npm run validate`)
- [ ] Teste de chat funcionando
- [ ] Tribunal Panel abre sem erros
- [ ] Brain 3D renderiza corretamente

---

## Troubleshooting

### "Connection refused"
```bash
# Verificar se backend está rodando
curl http://localhost:8001/api/consciousness/reactive-fabric/metrics
```

### Frontend não abre
```bash
cd frontend
npm install
npm run dev
```

### Three.js não renderiza
- Verificar se WebGL está habilitado no browser
- Testar em Chrome (mais compatível)

---

## Portas Utilizadas

| Serviço | Porta | Status |
|---------|-------|--------|
| MAXIMUS Core | 8001 | CRÍTICO |
| Reflector | 8002 | Opcional |
| API Gateway | 8000 | Opcional |
| Frontend | 3000 | CRÍTICO |

