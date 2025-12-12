# 🚀 PLANO DE SCALING 50X - NOESIS BIG DATA

**Data:** 2025-12-10
**Custo Atual:** $3 (6.1K exemplos)
**Meta:** $150-200 (300K+ exemplos)
**Escala:** 50x

---

## 📊 ESTRATÉGIAS DE SCALING

### 1. DATASET SCALING (300K exemplos)

#### A. Self-Instruct + Evol-Instruct (150K exemplos)
```bash
# Usar Claude/GPT-4 para gerar variações
# Custo: ~$50 (API calls)

python scripts/generate_synthetic_data.py \
  --base-examples 600 \
  --target 150000 \
  --method evol-instruct \
  --model claude-3-opus
```

**Técnicas:**
- **Breadth Evolution:** Adicionar constraints, contextos
- **Depth Evolution:** Aumentar complexidade, raciocínio
- **In-Breadth Evol:** Criar cenários paralelos
- **Mutation:** Transformar formato (code→essay, dialogue→monologue)

#### B. Seed Data Diversification (100K exemplos)
```python
# Explorar novos domínios filosóficos
domains = [
    "Epistemologia Bayesiana",
    "Teoria dos Jogos Evolucionária", 
    "Fenomenologia Computacional",
    "Ética de IA Avançada",
    "Meta-filosofia da Ciência",
    "Lógica Paraconsistente",
    "Filosofia da Mente Conectada",
    "Neuroética Computacional"
]
```

#### C. Cross-Domain Knowledge (50K exemplos)
- Filosofia + Matemática Avançada
- Física Quântica + Consciência
- Biologia + Ética
- Economia + Teoria da Decisão
- História + Epistemologia

---

### 2. COMPUTE SCALING (GPU Upgrade)

#### Opção A: Multi-GPU Training
```yaml
# modal_train.py - Atualizar para DDP
gpu: "A100-80GB:4"  # 4x A100 (320GB VRAM)
batch_size: 8       # Por GPU = 32 efetivo
gradient_acc: 2     # Batch efetivo = 64
```

**Custo:** ~$12/hora × 4h = **$48**
**Throughput:** 8x faster

#### Opção B: H100 Single GPU
```yaml
gpu: "H100"  # 80GB, 3x faster que A100
batch_size: 4
gradient_acc: 8  # Batch = 32
```

**Custo:** ~$8/hora × 5h = **$40**
**Throughput:** 3x faster

---

### 3. MODEL SCALING (Larger Base Models)

#### Opção A: Llama-3.1-70B
```python
base_model = "meta-llama/Llama-3.1-70B-Instruct"
# Precisa: 4x A100 ou 2x H100
# QLoRA adapters: ~5GB
```

**Custo:** $80-120 para 3 épocas
**Ganho:** Capacidade 8x maior

#### Opção B: Mixtral 8x22B (MoE)
```python
base_model = "mistralai/Mixtral-8x22B-Instruct-v0.1"
# Sparse MoE: só ativa 2 experts por token
# Mais eficiente que dense
```

**Custo:** $60-100
**Ganho:** 22B params, eficiência de 3B

---

### 4. TRAINING OPTIMIZATION

#### A. Learning Rate Scheduling
```python
# Atual: Cosine simples
# Upgrade: Cosine with Warm Restarts

scheduler = CosineAnnealingWarmRestarts(
    optimizer,
    T_0=1000,      # Restart a cada 1000 steps
    T_mult=2,      # Dobrar período
    eta_min=1e-6   # LR mínimo
)
```

#### B. Curriculum Learning
```python
# Fase 1: Easy examples (epochs 0-1)
# Fase 2: Medium examples (epochs 2-4)
# Fase 3: Hard examples (epochs 5-7)
# Fase 4: Mix all (epochs 8-10)

# Resultado: Convergência mais rápida e estável
```

#### C. Mixed Precision + Flash Attention 2
```python
# Já usa bfloat16
# Upgrade: Flash Attention 2 (2x faster)

pip install flash-attn --no-build-isolation
model = FastLanguageModel.from_pretrained(
    ...,
    use_flash_attention_2=True  # ATIVAR!
)
```

---

## 💰 BUDGET BREAKDOWN (50x Scale)

| Item | Atual | 50x Scale | Custo |
|------|-------|-----------|-------|
| Dataset generation | Manual | API synthetic | $50 |
| Training compute | L40S 1h | H100 8h | $64 |
| Validation runs | 0 | 3 iterations | $20 |
| Merge + Export | $0 | Same | $2 |
| **TOTAL** | **$3** | **50x data+model** | **$136** |

---

## 🎯 EXECUTION PLAN

### Phase 1: Data Generation (1 week)
```bash
# Dia 1-2: Evol-Instruct 100K
python scripts/generate_evol_instruct.py --target 100000

# Dia 3-4: Cross-domain 50K  
python scripts/generate_cross_domain.py --domains 8

# Dia 5-7: Quality filtering + validation
python scripts/validate_dataset.py --min-score 0.9
```

### Phase 2: Training Setup (2 days)
```bash
# Configurar H100 ou 4x A100
# Testar com subset 10K
# Ajustar hyperparameters
```

### Phase 3: Full Training (1 day)
```bash
# Upload 300K dataset para Modal
modal volume put noesis-training-data data/big/train.jsonl /dataset

# Run com H100
modal run --detach scripts/modal_train_big.py \
  --epochs 10 \
  --batch-size 4 \
  --gradient-accumulation 8
```

### Phase 4: Evaluation (1 day)
```bash
# Tribunal evaluation em test set 10K
# Human evaluation em 100 amostras
# Comparar com base model
```

---

## 📈 EXPECTED RESULTS

### Métricas Esperadas:

| Métrica | 6K Dataset | 300K Dataset |
|---------|------------|--------------|
| Loss | 0.029 | **0.008-0.015** |
| Tribunal Score | ~0.75 | **0.85-0.90** |
| Perplexity | ~1.5 | **~1.2** |
| Profundidade | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### Capacidades Emergentes:
- ✅ Multi-step reasoning (3+ steps)
- ✅ Self-correction automática
- ✅ Meta-cognição explícita
- ✅ Transfer learning cross-domain
- ✅ Few-shot adaptation

---

## 🛠️ TOOLS & SCRIPTS NEEDED

### 1. Synthetic Data Generator
```python
# scripts/generate_synthetic_big.py
- Evol-Instruct pipeline
- Quality scoring (Tribunal)
- Deduplication
- Format validation
```

### 2. Distributed Training Script  
```python
# scripts/modal_train_distributed.py
- Multi-GPU DDP
- Gradient checkpointing
- Mixed precision
- Monitoring & alerts
```

### 3. Evaluation Suite
```python
# scripts/evaluate_comprehensive.py
- Tribunal batch scoring
- Perplexity calculation
- Human eval interface
- A/B testing framework
```

---

## ⚠️ RISKS & MITIGATIONS

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Overfitting (300K) | Média | Alto | Early stopping, validation |
| Cost overrun | Baixa | Médio | Budget alerts, spot instances |
| Quality degradation | Média | Alto | Aggressive filtering (>0.9) |
| Homogenization | Alta | Médio | Diverse sources, temperature |

---

## 🚀 QUICK START (Começar Agora)

```bash
# 1. Gerar primeiro lote (10K exemplos)
cd /media/juan/DATA/projetos/Noesis/Daimon
python scripts/generate_evol_instruct.py \
  --input data/training/seed_examples_philosophical.jsonl \
  --output data/training/big/batch_1.jsonl \
  --count 10000 \
  --model claude-sonnet-3.5

# 2. Validar
python scripts/validate_dataset.py data/training/big/batch_1.jsonl

# 3. Upload para Modal
modal volume put noesis-training-data \
  data/training/big/batch_1.jsonl \
  /dataset/big/

# 4. Test run com H100
modal run scripts/modal_train.py::train_epoch \
  --epoch 0 \
  --gpu H100 \
  --batch-size 4
```

---

## 📚 REFERENCES

- **Evol-Instruct:** https://arxiv.org/abs/2304.12244
- **Self-Instruct:** https://arxiv.org/abs/2212.10560
- **Constitutional AI:** https://arxiv.org/abs/2212.08073
- **RLHF at Scale:** https://arxiv.org/abs/2203.02155

---

**STATUS:** 📋 PLANO COMPLETO - PRONTO PARA EXECUÇÃO
**NEXT:** Implementar `generate_evol_instruct.py`
