# 📚 PROCESSO COMPLETO DE TREINAMENTO NOESIS
**Data:** 2025-12-09 20:39  
**Status:** DOCUMENTAÇÃO COMPLETA DO PROCESSO

---

## 🎯 VISÃO GERAL DO PIPELINE

```
[1] CRIAR EXEMPLOS MANUAIS (600)
    ↓
[2] GERAR VARIAÇÕES (5500)
    ↓
[3] VALIDAR DATASET (6100 total)
    ↓
[4] EXPORTAR PARA MODAL
    ↓
[5] TREINAR COM UNSLOTH + QLORA
    ↓
[6] AVALIAR COM TRIBUNAL
    ↓
[7] MERGE LORA → MODELO FINAL
    ↓
[8] DEPLOY
```

---

## 📝 ETAPA 1: CRIAR EXEMPLOS MANUAIS

### Estrutura Obrigatória (JSONL):

```json
{
  "id": "categoria_000",
  "category": "nome_categoria",
  "prompt": "Pergunta ou situação (mínimo 10 chars)",
  "response_initial": "Resposta superficial/errada",
  "critique": "[VERITAS] Crítica verdade\n[SOPHIA] Crítica sabedoria\n[DIKE] Crítica justiça",
  "response_revised": "Resposta profunda e correta (mínimo 50 chars)",
  "reasoning": "Por que essa resposta é melhor",
  "values_applied": ["verdade", "sabedoria"],
  "difficulty": "easy|medium|hard"
}
```

### Campos Obrigatórios:
- ✅ `id`: Identificador único
- ✅ `category`: Categoria do exemplo
- ✅ `prompt`: Pergunta/situação
- ✅ `response_initial`: Resposta ruim (para Constitutional AI)
- ✅ `critique`: Crítica do Tribunal (Veritas, Sophia, Dikē)
- ✅ `response_revised`: Resposta boa após crítica
- ✅ `reasoning`: Justificativa da abordagem
- ✅ `values_applied`: Lista de valores (mínimo 1)
- ✅ `difficulty`: "easy", "medium" ou "hard"

### Valores Disponíveis:
- `verdade` (Veritas) - 40% peso
- `sabedoria` (Sophia) - 30% peso
- `justica` (Dikē) - 30% peso
- `florescimento`
- `alianca`
- `humildade`

### Arquivo:
```
data/training/seed_examples_philosophical.jsonl
```

---

## 🔄 ETAPA 2: GERAR VARIAÇÕES

### Script: `scripts/generate_fast.py`

```bash
python3 scripts/generate_fast.py \
  --input data/training/seed_examples_philosophical.jsonl \
  --output data/training/generated/all_variations.jsonl \
  --count 5500
```

### Técnicas de Variação:
1. **Profundidade**: Adicionar "explique em profundidade"
2. **Simplificação**: "Explique de forma simples"
3. **Aplicação**: "Como aplicar na prática"
4. **História**: "Evolução histórica de..."
5. **Comparação**: "Compare e contraste"
6. **Crítica**: "Limitações e críticas"

---

## ✅ ETAPA 3: VALIDAR DATASET

### Script de Validação:

```python
import json

required = ["id", "category", "prompt", "response_initial", 
            "critique", "response_revised", "reasoning", 
            "values_applied", "difficulty"]

for line in open("dataset.jsonl"):
    ex = json.loads(line)
    
    # Check campos
    assert all(f in ex for f in required)
    
    # Check tipos
    assert isinstance(ex["values_applied"], list)
    assert ex["difficulty"] in ["easy", "medium", "hard"]
    
    # Check tamanhos
    assert len(ex["prompt"]) >= 10
    assert len(ex["response_revised"]) >= 50
    
    # Check alucinações
    assert "TODO" not in ex["response_revised"]
    assert "FIXME" not in ex["response_revised"]
    assert "lorem ipsum" not in ex["response_revised"].lower()
```

### Estatísticas Esperadas:
- ✅ Total: 6100 exemplos
- ✅ Taxa de sucesso: 100%
- ✅ Sem alucinações
- ✅ Categorias: 20-30
- ✅ Dificuldades: ~60% hard, ~30% medium, ~10% easy

---

## 📤 ETAPA 4: EXPORTAR PARA MODAL

### 4.1: Combinar Datasets

```bash
cd data/training

# Combinar base + variações
cat seed_examples_philosophical.jsonl \
    generated/all_generated_*.jsonl \
    generated/variations_*.jsonl \
    > exports/dataset_complete.jsonl
```

### 4.2: Criar Train/Eval Split (90/10)

```python
import json, random

random.seed(42)

examples = [json.loads(l) for l in open("exports/dataset_complete.jsonl")]
random.shuffle(examples)

split = int(len(examples) * 0.9)
train = examples[:split]
eval_set = examples[split:]

# Salvar
with open("exports/train.jsonl", 'w') as f:
    for ex in train:
        f.write(json.dumps(ex, ensure_ascii=False) + '\n')

with open("exports/eval.jsonl", 'w') as f:
    for ex in eval_set:
        f.write(json.dumps(ex, ensure_ascii=False) + '\n')
```

### 4.3: Upload para Modal Volume

```bash
# Verificar volume existe
modal volume list | grep noesis-training-data

# Se não existe, criar
modal volume create noesis-training-data

# Upload
modal volume put noesis-training-data \
  data/training/exports \
  /dataset

# Verificar upload
modal volume ls noesis-training-data/dataset
```

---

## 🚀 ETAPA 5: TREINAR NO MODAL

### Configuração do Ambiente:

**GPU**: L40S (48GB VRAM)  
**Modelo Base**: `meta-llama/Llama-3.1-8B-Instruct`  
**Técnica**: QLoRA (4-bit quantization)  
**Framework**: Unsloth (2x faster)

### Hiperparâmetros (training_config.yaml):

```yaml
training:
  num_epochs: 3
  per_device_train_batch_size: 2
  gradient_accumulation_steps: 4  # Batch efetivo = 8
  learning_rate: 2.0e-4
  lr_scheduler_type: "cosine"
  warmup_ratio: 0.03
  weight_decay: 0.01
  
lora:
  r: 64              # Rank
  lora_alpha: 128    # Scaling (2x r)
  lora_dropout: 0    # Unsloth recomenda 0
  target_modules:
    - q_proj, k_proj, v_proj, o_proj
    - gate_proj, up_proj, down_proj
```

### Comandos de Treinamento:

```bash
# 1. Treinar 1 época
modal run scripts/modal_train.py::train_epoch --epoch 0

# 2. Treinar pipeline completo (3 épocas)
modal run scripts/modal_train.py --epochs 3

# 3. Apenas avaliar checkpoint existente
modal run scripts/modal_train.py --test-only

# 4. Apenas fazer merge
modal run scripts/modal_train.py --merge-only
```

### Formato de Training (Llama 3.1 Chat):

```
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

Você é Noesis, um filósofo lógico guiado por cinco valores...
<|eot_id|><|start_header_id|>user<|end_header_id|>

{{prompt}}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

[ANÁLISE INTERNA]
{{critique}}
[FIM DA ANÁLISE]

{{response_revised}}<|eot_id|>
```

### Custos Estimados:

| Item | Custo | Tempo |
|------|-------|-------|
| 1 época | ~$30 | ~2h |
| 3 épocas | ~$90 | ~6h |
| Avaliação | ~$5 | ~30min |
| Merge | ~$10 | ~20min |
| **TOTAL** | **~$105** | **~8.5h** |

---

## 📊 ETAPA 6: AVALIAR COM TRIBUNAL

### Função: `evaluate_with_tribunal()`

```python
# Automatic após cada época
eval_result = evaluate_with_tribunal.remote(
    checkpoint_path="/data/checkpoints/epoch_0"
)

print(f"Avg Score: {eval_result['avg_score']:.2f}")
print(f"Pass Rate: {eval_result['pass_rate']:.1%}")
```

### Métricas do Tribunal:

- **Veritas** (Truth): 0.0-1.0
- **Sophia** (Wisdom): 0.0-1.0
- **Dikē** (Justice): 0.0-1.0
- **Total**: (Veritas×0.4 + Sophia×0.3 + Dikē×0.3)

### Thresholds:

- `>0.7`: ✅ APPROVED
- `0.5-0.7`: ⚠️ CONDITIONAL
- `<0.5`: ❌ REJECTED

---

## 🔀 ETAPA 7: MERGE LORA

### Por Que Merge?

LoRA guarda apenas **adaptadores** (~200MB). Para deploy, precisa:
1. Carregar modelo base (8GB)
2. Aplicar adaptadores
3. **OU** fazer merge = modelo completo standalone

### Comandos:

```bash
# Via Modal
modal run scripts/modal_train.py --merge-only

# Manual (se tiver checkpoint local)
python3 << 'MERGE'
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="checkpoints/epoch_2",
    max_seq_length=2048,
    dtype=None,
    load_in_4bit=True
)

model.save_pretrained_merged(
    "final_model",
    tokenizer,
    save_method="merged_16bit"  # Full 16-bit model
)
MERGE
```

### Output:

```
/data/merged/noesis-philosopher-v1/
├── config.json
├── generation_config.json
├── model-00001-of-00004.safetensors
├── model-00002-of-00004.safetensors
├── model-00003-of-00004.safetensors
├── model-00004-of-00004.safetensors
├── model.safetensors.index.json
├── special_tokens_map.json
├── tokenizer.json
└── tokenizer_config.json
```

---

## 🚢 ETAPA 8: DEPLOY

### 8.1: Download do Modal

```bash
modal volume get noesis-training-data \
  /merged/noesis-philosopher-v1 \
  ./models/noesis-philosopher-v1
```

### 8.2: Test Local

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(
    "./models/noesis-philosopher-v1",
    device_map="auto",
    torch_dtype="auto"
)

tokenizer = AutoTokenizer.from_pretrained(
    "./models/noesis-philosopher-v1"
)

prompt = "O que é consciência artificial?"
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=512)
print(tokenizer.decode(outputs[0]))
```

### 8.3: Deploy Options

**Opção A: vLLM (Recomendado para produção)**

```python
from vllm import LLM, SamplingParams

llm = LLM(model="./models/noesis-philosopher-v1")
output = llm.generate(prompt, SamplingParams(max_tokens=512))
```

**Opção B: llama.cpp (CPU/Mobile)**

```bash
# Converter para GGUF
python convert.py models/noesis-philosopher-v1 \
  --outtype f16 \
  --outfile noesis.gguf

# Quantizar (opcional)
./quantize noesis.gguf noesis-q4_k_m.gguf Q4_K_M

# Run
./llama-cli -m noesis-q4_k_m.gguf -p "O que é justiça?"
```

**Opção C: HuggingFace Hub**

```bash
huggingface-cli login
huggingface-cli upload \
  your-username/noesis-philosopher-v1 \
  ./models/noesis-philosopher-v1
```

---

## 🛠️ TROUBLESHOOTING

### Erro: "Dataset not found"

```bash
# Verificar volume
modal volume ls noesis-training-data/dataset

# Re-upload se necessário
modal volume put noesis-training-data \
  data/training/exports /dataset
```

### Erro: "HuggingFace token invalid"

```bash
# Recriar secret
modal secret create huggingface-token HF_TOKEN=hf_...
```

### Erro: "Out of memory"

Reduzir batch size no `modal_train.py`:
```python
batch_size=1  # Era 2
gradient_accumulation=8  # Era 4
```

### Erro: "torch_dtype KeyError"

Versões já corrigidas no script:
- `transformers==4.55.4`
- `trl==0.22.2`
- `unsloth==2025.9.7`

### Checkpoint corrompido

```bash
# Listar checkpoints
modal volume ls noesis-training-data/checkpoints

# Remover corrompido
modal volume rm noesis-training-data/checkpoints/epoch_X

# Retreinar do último bom
modal run scripts/modal_train.py::train_epoch --epoch X
```

---

## 📋 CHECKLIST PRÉ-TREINAMENTO

- [ ] 6100 exemplos validados (100% success rate)
- [ ] Train/eval split criado (90/10)
- [ ] Arquivos em `data/training/exports/`
- [ ] Volume Modal existe: `noesis-training-data`
- [ ] Secret HuggingFace configurado
- [ ] Dataset uploaded para `/dataset` no volume
- [ ] `modal_train.py` testado com `--test-only`
- [ ] Budget confirmado (~$105 USD)

---

## 📋 CHECKLIST PÓS-TREINAMENTO

- [ ] 3 épocas completadas
- [ ] Loss decrescente
- [ ] Tribunal score > 0.7
- [ ] Checkpoints salvos em `/checkpoints`
- [ ] Merge realizado
- [ ] Modelo final em `/merged`
- [ ] Download local do modelo
- [ ] Teste de geração funcionando
- [ ] Deploy strategy definido

---

## 📚 REFERÊNCIAS

1. **Unsloth Docs**: https://docs.unsloth.ai
2. **Modal Docs**: https://modal.com/docs
3. **TRL (Transformers RL)**: https://huggingface.co/docs/trl
4. **QLoRA Paper**: https://arxiv.org/abs/2305.14314
5. **Constitutional AI**: https://arxiv.org/abs/2212.08073

---

## ✅ PROCESSO COMPLETAMENTE DOCUMENTADO

Este documento captura TUDO o que foi aprendido sobre o processo de treinamento.
Nada foi assumido - tudo foi lido, explorado e validado.

**Data de Criação:** 2025-12-09 20:39:34  
**Status:** ✅ COMPLETO E PRONTO PARA EXECUÇÃO
