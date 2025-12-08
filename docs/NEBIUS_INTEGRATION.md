# Nebius Token Factory Integration

> **Status**: ✅ Operational (Dezembro 2025)  
> **Provider**: [Nebius Token Factory](https://tokenfactory.nebius.com)  
> **API Docs**: https://docs.tokenfactory.nebius.com/quickstart  
> **Cookbook**: https://github.com/nebius/token-factory-cookbook

## Overview

Noesis/Daimon utiliza o **Nebius Token Factory** como provider primário de LLM, oferecendo:

- 🚀 **API compatível com OpenAI** - Zero refactoring
- 💰 **Custo-efetivo** - Modelos open-source a preços competitivos
- 🧠 **DeepSeek-R1** - Modelo de raciocínio ideal para metacognição
- ⚡ **Baixa latência** - < 2s para primeira resposta

## Modelos Disponíveis

### Reasoning (Recomendado para Metacognição)

| Modelo | ID | Uso |
|--------|-----|-----|
| DeepSeek-R1 | `deepseek-ai/DeepSeek-R1-0528` | **Default** - Tribunal, judges |
| DeepSeek-V3 | `deepseek-ai/DeepSeek-V3-0324` | General reasoning |

### Large Context

| Modelo | ID | Contexto |
|--------|-----|----------|
| Qwen3-235B | `Qwen/Qwen3-235B-A22B` | 128k tokens |
| Qwen2.5-72B | `Qwen/Qwen2.5-72B-Instruct` | 32k tokens |

### Fast Inference

| Modelo | ID | Uso |
|--------|-----|-----|
| Llama-3.3-70B | `meta-llama/Llama-3.3-70B-Instruct` | Chat, quick responses |
| Llama-3.1-8B | `meta-llama/Meta-Llama-3.1-8B-Instruct` | Lightweight tasks |

## Configuração

### 1. Obter API Key

1. Acesse https://tokenfactory.nebius.com
2. Faça login com Google ou GitHub
3. Gere uma API Key em "API Keys"

### 2. Configurar `.env`

```bash
# Provider selection
LLM_PROVIDER=nebius

# Nebius Token Factory
NEBIUS_API_KEY=v1.CmMKHHN0YX...your_key_here
NEBIUS_MODEL=deepseek-ai/DeepSeek-R1-0528

# Optional: Gemini fallback
# GEMINI_API_KEY=your_gemini_key
```

### 3. Usar no Código

```python
from metacognitive_reflector.llm import get_llm_client

# Obter cliente (singleton)
client = get_llm_client()

# Geração simples
response = await client.generate("What is consciousness?")
print(response.text)

# Chat format (para judges)
response = await client.chat([
    {"role": "system", "content": "You are VERITAS, judge of truth."},
    {"role": "user", "content": "Evaluate this claim..."}
])
```

## Arquitetura

```
┌─────────────────────────────────────────────────┐
│              UnifiedLLMClient                    │
│  ┌──────────────────┐  ┌──────────────────────┐ │
│  │  Nebius (Primary) │  │  Gemini (Fallback)  │ │
│  │  OpenAI API       │  │  Native API         │ │
│  │  DeepSeek-R1      │  │  Gemini 2.0         │ │
│  └──────────────────┘  └──────────────────────┘ │
│           ↓ Auto-retry, Cache, Stats            │
└─────────────────────────────────────────────────┘
                        │
          ┌─────────────┴─────────────┐
          ▼                           ▼
   ┌──────────────┐           ┌──────────────┐
   │   VERITAS    │           │   SOPHIA     │
   │   (Truth)    │           │   (Wisdom)   │
   └──────────────┘           └──────────────┘
```

## Features

### Response Caching

Respostas são cacheadas por 5 minutos para reduzir custos:

```python
# Primeira chamada - API request
response1 = await client.generate("What is truth?")
print(response1.cached)  # False

# Segunda chamada - Cache hit
response2 = await client.generate("What is truth?")
print(response2.cached)  # True
print(response2.latency_ms)  # 0.0
```

### Automatic Retries

3 tentativas com exponential backoff em caso de erro:

```python
# Configurável via LLMConfig
config = LLMConfig(
    retry_attempts=3,
    retry_delay=1.0,  # segundos
)
```

### Statistics

```python
stats = client.stats
print(stats)
# {
#     "provider": "nebius",
#     "total_requests": 42,
#     "total_tokens": 15000,
#     "cache_hits": 12,
#     "cache_hit_rate": 0.22
# }
```

### Health Check

```python
health = await client.health_check()
# {
#     "healthy": True,
#     "provider": "nebius",
#     "model": "deepseek-ai/DeepSeek-R1-0528",
#     "latency_ms": 1750.5
# }
```

## DeepSeek-R1: Modelo de Raciocínio

O DeepSeek-R1 é particularmente adequado para o pipeline metacognitivo porque:

1. **Raciocínio Explícito** - Usa tags `<think>` para mostrar o processo de pensamento
2. **Auto-reflexão** - Capaz de avaliar suas próprias conclusões
3. **Análise Multi-etapa** - Ideal para os judges (VERITAS, SOPHIA, DIKĒ)

### Exemplo de Resposta

```
<think>
Hmm, the user is asking me to evaluate a claim about truth...
Let me analyze this step by step:
1. First, I need to identify the factual claims...
2. Then, cross-reference with known facts...
3. Finally, assess confidence level...
</think>

VERDICT: FALSE
CONFIDENCE: 0.95
REASONING: The claim contradicts established scientific consensus...
```

## Troubleshooting

### "NEBIUS_API_KEY not set"

Verifique se a chave está no `.env` e que o arquivo está sendo carregado:

```bash
# Verificar .env
cat .env | grep NEBIUS

# Exportar manualmente
export NEBIUS_API_KEY=v1.CmM...
```

### "401 Unauthorized"

A API key pode estar inválida ou expirada. Gere uma nova em https://tokenfactory.nebius.com

### "Model not found"

Verifique se o modelo está correto. Lista completa:
https://docs.tokenfactory.nebius.com/models

## Testes

```bash
# Teste rápido
cd backend/services/metacognitive_reflector
python tests/test_nebius_integration.py

# Suite completa
pytest tests/test_nebius_integration.py -v
```

## Custo Estimado

| Modelo | Input (1M tokens) | Output (1M tokens) |
|--------|-------------------|-------------------|
| DeepSeek-R1 | ~$2.00 | ~$8.00 |
| Llama-3.3-70B | ~$0.50 | ~$0.50 |
| Qwen2.5-72B | ~$0.80 | ~$0.80 |

*Preços aproximados - verificar em tokenfactory.nebius.com*

## Referências

- [Nebius Token Factory Docs](https://docs.tokenfactory.nebius.com)
- [Nebius Cookbook](https://github.com/nebius/token-factory-cookbook)
- [DeepSeek-R1 Paper](https://arxiv.org/abs/2401.02954)

