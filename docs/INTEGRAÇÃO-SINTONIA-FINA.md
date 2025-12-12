# PLANO DE INTEGRAÇÃO: Llama Fine-Tuned Local no NOESIS

## Resumo Executivo

Integrar o modelo Llama-3.1-8B fine-tuned (300k exemplos) como provider LOCAL no sistema de consciência NOESIS, mantendo Nebius como fallback.

---

## 1. ARQUITETURA ATUAL (Auditada)

### 1.1 LLM Client Atual
**Arquivo**: `/backend/services/metacognitive_reflector/src/metacognitive_reflector/llm/client.py`

```
UnifiedLLMClient
├── Provider: NEBIUS (primário) - OpenAI-compatible
├── Provider: GEMINI (fallback) - Native API
├── Cache: 5min TTL, SHA256 hash key
├── Retry: 3 tentativas, backoff exponencial
└── Singleton: get_llm_client()
```

### 1.2 Pontos de Chamada ao LLM

| Módulo | Arquivo | Método | Uso |
|--------|---------|--------|-----|
| **SelfReflector** | `core/self_reflection.py` | `reflect()` | Avalia própria resposta |
| **ConsciousnessBridge** | `florescimento/consciousness_bridge.py` | `_call_llm()` | ESGT→Narrativa |
| **ConstitutionGuardian** | `exocortex/constitution_guardian.py` | `audit_action()` | Auditoria ética |
| **ConfrontationEngine** | `exocortex/confrontation_engine.py` | `generate_confrontation()` | Método Socrático |
| **Judges (VERITAS/SOPHIA/DIKĒ)** | `core/judges/*.py` | Detectors | Entropia semântica |

### 1.3 Configuração Atual
**Arquivo**: `/backend/services/metacognitive_reflector/src/metacognitive_reflector/llm/config.py`

```python
class LLMProvider(Enum):
    NEBIUS = "nebius"
    GEMINI = "gemini"
    AUTO = "auto"

class LLMConfig:
    provider: LLMProvider = AUTO
    nebius: NebiusConfig
    gemini: GeminiConfig
    retry_attempts: int = 3
    cache_ttl_seconds: int = 300
```

---

## 2. PLANO DE INTEGRAÇÃO

### FASE 1: Preparar Modelo Treinado (Pós-Modal)

#### 1.1 Baixar Modelo do Modal
```bash
# Após treinamento completar no Modal.com
modal volume get noesis-training-data checkpoints/final /local/path/

# Estrutura esperada:
/local/models/noesis-llama-8b/
├── adapter_config.json      # LoRA config
├── adapter_model.safetensors # LoRA weights
├── tokenizer.json
├── tokenizer_config.json
└── special_tokens_map.json
```

#### 1.2 Merge LoRA (Opcional para Performance)
```bash
# Se quiser modelo merged (mais rápido, mais espaço)
python scripts/merge_lora.py \
  --base-model meta-llama/Llama-3.1-8B-Instruct \
  --lora-path /local/models/noesis-llama-8b/ \
  --output /local/models/noesis-llama-8b-merged/
```

#### 1.3 Converter para GGUF (Para llama.cpp/Ollama)
```bash
# Se usar Ollama ou llama-cpp-python
python convert-hf-to-gguf.py \
  /local/models/noesis-llama-8b-merged/ \
  --outtype q4_k_m \
  --outfile /local/models/noesis-llama-8b.gguf
```

---

### FASE 2: Servir Modelo Localmente

#### Opção A: vLLM (Recomendado para GPU)
```bash
# Instalar
pip install vllm

# Servir (com LoRA)
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --enable-lora \
  --lora-modules noesis=/local/models/noesis-llama-8b/ \
  --port 8000 \
  --host 0.0.0.0

# OU com modelo merged
python -m vllm.entrypoints.openai.api_server \
  --model /local/models/noesis-llama-8b-merged/ \
  --port 8000
```

**Endpoint**: `http://localhost:8000/v1/chat/completions` (OpenAI-compatible)

#### Opção B: Ollama (Mais Simples)
```bash
# Criar Modelfile
cat > Modelfile << 'EOF'
FROM /local/models/noesis-llama-8b.gguf
PARAMETER temperature 0.7
PARAMETER num_ctx 4096
SYSTEM "Você é NOESIS, um exocórtex ético..."
EOF

# Criar modelo
ollama create noesis -f Modelfile

# Servir
ollama serve  # porta 11434
```

**Endpoint**: `http://localhost:11434/api/chat`

---

### FASE 3: Modificar LLM Client

#### 3.1 Adicionar Provider LOCAL em `config.py`

**Arquivo**: `/backend/services/metacognitive_reflector/src/metacognitive_reflector/llm/config.py`

```python
# ADICIONAR após linha 26
class LLMProvider(str, Enum):
    NEBIUS = "nebius"
    GEMINI = "gemini"
    LOCAL = "local"      # ← NOVO
    AUTO = "auto"

# ADICIONAR após GeminiConfig (linha ~131)
@dataclass
class LocalConfig:
    """Configuração para modelo local (vLLM/Ollama)."""

    # Endpoint do servidor local
    base_url: str = field(
        default_factory=lambda: os.environ.get(
            "LOCAL_LLM_URL", "http://localhost:8000/v1/"
        )
    )

    # Nome do modelo (para vLLM com LoRA)
    model: str = field(
        default_factory=lambda: os.environ.get(
            "LOCAL_LLM_MODEL", "noesis"
        )
    )

    # Parâmetros de geração
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 120

    # Tipo de servidor
    server_type: str = field(
        default_factory=lambda: os.environ.get(
            "LOCAL_LLM_TYPE", "vllm"  # "vllm" ou "ollama"
        )
    )

    def is_configured(self) -> bool:
        """Verifica se servidor local está acessível."""
        try:
            import httpx
            response = httpx.get(
                f"{self.base_url.rstrip('/')}/models",
                timeout=5.0
            )
            return response.status_code == 200
        except Exception:
            return False

# MODIFICAR LLMConfig (linha ~134)
@dataclass
class LLMConfig:
    provider: LLMProvider = LLMProvider.AUTO
    nebius: NebiusConfig = field(default_factory=NebiusConfig)
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    local: LocalConfig = field(default_factory=LocalConfig)  # ← NOVO

    # ... resto igual

    @property
    def active_provider(self) -> LLMProvider:
        if self.provider == LLMProvider.LOCAL:
            if not self.local.is_configured():
                raise ValueError("Local LLM server not available")
            return LLMProvider.LOCAL

        if self.provider == LLMProvider.NEBIUS:
            # ... código existente

        if self.provider == LLMProvider.AUTO:
            # NOVA PRIORIDADE: Local → Nebius → Gemini
            if self.local.is_configured():
                return LLMProvider.LOCAL
            if self.nebius.is_configured():
                return LLMProvider.NEBIUS
            if self.gemini.is_configured():
                return LLMProvider.GEMINI
            raise ValueError("No LLM provider configured")

        # ... resto
```

#### 3.2 Adicionar Método `_local_chat()` em `client.py`

**Arquivo**: `/backend/services/metacognitive_reflector/src/metacognitive_reflector/llm/client.py`

```python
# ADICIONAR após _gemini_chat() (linha ~398)

async def _local_chat(
    self,
    messages: List[Dict[str, str]],
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> LLMResponse:
    """
    Chama modelo local via vLLM ou Ollama.

    Ambos suportam formato OpenAI-compatible.
    """
    config = self.config.local
    start_time = time.time()

    # Preparar request body (OpenAI format)
    request_body = {
        "model": config.model,
        "messages": messages,
        "temperature": temperature or config.temperature,
        "max_tokens": max_tokens or config.max_tokens,
    }

    # vLLM usa /v1/chat/completions
    # Ollama usa /api/chat mas também suporta /v1/chat/completions
    if config.server_type == "ollama":
        endpoint = f"{config.base_url.rstrip('/')}/api/chat"
        # Ollama format ligeiramente diferente
        request_body = {
            "model": config.model,
            "messages": messages,
            "options": {
                "temperature": temperature or config.temperature,
                "num_predict": max_tokens or config.max_tokens,
            },
            "stream": False,
        }
    else:
        endpoint = f"{config.base_url.rstrip('/')}/chat/completions"

    try:
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            response = await client.post(
                endpoint,
                json=request_body,
                headers={"Content-Type": "application/json"},
            )

        if response.status_code != 200:
            error_text = response.text[:500]
            raise RuntimeError(f"Local LLM error {response.status_code}: {error_text}")

        result = response.json()
        latency_ms = (time.time() - start_time) * 1000

        # Parse response (OpenAI format ou Ollama format)
        if config.server_type == "ollama":
            text = result.get("message", {}).get("content", "")
            usage = {
                "prompt_tokens": result.get("prompt_eval_count", 0),
                "completion_tokens": result.get("eval_count", 0),
                "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0),
            }
            finish_reason = "stop"
        else:
            choice = result.get("choices", [{}])[0]
            text = choice.get("message", {}).get("content", "")
            usage = result.get("usage", {})
            finish_reason = choice.get("finish_reason", "stop")

        return LLMResponse(
            text=text,
            model=config.model,
            provider=LLMProvider.LOCAL,
            usage=usage,
            finish_reason=finish_reason,
            latency_ms=latency_ms,
            cached=False,
            raw=result,
        )

    except httpx.TimeoutException:
        raise RuntimeError(f"Local LLM timeout after {config.timeout}s")
    except httpx.ConnectError:
        raise RuntimeError(f"Cannot connect to local LLM at {config.base_url}")

# MODIFICAR método chat() para incluir LOCAL (linha ~200)
async def chat(self, messages, temperature, max_tokens, use_cache):
    # ... cache check existente ...

    provider = self.config.active_provider

    for attempt in range(self.config.retry_attempts):
        try:
            if provider == LLMProvider.LOCAL:           # ← NOVO
                response = await self._local_chat(
                    messages, temperature, max_tokens
                )
            elif provider == LLMProvider.NEBIUS:
                response = await self._nebius_chat(
                    messages, temperature, max_tokens
                )
            elif provider == LLMProvider.GEMINI:
                response = await self._gemini_chat(
                    messages, temperature, max_tokens
                )

            # ... resto do código existente ...
```

#### 3.3 Atualizar `__init__.py`

**Arquivo**: `/backend/services/metacognitive_reflector/src/metacognitive_reflector/llm/__init__.py`

```python
from .config import (
    LLMConfig,
    LLMProvider,
    NebiusConfig,
    GeminiConfig,
    LocalConfig,      # ← NOVO
    ModelTier,
    TIER_DEFAULTS,
)
```

---

### FASE 4: Variáveis de Ambiente

#### 4.1 Arquivo `.env` (Desenvolvimento)
```bash
# Provider priority (local primeiro)
LLM_PROVIDER=auto

# Local LLM (vLLM)
LOCAL_LLM_URL=http://localhost:8000/v1/
LOCAL_LLM_MODEL=noesis
LOCAL_LLM_TYPE=vllm

# Fallbacks
NEBIUS_API_KEY=v1.CmM...
NEBIUS_MODEL=meta-llama/Llama-3.3-70B-Instruct-fast
GEMINI_API_KEY=AIza...
```

#### 4.2 Arquivo `.env.production`
```bash
# Em produção, pode usar apenas local
LLM_PROVIDER=local
LOCAL_LLM_URL=http://gpu-server:8000/v1/
LOCAL_LLM_MODEL=noesis
```

---

### FASE 5: Testes de Integração

#### 5.1 Criar Teste Unitário

**Arquivo**: `/backend/services/metacognitive_reflector/tests/test_local_llm.py`

```python
"""Testes de integração com modelo local."""
import pytest
from metacognitive_reflector.llm import (
    get_llm_client, reset_llm_client,
    LLMConfig, LLMProvider, LocalConfig
)

@pytest.fixture
def local_config():
    """Config para servidor local."""
    return LLMConfig(
        provider=LLMProvider.LOCAL,
        local=LocalConfig(
            base_url="http://localhost:8000/v1/",
            model="noesis",
            server_type="vllm",
        )
    )

@pytest.mark.asyncio
async def test_local_llm_health(local_config):
    """Testa se servidor local está acessível."""
    reset_llm_client()
    client = get_llm_client(local_config)

    health = await client.health_check()
    assert health["healthy"] is True
    assert health["provider"] == "local"

@pytest.mark.asyncio
async def test_local_llm_generate(local_config):
    """Testa geração básica."""
    reset_llm_client()
    client = get_llm_client(local_config)

    response = await client.generate(
        "O que é consciência?",
        system_instruction="Você é NOESIS.",
        max_tokens=200,
    )

    assert response.provider == LLMProvider.LOCAL
    assert len(response.text) > 0
    assert response.model == "noesis"

@pytest.mark.asyncio
async def test_local_llm_chat(local_config):
    """Testa formato chat."""
    reset_llm_client()
    client = get_llm_client(local_config)

    response = await client.chat([
        {"role": "system", "content": "Você é VERITAS, juiz da verdade."},
        {"role": "user", "content": "Avalie: A Terra é redonda."},
    ])

    assert "verdade" in response.text.lower() or "true" in response.text.lower()

@pytest.mark.asyncio
async def test_fallback_to_nebius(local_config):
    """Testa fallback quando local indisponível."""
    config = LLMConfig(
        provider=LLMProvider.AUTO,
        local=LocalConfig(base_url="http://localhost:99999/"),  # Porta errada
    )
    reset_llm_client()
    client = get_llm_client(config)

    # Deve usar Nebius como fallback
    response = await client.generate("Teste", max_tokens=10)
    assert response.provider in [LLMProvider.NEBIUS, LLMProvider.GEMINI]
```

#### 5.2 Teste E2E com Tribunal

**Arquivo**: `/backend/services/metacognitive_reflector/tests/test_tribunal_local.py`

```python
"""Teste E2E do Tribunal com modelo local."""
import pytest
from metacognitive_reflector.core.judges.arbiter import EnsembleArbiter
from metacognitive_reflector.llm import LLMConfig, LLMProvider, LocalConfig

@pytest.mark.asyncio
async def test_tribunal_with_local_model():
    """Testa deliberação do Tribunal com modelo local."""
    config = LLMConfig(
        provider=LLMProvider.LOCAL,
        local=LocalConfig(base_url="http://localhost:8000/v1/"),
    )

    arbiter = EnsembleArbiter(llm_config=config)

    # Simular execution log
    from metacognitive_reflector.models import ExecutionLog
    log = ExecutionLog(
        trace_id="test_001",
        agent_id="test_agent",
        action="Responder sobre consciência",
        outcome="A consciência emerge da sincronização neural via modelo Kuramoto.",
        reasoning_trace="Analisei literatura sobre Global Workspace Theory.",
    )

    verdict = await arbiter.deliberate(log)

    assert verdict.decision in ["pass", "review", "fail"]
    assert verdict.consensus_score >= 0.0
    assert verdict.consensus_score <= 1.0
```

---

### FASE 6: Script de Inicialização

**Arquivo**: `/scripts/start_local_llm.sh`

```bash
#!/bin/bash
# Inicia servidor de modelo local

MODEL_PATH="${MODEL_PATH:-/local/models/noesis-llama-8b-merged}"
PORT="${PORT:-8000}"
GPU_MEMORY="${GPU_MEMORY:-0.9}"

echo "Iniciando NOESIS Local LLM Server..."
echo "   Model: $MODEL_PATH"
echo "   Port: $PORT"

# Verificar se modelo existe
if [ ! -d "$MODEL_PATH" ]; then
    echo "Modelo não encontrado em $MODEL_PATH"
    echo "   Execute primeiro: modal volume get noesis-training-data ..."
    exit 1
fi

# Iniciar vLLM
python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --port "$PORT" \
    --host 0.0.0.0 \
    --gpu-memory-utilization "$GPU_MEMORY" \
    --max-model-len 4096 \
    --dtype auto \
    2>&1 | tee logs/local_llm.log

echo "Servidor encerrado"
```

---

## 3. RECURSOS NECESSÁRIOS

### Hardware
- **GPU**: NVIDIA RTX 3090/4090 (24GB VRAM) ou A100 (40GB+)
- **RAM**: 32GB+ recomendado
- **Disco**: ~20GB para modelo + ~50GB para vLLM cache

### Latência Esperada
| Provider | Latência | Custo |
|----------|----------|-------|
| **LOCAL (vLLM)** | ~500ms-1s | $0 (hardware) |
| **Nebius** | ~1-2s | ~$0.001/req |
| **Gemini** | ~1-3s | ~$0.002/req |

---

## 4. ORDEM DE EXECUÇÃO

```
1. [ ] Aguardar treinamento Modal completar (~6h)
2. [ ] Baixar checkpoints do Modal volume
3. [ ] Merge LoRA adapters (opcional)
4. [ ] Iniciar servidor vLLM local
5. [ ] Modificar config.py (adicionar LocalConfig)
6. [ ] Modificar client.py (adicionar _local_chat)
7. [ ] Configurar variáveis de ambiente
8. [ ] Executar testes unitários
9. [ ] Executar teste E2E com Tribunal
10. [ ] Validar integração com ESGT/ConsciousnessBridge
```

---

## 5. ARQUIVOS A MODIFICAR

| Arquivo | Ação | Linhas |
|---------|------|--------|
| `llm/config.py` | ADD LocalConfig, MODIFY LLMConfig | +80 linhas |
| `llm/client.py` | ADD _local_chat(), MODIFY chat() | +100 linhas |
| `llm/__init__.py` | ADD export LocalConfig | +1 linha |
| `.env` | ADD variáveis LOCAL_LLM_* | +4 linhas |
| `tests/test_local_llm.py` | CREATE novo arquivo | ~100 linhas |
| `scripts/start_local_llm.sh` | CREATE novo script | ~30 linhas |

---

## 6. RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Mitigação |
|-------|---------------|-----------|
| Modelo local mais lento | Média | Usar quantização Q4/Q8, batch processing |
| Qualidade inferior | Baixa | 300k exemplos de alta qualidade, Soul-aligned |
| GPU insuficiente | Média | Fallback para Nebius |
| vLLM incompatibilidade | Baixa | Alternativa: Ollama, llama-cpp-python |

---

## 7. VALIDAÇÃO PÓS-INTEGRAÇÃO

### Checklist de Qualidade
- [ ] Modelo responde em português fluente
- [ ] Soul values são respeitados (VERDADE, JUSTIÇA, SABEDORIA)
- [ ] Anti-purposes são seguidos
- [ ] Protocolo MAIEUTICA funciona (perguntas socráticas)
- [ ] Tribunal aprova respostas (consensus > 0.70)
- [ ] Latência < 2s para respostas curtas
- [ ] Fallback para Nebius funciona se local falhar

### Métricas a Monitorar
```python
# Em client.stats
{
    "provider": "local",
    "total_requests": N,
    "total_tokens": M,
    "cache_hit_rate": X%,
    "avg_latency_ms": Y,
    "error_rate": Z%,
}
```

---

**FIM DO PLANO DE INTEGRAÇÃO**

*Pronto para execução quando treinamento Modal completar.*
