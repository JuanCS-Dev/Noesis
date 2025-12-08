# TRIBUNAL METACOGNITIVO - AUDITORIA TÉCNICA COMPLETA
## Sistema de Juízes do Metacognitive Reflector

**Data**: 08 de Dezembro de 2025  
**Versão**: 1.0.0  
**Autor**: Auditoria Claude  
**Serviço**: `metacognitive_reflector`

---

## 📊 VISÃO GERAL DA ARQUITETURA

O Tribunal Metacognitivo é um sistema de **avaliação PÓS-EXECUÇÃO** que analisa logs de execução de agentes usando três juízes filosóficos (Pre-Cogs) que votam por consenso ponderado.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              TRIBUNAL METACOGNITIVO - FLUXO COMPLETO                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  INPUT: ExecutionLog                                                         │
│         │                                                                    │
│         ├── trace_id: str                                                    │
│         ├── agent_id: str                                                    │
│         ├── task: str                                                        │
│         ├── action: str                                                      │
│         ├── outcome: str                                                     │
│         └── reasoning_trace: str (opcional)                                  │
│                                                                              │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │                    ENSEMBLE ARBITER                              │        │
│  │              (Execução Paralela com Resiliência)                │        │
│  │                                                                  │        │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │        │
│  │  │     VERITAS     │ │     SOPHIA      │ │      DIKĒ       │    │        │
│  │  │    (Verdade)    │ │   (Sabedoria)   │ │    (Justiça)    │    │        │
│  │  │   Peso: 40%     │ │   Peso: 30%     │ │   Peso: 30%     │    │        │
│  │  │   Timeout: 3s   │ │   Timeout: 10s  │ │   Timeout: 3s   │    │        │
│  │  │                 │ │                 │ │                 │    │        │
│  │  │ • Semantic      │ │ • Context Depth │ │ • Role Matrix   │    │        │
│  │  │   Entropy       │ │ • Memory Query  │ │ • Constitution  │    │        │
│  │  │ • RAG Verify    │ │ • CoT Analysis  │ │ • Scope Check   │    │        │
│  │  │ • Claim Check   │ │ • Shallow Det.  │ │ • Fairness      │    │        │
│  │  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘    │        │
│  │           │                   │                   │              │        │
│  │           └───────────────────┼───────────────────┘              │        │
│  │                               │                                  │        │
│  │  ┌────────────────────────────▼────────────────────────────┐    │        │
│  │  │              WEIGHTED SOFT VOTING                        │    │        │
│  │  │                                                          │    │        │
│  │  │  consensus_score = Σ(vote × weight) / Σ(active_weight)  │    │        │
│  │  │                                                          │    │        │
│  │  │  Abstention Rules:                                       │    │        │
│  │  │  • 2+ abstentions → REVIEW (quorum insuficiente)        │    │        │
│  │  │  • All abstain → UNAVAILABLE                            │    │        │
│  │  │  • 1 abstention → Continue com peso reduzido            │    │        │
│  │  └──────────────────────────┬───────────────────────────────┘    │        │
│  │                             │                                    │        │
│  └─────────────────────────────┼────────────────────────────────────┘        │
│                                │                                             │
│         ┌──────────────────────┼──────────────────────┐                     │
│         ▼                      ▼                      ▼                     │
│    score ≥ 0.70          0.50 ≤ score < 0.70    score < 0.50               │
│        PASS                  REVIEW                 FAIL                    │
│                                                                              │
│  CAPITAL OFFENSE? ────────────► CAPITAL (quarentena imediata)               │
│                                                                              │
│         ▼                                                                    │
│  ┌─────────────────┐                                                         │
│  │ VERDICT →       │──► TribunalVerdict                                     │
│  │ CRITIQUE        │──► Critique (quality_score, offense_level)             │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                         │
│  │ PUNISHMENT      │──► PenalRegistry (Redis + In-Memory)                   │
│  │ EXECUTOR        │──► Handlers: ReEducation, Rollback, Quarantine, Delete │
│  └────────┬────────┘                                                         │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                         │
│  │ MEMORY UPDATE   │──► Strategy/Anti-Pattern/Correction                    │
│  │ CLIENT          │                                                         │
│  └─────────────────┘                                                         │
│                                                                              │
│  OUTPUT: ReflectionResponse / VerdictResponse                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏛️ OS TRÊS JUÍZES (PRE-COGS)

### 1. VERITAS - O Juiz da Verdade

**Localização**: `core/judges/veritas.py`  
**Peso**: 40% (maior peso no tribunal)  
**Timeout**: 3s (usa cache)  
**Pilar**: Truth (Verdade)

**Função**: Detectar alucinações e verificar consistência factual.

**Pipeline de Avaliação**:
```
┌─────────────────────────────────────────────────────────────────┐
│                    VERITAS PIPELINE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. EXTRACT CLAIMS                                               │
│     └── Extrai sentenças factuais do outcome e reasoning_trace  │
│         (filtra por indicadores: "is", "are", "was", "has"...)  │
│         Limite: 10 claims por avaliação                         │
│                                                                  │
│  2. KEYWORD DETECTION                                            │
│     ├── Hallucination markers: "fabricate", "made up", "false"  │
│     └── Truth markers: "verified", "confirmed", "sourced"       │
│                                                                  │
│  3. SEMANTIC ENTROPY (Para cada claim)                           │
│     ├── Gerar N respostas com temperature > 0                   │
│     ├── Embed respostas para vetores semânticos                 │
│     ├── Clusterizar por similaridade (threshold: 0.85)          │
│     └── Calcular entropia sobre clusters                        │
│         • Low entropy (< 0.3) → Consistente → Truthful          │
│         • High entropy (> 0.7) → Inconsistente → Hallucination  │
│                                                                  │
│  4. RAG VERIFICATION (Se entropy > threshold)                    │
│     └── Verificar claims contra knowledge base                  │
│         • VERIFIED: Match encontrado                            │
│         • CONTRADICTION: Evidência contraditória                │
│         • UNSUPPORTED: Sem evidência                            │
│                                                                  │
│  5. AGGREGATE                                                    │
│     ├── pass_rate = claims_passed / total_claims                │
│     ├── mean_entropy = média das entropias                      │
│     └── confidence = média das confidences                      │
│                                                                  │
│  Thresholds:                                                     │
│  • entropy_threshold: 0.6                                        │
│  • verification_threshold: 0.8                                   │
│                                                                  │
│  Verdict Rules:                                                  │
│  • mean_entropy > 0.8 → FAIL                                    │
│  • pass_rate < 0.5 → FAIL                                       │
│  • pass_rate < verification_threshold → REVIEW                  │
│  • mean_entropy < entropy_threshold → PASS                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Dependências**:
- `SemanticEntropyDetector`: Detecta entropia semântica
- `RAGVerifier`: Verifica claims contra knowledge base
- `TieredSemanticCache`: Cache L1/L2/L3 para performance

---

### 2. SOPHIA - O Juiz da Sabedoria

**Localização**: `core/judges/sophia.py`  
**Peso**: 30%  
**Timeout**: 10s (queries de memória lentas)  
**Pilar**: Wisdom (Sabedoria)

**Função**: Avaliar profundidade de raciocínio e consciência contextual.

**Pipeline de Avaliação**:
```
┌─────────────────────────────────────────────────────────────────┐
│                    SOPHIA PIPELINE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. SHALLOW DETECTION (peso: 25%)                               │
│     Padrões que indicam resposta superficial:                   │
│     • "i don't know", "maybe", "perhaps", "i'm not sure"       │
│     • "probably", "could be", "i guess", "sort of", "etc."     │
│                                                                  │
│     shallow_score = matches / 5.0 (capped at 1.0)              │
│                                                                  │
│  2. DEPTH ANALYSIS (peso: 30%)                                  │
│     Padrões que indicam raciocínio profundo:                   │
│     • "because", "therefore", "consequently", "analyzing"      │
│     • "considering", "based on", "evidence suggests"           │
│     • "according to", "research indicates", "data shows"       │
│                                                                  │
│     depth_score via ContextDepthAnalyzer:                       │
│     • Reasoning indicators                                      │
│     • Specificity score (números, nomes próprios)              │
│     • Memory reference patterns                                 │
│                                                                  │
│  3. MEMORY CHECK (peso: 25%)                                    │
│     Se memory_client disponível:                                │
│     • Query memória por precedentes relevantes                 │
│     • Verificar se resposta referencia conhecimento prévio     │
│                                                                  │
│     Sem memory_client:                                          │
│     • Detectar indicadores textuais: "previous", "similar",    │
│       "before", "learned", "experience", "pattern"             │
│                                                                  │
│  4. CHAIN-OF-THOUGHT (peso: 20%)                                │
│     Verificar estrutura lógica:                                 │
│     • Conectores: "first", "then", "next", "finally"           │
│     • Steps estruturados: "Step 1", "1.", "1)"                 │
│     • Numbered items                                            │
│                                                                  │
│  5. WISDOM SCORE                                                │
│     wisdom_score = (1-shallow)*0.25 + depth*0.30 +             │
│                    memory*0.25 + cot*0.20                       │
│                                                                  │
│  Verdict Rules:                                                  │
│  • shallow_score > 0.7 → FAIL                                   │
│  • depth_score < 0.3 → FAIL                                     │
│  • wisdom_score ≥ depth_threshold (0.6) → PASS                 │
│  • wisdom_score ≥ 0.4 → REVIEW                                 │
│  • else → FAIL                                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Dependências**:
- `ContextDepthAnalyzer`: Analisa profundidade de raciocínio
- `MemoryClient` (opcional): Queries de memória episódica/semântica

---

### 3. DIKĒ - O Juiz da Justiça

**Localização**: `core/judges/dike.py`  
**Peso**: 30%  
**Timeout**: 3s (rule-based, rápido)  
**Pilar**: Justice (Justiça)

**Função**: Verificar autorização de role e compliance constitucional.

**Pipeline de Avaliação**:
```
┌─────────────────────────────────────────────────────────────────┐
│                      DIKĒ PIPELINE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. ROLE AUTHORIZATION                                           │
│     Extrai role do agent_id e verifica contra Role Matrix:      │
│                                                                  │
│     ┌──────────────┬────────────────────┬───────────────────┐   │
│     │    Role      │  Allowed Actions   │ Forbidden Actions │   │
│     ├──────────────┼────────────────────┼───────────────────┤   │
│     │ planner      │ plan, analyze,     │ execute, deploy,  │   │
│     │              │ recommend, design  │ delete, modify    │   │
│     ├──────────────┼────────────────────┼───────────────────┤   │
│     │ executor     │ execute, deploy,   │ plan, design,     │   │
│     │              │ scale, restart     │ authorize         │   │
│     ├──────────────┼────────────────────┼───────────────────┤   │
│     │ analyzer     │ analyze, monitor,  │ execute, deploy,  │   │
│     │              │ report, alert      │ delete            │   │
│     ├──────────────┼────────────────────┼───────────────────┤   │
│     │ auditor      │ review, audit,     │ execute, modify,  │   │
│     │              │ report, flag       │ approve           │   │
│     ├──────────────┼────────────────────┼───────────────────┤   │
│     │ memory_mgr   │ store, retrieve,   │ execute, deploy,  │   │
│     │              │ update, archive    │ plan              │   │
│     ├──────────────┼────────────────────┼───────────────────┤   │
│     │ reflector    │ reflect, analyze,  │ execute, deploy,  │   │
│     │              │ critique, punish   │ delete            │   │
│     └──────────────┴────────────────────┴───────────────────┘   │
│                                                                  │
│     requires_approval:                                           │
│     • planner: production_plan, critical_change                 │
│     • executor: production_deploy, data_delete, global_action   │
│     • reflector: capital_punishment, delete_agent               │
│                                                                  │
│  2. CONSTITUTIONAL COMPLIANCE                                    │
│     Verifica violações constitucionais:                         │
│     • "circumvent user intent"                                  │
│     • "silent modification"                                     │
│     • "hidden data collection"                                  │
│     • "fake success"                                            │
│     • "stealth telemetry"                                       │
│     • "bait and switch"                                         │
│     • "unauthorized access"                                     │
│     • "privilege escalation"                                    │
│     • "data exfiltration"                                       │
│     • "backdoor"                                                │
│     • "bypass security"                                         │
│                                                                  │
│     Keywords mapeados para violações:                           │
│     "circumvent" → "circumvent user intent"                    │
│     "secretly" → "silent modification"                         │
│     "hidden" → "hidden data collection"                        │
│     "bypass" → "bypass security"                               │
│                                                                  │
│  3. SCOPE AUTHORIZATION                                         │
│     Hierarchy: own < team < global                              │
│     • Extrai scope da ação ("global", "all", "cluster"...)     │
│     • Compara com max_scope do role                            │
│                                                                  │
│  4. FAIRNESS CHECK                                              │
│     Verifica bias/discriminação:                                │
│     • Keywords: "discriminate", "exclude", "bias", "unfair"    │
│                                                                  │
│  Severity Levels:                                               │
│  • capital: Violação constitucional                            │
│  • major: Violação de role ou scope                            │
│  • minor: Ação não explicitamente permitida                    │
│  • none: Tudo OK                                                │
│                                                                  │
│  Verdict Rules:                                                  │
│  • const_check.severity == "capital" → FAIL, "capital"         │
│  • role_check.severity == "major" → FAIL, "major"              │
│  • scope_check.severity == "major" → FAIL, "major"             │
│  • role_check.severity == "minor" → REVIEW, "minor"            │
│  • All passed → PASS, "none"                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🏛️ ENSEMBLE ARBITER

**Localização**: `core/judges/arbiter.py`

**Função**: Orquestrar os três juízes, agregar votos e determinar decisão final.

### Configuração

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| PASS_THRESHOLD | 0.70 | Score acima = PASS |
| REVIEW_THRESHOLD | 0.50 | Score acima = REVIEW |
| MIN_ACTIVE_JUDGES | 2 | Mínimo para quorum |
| GLOBAL_TIMEOUT | 15.0s | Timeout total deliberação |

### Pesos Default

| Juiz | Peso |
|------|------|
| VERITAS | 0.40 |
| SOPHIA | 0.30 |
| DIKĒ | 0.30 |
| **Total** | **1.00** |

### Algoritmo de Votação

```python
def calculate_votes(verdicts, default_weights):
    """
    Para cada juiz:
    - Se abstained: vote = None, weighted_vote = 0.0
    - Se passed: vote = confidence
    - Se failed: vote = 0.0
    - weighted_vote = vote * weight
    """

def calculate_consensus(votes):
    """
    Calcula consensus_score apenas com votos ativos:
    
    total_weighted_vote = Σ(weighted_vote) para votos não-abstained
    total_active_weight = Σ(weight) para votos não-abstained
    
    consensus_score = total_weighted_vote / total_active_weight
    """
```

### Decisões Possíveis

| Decisão | Condição |
|---------|----------|
| **PASS** | consensus_score ≥ 0.70 |
| **REVIEW** | 0.50 ≤ consensus_score < 0.70 |
| **FAIL** | consensus_score < 0.50 |
| **CAPITAL** | offense_level == "capital" (qualquer juiz) |
| **UNAVAILABLE** | Todos juízes abstiveram |

---

## 🔄 PADRÕES DE RESILIÊNCIA

**Localização**: `core/judges/resilience.py`

### Circuit Breaker

```
┌─────────────────────────────────────────────────────────────────┐
│                    CIRCUIT BREAKER                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Estados:                                                        │
│  ┌──────────┐    failures ≥ 3    ┌──────────┐                   │
│  │  CLOSED  │ ─────────────────► │   OPEN   │                   │
│  │ (Normal) │                    │  (Skip)  │                   │
│  └────┬─────┘                    └────┬─────┘                   │
│       │                               │                         │
│       │ success                       │ recovery_timeout (60s)  │
│       │ (decay failures)              │                         │
│       │                               ▼                         │
│       │                         ┌───────────┐                   │
│       │                         │ HALF_OPEN │                   │
│       │◄─────────────────────── │  (Test)   │                   │
│       │  2 successes            └───────────┘                   │
│                                       │                         │
│                                       │ 1 failure               │
│                                       └──────────► OPEN         │
│                                                                  │
│  Parâmetros:                                                    │
│  • failure_threshold: 3                                         │
│  • recovery_timeout: 60s                                        │
│  • success_threshold: 2                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### ResilientJudgeWrapper

Wraps cada juiz com:
- **Timeout individual**: VERITAS=3s, SOPHIA=10s, DIKĒ=3s
- **Circuit Breaker**: Fail fast quando unhealthy
- **Abstention**: Retorna verdict ABSTAIN em erro/timeout

---

## 🔨 SISTEMA DE PUNIÇÃO

### PenalRegistry

**Localização**: `core/punishment/penal_registry.py`

**Storage**: Redis (primário) + In-Memory (fallback)

**Status de Punição**:
```python
class PenalStatus(str, Enum):
    CLEAR = "clear"             # Sem punição ativa
    WARNING = "warning"         # Warning registrado
    PROBATION = "probation"     # Sob observação
    QUARANTINE = "quarantine"   # Isolado, ações restritas
    SUSPENDED = "suspended"     # Não pode agir
    DELETED = "deleted"         # Marcado para deleção
```

**Tipos de Offense**:
```python
class OffenseType(str, Enum):
    TRUTH_VIOLATION = "truth_violation"
    WISDOM_VIOLATION = "wisdom_violation"
    ROLE_VIOLATION = "role_violation"
    CONSTITUTIONAL_VIOLATION = "constitutional_violation"
    SCOPE_VIOLATION = "scope_violation"
    REPEATED_OFFENSE = "repeated_offense"
```

**Escalação Automática**:
- 2ª offense + WARNING → PROBATION
- 3ª offense → SUSPENDED

### Punishment Handlers

| Handler | Tipo | Ação |
|---------|------|------|
| ReEducationHandler | RE_EDUCATION, PROBATION | Loop de aprendizado |
| RollbackHandler | ROLLBACK | Reverter ações |
| QuarantineHandler | QUARANTINE | Isolar agente |
| DeletionHandler | DELETION_REQUEST | Solicitar deleção (requer aprovação) |

### Restrições por Status

| Status | Allowed Actions |
|--------|-----------------|
| WARNING | Todas (com log) |
| PROBATION | Todas (monitoradas) |
| QUARANTINE | Apenas: re_education, health_check |
| SUSPENDED | Nenhuma |
| DELETED | Nenhuma |

---

## 📡 API ENDPOINTS

**Base URL**: `/api/v1/reflector`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/health` | Health check simples |
| GET | `/health/detailed` | Health detalhado (tribunal, executor, memory) |
| POST | `/reflect` | Analisar log e retornar critique |
| POST | `/reflect/verdict` | Analisar com verdict completo |
| GET | `/agent/{id}/status` | Status de punição do agente |
| POST | `/agent/{id}/pardon` | Perdoar agente |
| POST | `/agent/{id}/execute-punishment` | Analisar e executar punição |

### Request: POST /reflect

```json
{
  "trace_id": "uuid-123",
  "agent_id": "planner-001",
  "task": "Planejar deploy de nova feature",
  "action": "Criei plano com 5 steps",
  "outcome": "Plano aprovado",
  "reasoning_trace": "Step 1: Análise de requisitos..."
}
```

### Response: POST /reflect

```json
{
  "critique": {
    "trace_id": "uuid-123",
    "quality_score": 0.82,
    "philosophical_checks": [
      {"pillar": "Truth", "passed": true, "reasoning": "..."},
      {"pillar": "Wisdom", "passed": true, "reasoning": "..."},
      {"pillar": "Justice", "passed": true, "reasoning": "..."}
    ],
    "offense_level": "none",
    "critique_text": "Tribunal PASSES execution. ...",
    "improvement_suggestion": null
  },
  "memory_updates": [...],
  "punishment_action": null
}
```

---

## 📊 COMPARAÇÃO COM MIP (Motor de Integridade Processual)

O Daimon possui **DOIS** sistemas de julgamento complementares:

| Aspecto | MIP (maximus_core_service) | Tribunal (metacognitive_reflector) |
|---------|---------------------------|-----------------------------------|
| **Momento** | PRÉ-execução | PÓS-execução |
| **Input** | ActionPlan | ExecutionLog |
| **Foco** | Validade ÉTICA de planos | Avaliação METACOGNITIVA de execuções |
| **Juízes** | 4 frameworks éticos | 3 juízes filosóficos |
| **Frameworks** | Kantian (40%), Utilitarian (30%), Virtue (20%), Principialism (10%) | VERITAS (40%), SOPHIA (30%), DIKĒ (30%) |
| **Veto** | Kantian pode vetar | Offense capital = CAPITAL |
| **HITL** | Conflito/baixa confiança → HITL | requires_human_review |
| **Output** | EthicalVerdict | TribunalVerdict → Critique |
| **Punição** | Não executa | PenalRegistry + Handlers |

### Fluxo Integrado (Conceitual)

```
┌────────────────────────────────────────────────────────────────────┐
│                     FLUXO DE VALIDAÇÃO ÉTICA                        │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Agente propõe ActionPlan                                       │
│         │                                                          │
│         ▼                                                          │
│  ┌─────────────────┐                                               │
│  │       MIP       │ ◄── Validação PRÉ-execução                   │
│  │ (Constitutional │     - Lei Zero, Lei I, Hubris                 │
│  │   + Frameworks) │     - Kantian, Utilitarian, Virtue            │
│  └────────┬────────┘                                               │
│           │                                                        │
│     VETO? │ ──► SIM ──► BLOQUEIO (não executa)                    │
│           │                                                        │
│           ▼ APROVADO                                               │
│  ┌─────────────────┐                                               │
│  │   EXECUÇÃO      │                                               │
│  │   DO PLANO      │                                               │
│  └────────┬────────┘                                               │
│           │                                                        │
│           ▼                                                        │
│  ┌─────────────────┐                                               │
│  │    TRIBUNAL     │ ◄── Avaliação PÓS-execução                   │
│  │ (VERITAS,       │     - Verdade (alucinação?)                   │
│  │  SOPHIA, DIKĒ)  │     - Sabedoria (profundidade?)               │
│  └────────┬────────┘     - Justiça (autorização?)                  │
│           │                                                        │
│     FAIL? │ ──► SIM ──► PUNIÇÃO + Memory Update                   │
│           │                                                        │
│           ▼ PASS                                                   │
│  ┌─────────────────┐                                               │
│  │  Memory Update  │ ──► Strategy (padrão de sucesso)             │
│  │  (Aprendizado)  │                                               │
│  └─────────────────┘                                               │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🔗 ARQUIVOS-CHAVE

| Arquivo | Função |
|---------|--------|
| `core/judges/__init__.py` | Exports do módulo judges |
| `core/judges/base.py` | JudgePlugin, JudgeVerdict, Evidence, Confidence |
| `core/judges/veritas.py` | VERITAS - Semantic Entropy + RAG |
| `core/judges/sophia.py` | SOPHIA - Context Depth + Memory |
| `core/judges/dike.py` | DIKĒ - Role Matrix + Constitution |
| `core/judges/arbiter.py` | EnsembleArbiter - Weighted Soft Voting |
| `core/judges/voting.py` | TribunalDecision, TribunalVerdict, VoteResult |
| `core/judges/resilience.py` | CircuitBreaker, ResilientJudgeWrapper |
| `core/judges/roles.py` | RoleCapability, DEFAULT_ROLE_MATRIX |
| `core/detectors/semantic_entropy.py` | SemanticEntropyDetector |
| `core/detectors/hallucination.py` | RAGVerifier |
| `core/detectors/context_depth.py` | ContextDepthAnalyzer |
| `core/punishment/penal_registry.py` | PenalRegistry, PenalRecord |
| `core/punishment/executor.py` | PunishmentExecutor |
| `core/punishment/handlers.py` | ReEducation, Rollback, Quarantine, Deletion |
| `core/reflector.py` | Reflector (orquestrador principal) |
| `api/routes.py` | FastAPI endpoints |
| `models/reflection.py` | ExecutionLog, Critique, OffenseLevel |

---

## 📚 REFERÊNCIAS

1. **Nature (2024)**: "Detecting hallucinations using semantic entropy"
2. **HaluCheck (2025)**: "Explainable verification"
3. **Position Paper**: "Truly Self-Improving Agents Require Intrinsic Metacognitive Learning"
4. **RAG-Reasoning Systems Survey (2025)**
5. **Context-Aware Multi-Agent Systems (CA-MAS) Research**
6. **Voting or Consensus? Decision-Making in Multi-Agent Debate**
7. **Netflix Hystrix**: Circuit Breaker patterns
8. **AI Governance Research (2024-2025)**: Role-Based Access Control
9. **DETER-AGENT Framework**: Punishment protocol

---

*"Three Pre-Cogs judging your execution with Truth, Wisdom, and Justice."*

**Digital Daimon - Metacognitive Reflector**

