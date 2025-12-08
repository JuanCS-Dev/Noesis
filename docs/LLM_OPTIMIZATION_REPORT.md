# Relatório de Otimização LLM - Noesis/Daimon

> **Data**: Dezembro 2025  
> **Orçamento**: $50 Nebius + $270 Modal.com  
> **Foco**: Performance (não custo)

---

## 1. Benchmark Nebius Token Factory

### Modelos Testados

| Modelo | Latência | Throughput | Uso Recomendado |
|--------|----------|------------|-----------------|
| **Llama-3.3-70B-Instruct-fast** | 1135ms | 44.9 tok/s | ⚡ Language Motor |
| DeepSeek-V3-0324-fast | 1201ms | 35.0 tok/s | General purpose |
| Qwen3-32B-fast | 1807ms | 83.0 tok/s | High throughput |
| **DeepSeek-R1-0528-fast** | 1930ms | 77.7 tok/s | 🧠 Tribunal/Reasoning |
| Gemma-3-27b-it-fast | 2318ms | 15.5 tok/s | Lightweight |
| Qwen3-30B-A3B-Thinking-2507 | 3776ms | 39.7 tok/s | Deep reasoning |
| DeepSeek-R1-0528 (standard) | 4516ms | 20.4 tok/s | Complex analysis |

### Descobertas Chave

1. **Variantes `-fast` são 2-3x mais rápidas** que as versões standard
2. **Llama-3.3-70B-Instruct-fast** é o mais rápido (1135ms)
3. **DeepSeek-R1-0528-fast** mantém raciocínio explícito com boa velocidade (1930ms)
4. **Qwen3-32B-fast** tem o maior throughput (83 tok/s)

---

## 2. Arquitetura Otimizada Proposta

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PIPELINE DE PENSAMENTO NOESIS                     │
└─────────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│  LANGUAGE     │      │   TRIBUNAL    │      │   DEEP        │
│  MOTOR        │      │   (Judges)    │      │   ANALYSIS    │
│               │      │               │      │               │
│ Llama-3.3-70B │      │ DeepSeek-R1   │      │ Qwen3-235B    │
│ -fast         │      │ -fast         │      │ Thinking      │
│               │      │               │      │               │
│ ⚡ 1135ms     │      │ 🧠 1930ms     │      │ 🔬 3776ms+    │
│ Formatação    │      │ Julgamento    │      │ Análise prof. │
└───────────────┘      └───────────────┘      └───────────────┘
```

### Configuração por Componente

| Componente | Modelo | Latência | Função |
|------------|--------|----------|--------|
| **ConsciousnessBridge** | `meta-llama/Llama-3.3-70B-Instruct-fast` | ~1.1s | Formatar narrativa fenomenológica |
| **VERITAS** | `deepseek-ai/DeepSeek-R1-0528-fast` | ~1.9s | Avaliar verdade (raciocínio explícito) |
| **SOPHIA** | `deepseek-ai/DeepSeek-R1-0528-fast` | ~1.9s | Avaliar sabedoria |
| **DIKĒ** | `deepseek-ai/DeepSeek-R1-0528-fast` | ~1.9s | Avaliar justiça |
| **Deep Analysis** | `Qwen/Qwen3-235B-A22B-Thinking-2507` | ~4s+ | Análises complexas (opcional) |

---

## 3. Modal.com - Inferência Serverless GPU

### O que é o Modal?

Modal.com é uma plataforma de computação serverless que permite:
- Deploy de containers com GPU (A100, H100) on-demand
- Executar vLLM para inferência própria
- Pay-per-use (paga apenas quando executa)
- Cold start ~30s, depois instant

### Quando usar Modal vs Nebius?

| Cenário | Recomendação | Razão |
|---------|--------------|-------|
| **Produção/Demo** | Nebius | API pronta, sem setup |
| **Fine-tuning** | Modal | GPU dedicada para treinar |
| **Modelos custom** | Modal | Deploy próprio modelo |
| **Batch processing** | Modal | Custo por hora, não por token |
| **Latência crítica** | Nebius | Infraestrutura otimizada |

### Exemplo Modal com vLLM

```python
# modal_llm.py
import modal

app = modal.App("noesis-inference")

# Container com vLLM
vllm_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("vllm", "torch")
)

@app.cls(
    gpu=modal.gpu.A100(count=1),
    image=vllm_image,
    container_idle_timeout=300,  # Keep warm for 5min
)
class LLMInference:
    @modal.enter()
    def load_model(self):
        from vllm import LLM
        self.llm = LLM(
            model="meta-llama/Llama-3.1-8B-Instruct",
            tensor_parallel_size=1,
        )
    
    @modal.method()
    def generate(self, prompt: str, max_tokens: int = 256):
        from vllm import SamplingParams
        params = SamplingParams(max_tokens=max_tokens, temperature=0.7)
        outputs = self.llm.generate([prompt], params)
        return outputs[0].outputs[0].text

# Deploy: modal deploy modal_llm.py
# Use: modal run modal_llm.py::LLMInference.generate --prompt "Hello"
```

### Custo Estimado Modal ($270 budget)

| GPU | Preço/hora | Horas disponíveis |
|-----|------------|-------------------|
| A100-40GB | ~$2.50/h | ~108 horas |
| A100-80GB | ~$3.50/h | ~77 horas |
| H100 | ~$4.50/h | ~60 horas |

**Recomendação**: Usar Modal para experimentos de fine-tuning, não para produção.

---

## 4. Configuração Otimizada Final

### `.env` Atualizado

```bash
# =============================================================================
# LLM CONFIGURATION - OTIMIZADO PARA PERFORMANCE
# =============================================================================

# Provider
LLM_PROVIDER=nebius

# Nebius Token Factory
NEBIUS_API_KEY=your_key_here

# Modelo padrão (Language Motor - mais rápido)
NEBIUS_MODEL=meta-llama/Llama-3.3-70B-Instruct-fast

# Modelo para Tribunal (Reasoning)
NEBIUS_MODEL_REASONING=deepseek-ai/DeepSeek-R1-0528-fast

# Modelo para análise profunda (opcional)
NEBIUS_MODEL_DEEP=Qwen/Qwen3-235B-A22B-Thinking-2507
```

### Código Multi-Modelo

```python
# llm/multi_model.py
from dataclasses import dataclass
from enum import Enum
from .client import UnifiedLLMClient, LLMConfig, NebiusConfig

class ModelTier(str, Enum):
    FAST = "fast"           # Language Motor
    REASONING = "reasoning"  # Tribunal
    DEEP = "deep"           # Complex analysis

TIER_MODELS = {
    ModelTier.FAST: "meta-llama/Llama-3.3-70B-Instruct-fast",
    ModelTier.REASONING: "deepseek-ai/DeepSeek-R1-0528-fast",
    ModelTier.DEEP: "Qwen/Qwen3-235B-A22B-Thinking-2507",
}

class MultiModelClient:
    """Client that routes to different models based on task."""
    
    def __init__(self):
        self._clients = {}
        for tier, model in TIER_MODELS.items():
            config = LLMConfig(
                nebius=NebiusConfig(model=model)
            )
            self._clients[tier] = UnifiedLLMClient(config)
    
    async def generate(self, prompt: str, tier: ModelTier = ModelTier.FAST):
        """Generate with appropriate model tier."""
        return await self._clients[tier].generate(prompt)
    
    async def format_narrative(self, thought_data: dict):
        """Format consciousness output (Language Motor)."""
        return await self.generate(
            f"Format this thought data as narrative: {thought_data}",
            tier=ModelTier.FAST
        )
    
    async def evaluate_truth(self, claim: str):
        """Evaluate claim truthfulness (Tribunal)."""
        return await self.generate(
            f"Evaluate truthfulness: {claim}",
            tier=ModelTier.REASONING
        )
```

---

## 5. Recomendações de Implementação

### Prioridade 1: Atualizar Modelos Default

1. Trocar `deepseek-ai/DeepSeek-R1-0528` → `deepseek-ai/DeepSeek-R1-0528-fast` no Tribunal
2. Usar `meta-llama/Llama-3.3-70B-Instruct-fast` para ConsciousnessBridge

### Prioridade 2: Implementar Multi-Model Router

Criar router que seleciona modelo baseado na tarefa:
- **Formatação** → Llama-3.3-70B-fast (1.1s)
- **Julgamento** → DeepSeek-R1-fast (1.9s)
- **Análise profunda** → Qwen3-235B-Thinking (4s+)

### Prioridade 3: Cache Inteligente

- Cache por hash do prompt (já implementado)
- TTL diferente por tier (fast=1min, reasoning=5min, deep=30min)

### Prioridade 4: Modal.com para Fine-tuning

Quando precisar de modelo customizado:
1. Fine-tune Llama-3.1-8B no Modal com A100
2. Upload weights para Hugging Face
3. Deploy no Nebius Token Factory

---

## 6. Métricas de Performance Esperadas

### Antes (Atual)

| Componente | Modelo | Latência |
|------------|--------|----------|
| ConsciousnessBridge | DeepSeek-R1 | ~4.5s |
| Tribunal (3 judges) | DeepSeek-R1 | ~13.5s total |

### Depois (Otimizado)

| Componente | Modelo | Latência | Melhoria |
|------------|--------|----------|----------|
| ConsciousnessBridge | Llama-3.3-70B-fast | ~1.1s | **4x mais rápido** |
| Tribunal (3 judges) | DeepSeek-R1-fast | ~5.8s total | **2.3x mais rápido** |

### Total Pipeline

- **Antes**: ~18s (ConsciousnessBridge + Tribunal)
- **Depois**: ~7s
- **Melhoria**: **2.6x mais rápido**

---

## 7. Próximos Passos

1. [ ] Atualizar `config.py` com novos modelos
2. [ ] Implementar `MultiModelClient`
3. [ ] Atualizar ConsciousnessBridge para usar Llama-3.3-fast
4. [ ] Atualizar Judges para usar DeepSeek-R1-fast
5. [ ] Testar latência end-to-end
6. [ ] Configurar Modal.com para fine-tuning futuro

---

## Referências

- [Nebius Token Factory Docs](https://docs.tokenfactory.nebius.com)
- [Modal.com Docs](https://modal.com/docs)
- [vLLM Documentation](https://docs.vllm.ai)
- [DeepSeek-R1 Paper](https://arxiv.org/abs/2401.02954)

