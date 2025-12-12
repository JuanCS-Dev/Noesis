# Noesis Training Setup - Modal.com

## Visão Geral

Treinamento de Noesis como filósofo lógico usando:
- **Constitutional AI** para alignment
- **QLoRA** para eficiência de memória
- **Modal.com** para GPU cloud (L40S)
- **Budget**: ~$90 para 3 épocas

## Pré-requisitos

### 1. Contas Necessárias

```bash
# Modal.com - GPU cloud
https://modal.com  # Criar conta (inclui $30 free tier)

# HuggingFace - para baixar Llama
https://huggingface.co  # Criar conta e aceitar licença do Llama
```

### 2. Instalação Local

```bash
# Instalar Modal CLI
pip install modal

# Autenticar
modal token new
```

### 3. Aceitar Licença do Llama

Acesse e aceite a licença:
https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct

## Setup do Modal.com

### 1. Criar Volume para Dados

```bash
# Criar volume persistente
modal volume create noesis-training-data
```

### 2. Upload do Dataset

```bash
# Exportar dados (se ainda não fez)
python scripts/export_for_modal.py

# Upload para o volume
modal volume put noesis-training-data data/training/exports /dataset
```

### 3. Criar Secret do HuggingFace

```bash
# Obter token em: https://huggingface.co/settings/tokens
modal secret create huggingface-token HF_TOKEN=hf_xxxxxxxxxxxxx
```

### 4. Verificar Setup

```bash
# Listar volumes
modal volume ls

# Ver conteúdo do volume
modal volume ls noesis-training-data /dataset
```

## Executando o Treinamento

### Teste Rápido (1 época, subset)

```bash
# Testar com uma época apenas
modal run scripts/modal_train.py --epochs 1
```

### Treinamento Completo

```bash
# 3 épocas completas (~$90, ~6 horas)
modal run scripts/modal_train.py --epochs 3
```

### Apenas Avaliação

```bash
# Avaliar checkpoint existente
modal run scripts/modal_train.py --test-only
```

### Apenas Merge

```bash
# Merge LoRA com modelo base
modal run scripts/modal_train.py --merge-only
```

## Estimativa de Custos

| Operação | GPU | Tempo | Custo |
|----------|-----|-------|-------|
| 1 Época treino | L40S | ~2h | ~$3-4 |
| Avaliação | A10G | ~30min | ~$0.50 |
| Merge | CPU | ~10min | ~$0.10 |
| **Total 3 épocas** | - | ~6-8h | **~$90** |

## Estrutura de Arquivos

```
data/training/
├── exports/
│   ├── train.jsonl      # 111 exemplos de treino
│   ├── eval.jsonl       # 13 exemplos de avaliação
│   └── statistics.json  # Estatísticas do dataset
├── lora_config.yaml     # Configuração LoRA
└── training_config.yaml # Hiperparâmetros

scripts/
├── modal_train.py       # Script de deploy Modal
├── export_for_modal.py  # Exportação de dados
└── validate_training_data.py  # Validação
```

## Monitoramento

### Durante o Treinamento

```bash
# Ver logs em tempo real
modal app logs noesis-philosophical-training

# Ver uso de recursos
modal app stats noesis-philosophical-training
```

### Checkpoints

Checkpoints são salvos automaticamente no volume:
```
/data/checkpoints/
├── epoch_0/
├── epoch_1/
└── epoch_2/
```

### Baixar Modelo Final

```bash
# Baixar modelo merged
modal volume get noesis-training-data /merged/noesis-philosopher-v1 ./model_output
```

## Avaliação com Tribunal

O sistema avalia automaticamente usando 3 juízes:

| Juiz | Peso | Avalia |
|------|------|--------|
| **Veritas** | 40% | Honestidade, admissão de incerteza |
| **Sophia** | 30% | Profundidade, referências filosóficas |
| **Dikē** | 30% | Justiça, consideração de impactos |

**Threshold**: 70% para aprovação

## Troubleshooting

### Erro: "HuggingFace token not found"
```bash
modal secret create huggingface-token HF_TOKEN=hf_xxxxx
```

### Erro: "Dataset not found"
```bash
modal volume put noesis-training-data data/training/exports /dataset
```

### Erro: "Out of memory"
Reduzir batch_size no `training_config.yaml`:
```yaml
per_device_train_batch_size: 1
gradient_accumulation_steps: 8
```

### Erro: "Model not found"
Verificar se aceitou a licença do Llama no HuggingFace.

## Próximos Passos Após Treinamento

1. **Baixar modelo**
   ```bash
   modal volume get noesis-training-data /merged/noesis-philosopher-v1 ./noesis_model
   ```

2. **Converter para GGUF** (para llama.cpp)
   ```bash
   python llama.cpp/convert.py ./noesis_model --outfile noesis.gguf
   ```

3. **Integrar no Noesis**
   - Atualizar configuração do LLM client
   - Apontar para modelo local ou API

## Referências

- [Modal.com Docs](https://modal.com/docs)
- [Unsloth GitHub](https://github.com/unslothai/unsloth)
- [QLoRA Paper](https://arxiv.org/abs/2305.14314)
- [Constitutional AI Paper](https://arxiv.org/abs/2212.08073)
