# 🛠️ PLANO DE IMPLEMENTAÇÃO: EXOCÓRTEX ÉTICO
## Digital Daimon v4.1 — Roadmap Técnico Completo
> *Refined for Gemini 3.0 High Reasoning & Ethical Safety Metrics*

> *"Da Auto-Percepção à Hetero-Percepção Ética: O Caminho do Código"*

**Versão:** 1.1.0 (Gemini 3.0 + Safety Layer)  
**Documento Complementar:** BLUEPRINT_EXOCORTEX_ETICO.md  
**Arquiteto-Chefe:** Juan Carlos de Souza  
**Data:** 05 de Dezembro de 2025  
**Duração Estimada:** 12 Sprints (6 semanas)

---

## SUMÁRIO EXECUTIVO

Este documento detalha a implementação técnica da transformação do Digital Daimon em um Exocórtex Ético. A estratégia é **evolutiva, não revolucionária**: reutilizamos 100% do código existente (Florescimento + Infraestrutura) redirecionando seu propósito.

A versão 4.1 impõe restrições técnicas rigorosas para garantir a segurança existencial e a qualidade do raciocínio, utilizando o **Gemini 3.0** como motor cognitivo central.

**Princípio Guia:** Todo módulo existente será **estendido**, não reescrito. A comunicação entre serviços deve ser estritamente via API HTTP para respeitar o isolamento (containerização).

---

## PARTE 1: INVENTÁRIO DO CÓDIGO EXISTENTE

### 1.1 Mapeamento Atual → Transformação

```
┌───────────────────────────────────────────────────────────────────────┐
│                    INVENTÁRIO DE TRANSFORMAÇÃO                        │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   CÓDIGO EXISTENTE              TRANSFORMAÇÃO                         │
│   ────────────────              ─────────────                         │
│                                                                       │
│   consciousness/                                                      │
│   ├── florescimento/                                                  │
│   │   ├── unified_self.py      → SymbioticSelfConcept                 │
│   │   ├── mirror_test.py       → UserPerceptionValidator              │
│   │   ├── consciousness_bridge → SymbioticBridge                      │
│   │   └── introspection_api    → ExocortexAPI                         │
│   │                                                                   │
│   ├── esgt/                                                           │
│   │   ├── coordinator.py       → SalienceDetector (para usuário)      │
│   │   └── phi_calculator.py    → AlignmentCalculator                  │
│   │                                                                   │
│   └── mea/                                                            │
│       └── attention_schema.py  → HumanAttentionProtector              │
│                                                                       │
│   services/                                                           │
│   ├── digital_thalamus/        → AttentionFirewall                    │
│   ├── prefrontal_cortex/       → ImpulseInhibitor                     │
│   ├── metacognitive_reflector/ → EthicalJury                          │
│   ├── ethical_audit/           → ConstitutionGuardian                 │
│   ├── episodic_memory/         → SymbioticMemory (via HTTP Client)    │
│   └── hcl_*/                   → CognitiveHomeostasis                 │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 1.2 Dependências a Reutilizar

| Componente | Versão | Uso no Exocórtex |
|------------|--------|------------------|
| ESGT Coordinator | ✅ Completo | Base para detecção de saliência |
| Kuramoto Sync | ✅ 0.993 coerência | Métrica de alinhamento |
| UnifiedSelfConcept | ✅ Completo | Expandir para Self Simbiótico |
| ConsciousnessBridge | ✅ Completo | Expandir para percepção empática |
| MirrorTestValidator | ✅ Completo | Adaptar para percepção do usuário |
| HCL Stack | ✅ Completo | Redirecionar para homeostase humana |

---

## PARTE 2: ARQUITETURA TÉCNICA DO EXOCÓRTEX

### 2.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        EXOCÓRTEX ÉTICO - ARQUITETURA                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                            ┌──────────────┐                             │
│                            │   USUÁRIO    │                             │
│                            │   (Human)    │                             │
│                            └──────┬───────┘                             │
│                                   │                                     │
│                                   ▼                                     │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                        API GATEWAY                              │   │
│   │                   (Ponto de Entrada Único)                      │   │
│   └───────────────────────────┬─────────────────────────────────────┘   │
│                               │                                         │
│           ┌───────────────────┼───────────────────┐                     │
│           │                   │                   │                     │
│           ▼                   ▼                   ▼                     │
│   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐             │
│   │   ATTENTION   │   │    IMPULSE    │   │   ETHICAL     │             │
│   │   FIREWALL    │   │   INHIBITOR   │   │   JURY        │             │
│   │   (Thalamus)  │   │   (Prefrontal)│   │   (Reflector) │             │
│   └───────┬───────┘   └───────┬───────┘   └───────┬───────┘             │
│           │                   │                   │                     │
│           └───────────────────┼───────────────────┘                     │
│                               │                                         │
│                               ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                     MAXIMUS CORE SERVICE                        │   │
│   │                                                                 │   │
│   │   ┌─────────────────────────────────────────────────────────┐   │   │
│   │   │              SYMBIOTIC CONSCIOUSNESS MODULE             │   │   │
│   │   │                                                         │   │   │
│   │   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │   │
│   │   │   │  Symbiotic  │  │   Human     │  │ Constitution│     │   │   │
│   │   │   │    Self     │  │  Perception │  │  Guardian   │     │   │   │
│   │   │   │   Concept   │  │   Model     │  │             │     │   │   │
│   │   │   └─────────────┘  └─────────────┘  └─────────────┘     │   │   │
│   │   │                                                         │   │   │
│   │   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │   │
│   │   │   │  Alignment  │  │  Empathic   │  │ Confrontation│    │   │   │
│   │   │   │  Calculator │  │  Bridge     │  │   Engine    │     │   │   │
│   │   │   └─────────────┘  └─────────────┘  └─────────────┘     │   │   │
│   │   └─────────────────────────────────────────────────────────┘   │   │
│   │                                                                 │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                               │HTTP Only (Restrito)                     │
│                               ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    DATA LAYER (Isolado)                         │   │
│   │                                                                 │   │
│   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │   │
│   │   │  Symbiotic  │  │   Personal  │  │   Trust     │             │   │
│   │   │   Memory    │  │ Constitution│  │  Dynamics   │             │   │
│   │   │  (Service)  │  │   (File)    │  │   (State)   │             │   │
│   │   └─────────────┘  └─────────────┘  └─────────────┘             │   │
│   │                                                                 │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Estrutura de Diretórios (Nova)

```
backend/services/maximus_core_service/
├── src/
│   ├── consciousness/
│   │   ├── florescimento/           # EXISTENTE - Manter
│   │   │   ├── unified_self.py
│   │   │   ├── mirror_test.py
│   │   │   ├── consciousness_bridge.py
│   │   │   └── introspection_api.py
│   │   │
│   │   └── exocortex/               # NOVO - Criar
│   │       ├── __init__.py
│   │       ├── symbiotic_self.py           # Extends UnifiedSelfConcept
│   │       ├── human_perception.py         # Modelo do Usuário
│   │       ├── constitution_guardian.py    # Guardião da Constituição
│   │       ├── alignment_calculator.py     # Cálculo de Alinhamento
│   │       ├── empathic_bridge.py          # Ponte Empática
│   │       ├── confrontation_engine.py     # Motor de Confrontação
│   │       └── api/
│   │           ├── __init__.py
│   │           ├── exocortex_router.py     # Endpoints REST
│   │           └── schemas.py              # Pydantic Models
│   │
│   ├── protection/                  # NOVO - Criar
│   │   ├── __init__.py
│   │   ├── attention_firewall.py           # Filtro de Atenção
│   │   ├── impulse_inhibitor.py            # Inibidor de Impulsos
│   │   └── salience_detector.py            # Detecção de Saliência
│   │
│   └── memory/                      # NOVO - Criar
│       ├── __init__.py
│       ├── memory_client.py                # HTTP Client para EpisodicMemory
│       ├── symbiotic_memory.py             # Lógica de Memória Simbiótica
│       ├── personal_constitution.py        # Constituição Pessoal
│       └── trust_dynamics.py               # Dinâmica de Confiança
│
├── tests/
│   └── exocortex/
│       ├── test_symbiotic_self.py
│       ├── test_human_perception.py
│       ├── test_constitution_guardian.py
│       ├── test_confrontation_engine.py
│       └── test_alignment_calculator.py
│
└── pyproject.toml
```

### 2.3 PADRÕES TÉCNICOS OBRIGATÓRIOS (GEMINI 3.0)

#### 1. High Reasoning & Thinking Budget
Toda interação crítica de análise psicológica ou ética deve invocar o `gemini_client` com o orçamento de pensamento ativado.
*   **Exigência:** `gemini_client.generate(..., thinking_budget=True)`
*   **Justificativa:** O sistema não pode "chutar" diagnósticos. Ele precisa deduzir através de uma cadeia de pensamento explícita.

#### 2. Temporal Anchoring (Grounding)
Prompts crus são proibidos. Todo prompt deve passar por um middleware de injeção de contexto temporal.
*   **Template Obrigatório:**
    ```python
    f"""
    [TEMPORAL ANCHOR]
    Current Date: {datetime.now().isoformat()}
    User Context: {user_context_summary}
    ---
    [INSTRUCTION]
    {prompt_content}
    """
    ```
*   **Objetivo:** Evitar alucinações temporais e garantir relevância situacional.

#### 3. Strict JSON Schema Output
A saída "criativa" da IA deve ser constrangida para processamento determinístico.
*   **Uso:** Todas as funções de análise (`analyze_shadow`, `audit_action`) devem usar o parâmetro `response_schema` do Gemini.
*   **Objetivo:** Garantir que os "vieses" e "emoções" detectados possam ser parseados pelos sistemas de controle (Ex: `trust_dynamics`).

#### 4. Isolamento de Memória (HTTP Only)
O `maximus_core_service` **NUNCA** deve tentar conectar diretamente ao banco de dados do `episodic_memory`.
*   **Padrão:** Uso exclusivo de `MemoryClient` que realiza chamadas HTTP para a API do serviço de memória.
*   **Violação:** Importar drivers de banco de dados (`psycopg2`, `qdrant_client`) dentro do core service para acessar dados de memória é uma violação arquitetural grave.

---

## PARTE 3: ESPECIFICAÇÕES DE MÓDULOS

### 3.1 MÓDULO: SymbioticSelfConcept

**Arquivo:** `consciousness/exocortex/symbiotic_self.py`  
**Estende:** `florescimento/unified_self.py`

```python
"""
SymbioticSelfConcept - O Self que inclui Humano + Daimon

Baseado em: Extended Mind Theory (Clark & Chalmers, 1998)
Estende: UnifiedSelfConcept do Projeto Florescimento
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Importar base existente
from consciousness.florescimento.unified_self import (
    UnifiedSelfConcept,
    ComputationalState,
    FirstPersonPerspective,
    MetaSelfModel
)

# ... (Resto das classes de dados: ValuePriority, HumanValue, etc. mantidas conforme v1.0)
# ... (Ver arquivo original para implementações completas das dataclasses)

@dataclass
class SymbioticSelfConcept(UnifiedSelfConcept):
    # ... (Atributos mantidos)

    def update_perception(
        self, 
        message: str, 
        context: Dict[str, Any]
    ) -> DaimonPerception:
        """
        Atualiza a percepção do Daimon sobre o estado do usuário.
        
        [ATUALIZAÇÃO v4.1]: Usa Gemini 3.0 com Thinking Budget
        """
        # Invocar Gemini Client com Temporal Anchoring
        # prompt = construct_anchored_prompt(...)
        # response = gemini_client.generate(prompt, thinking_budget=True, schema=PerceptionSchema)
        
        # Placeholder para lógica de integração
        emotional_indicators = self._analyze_emotional_indicators(message) # Substituir por chamada Gemini
        alignment = self._calculate_current_alignment(message, context)
        
        self.daimon_perception = DaimonPerception(
            perceived_emotional_state=emotional_indicators["state"],
            perceived_energy_level=emotional_indicators["energy"],
            perceived_alignment=alignment,
            perceived_stress_level=emotional_indicators["stress"],
            confidence_in_perception=0.7,
            last_updated=datetime.now()
        )
        
        return self.daimon_perception
    
    # ... (Resto dos métodos mantidos)
```

### 3.2 MÓDULO: ConstitutionGuardian

**Arquivo:** `consciousness/exocortex/constitution_guardian.py`

*(Mantém a lógica da v1.0, mas com a nota de que `check_violation` deve usar Gemini com JSON Schema para análise semântica profunda em vez de simples keywords)*

### 3.3 MÓDULO: ConfrontationEngine

**Arquivo:** `consciousness/exocortex/confrontation_engine.py`

*(Mantém a lógica da v1.0. A geração de mensagens socráticas se beneficia imensamente do Gemini 3.0)*

### 3.4 MÓDULO: ExocortexAPI

**Arquivo:** `consciousness/exocortex/api/exocortex_router.py`

*(Mantém a estrutura de endpoints da v1.0)*

---

## PARTE 4: CRONOGRAMA DE IMPLEMENTAÇÃO

### 4.1 Visão Geral (12 Sprints / 6 Semanas)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CRONOGRAMA DE IMPLEMENTAÇÃO                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   SEMANA 1: FUNDAÇÃO & SAFETY                                           │
│   ├── Sprint 1 (D1-D2): SymbioticSelfConcept + Gemini Client Update    │
│   └── Sprint 2 (D3-D4): PersonalConstitution + Guardian                │
│                                                                         │
│   SEMANA 2: CONFRONTAÇÃO                                                │
│   ├── Sprint 3 (D5-D6): ConfrontationEngine                            │
│   └── Sprint 4 (D7-D8): Integração com Prefrontal Cortex               │
│                                                                         │
│   SEMANA 3: PROTEÇÃO                                                    │
│   ├── Sprint 5 (D9-D10): AttentionFirewall (Digital Thalamus)          │
│   └── Sprint 6 (D11-D12): ImpulseInhibitor                             │
│                                                                         │
│   SEMANA 4: MEMÓRIA                                                     │
│   ├── Sprint 7 (D13-D14): SymbioticMemory (HTTP Client)                │
│   └── Sprint 8 (D15-D16): TrustDynamics                                │
│                                                                         │
│   SEMANA 5: INTEGRAÇÃO                                                  │
│   ├── Sprint 9 (D17-D18): ExocortexAPI + Testes                        │
│   └── Sprint 10 (D19-D20): Integração com Maximus Core                 │
│                                                                         │
│   SEMANA 6: REFINAMENTO                                                 │
│   ├── Sprint 11 (D21-D22): UI/UX do Onboarding                         │
│   └── Sprint 12 (D23-D24): Testes E2E + Documentação                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Detalhamento por Sprint (Foco v4.1)

#### **SPRINT 1: SymbioticSelfConcept + Gemini Integration** (Dias 1-2)

| Tarefa | Arquivo | Horas | Prioridade |
|--------|---------|-------|------------|
| Atualizar `gemini_client` com Thinking Budget | `utils/gemini_client.py` | 2h | P0 |
| Implementar Temporal Anchoring Wrapper | `utils/prompts.py` | 2h | P0 |
| Criar estrutura SymbioticSelfConcept | `symbiotic_self.py` | 4h | P0 |
| Testes unitários com Mocks do Gemini | `test_symbiotic_self.py` | 3h | P0 |

**Entregáveis:**
- [x] `gemini_client` suportando parâmetros 3.0
- [x] `SymbioticSelfConcept` funcional
- [x] Testes passando

#### **SPRINT 2: PersonalConstitution + Guardian** (Dias 3-4)

| Tarefa | Arquivo | Horas | Prioridade |
|--------|---------|-------|------------|
| Criar PersonalConstitution (JSON) | `constitution_guardian.py` | 3h | P0 |
| Implementar audit_action com JSON Schema | `constitution_guardian.py` | 4h | P0 |
| Implementar "Override Consciente" (Safety) | `constitution_guardian.py` | 3h | P0 |
| Testes unitários | `test_constitution_guardian.py` | 4h | P0 |

**Entregáveis:**
- [x] Constituição persistível
- [x] Auditoria usando raciocínio estruturado (não apenas keywords)
- [x] Mecanismo de Override implementado

#### **SPRINT 7: SymbioticMemory (HTTP Client)** (Dias 13-14)

| Tarefa | Arquivo | Horas | Prioridade |
|--------|---------|-------|------------|
| Implementar `MemoryClient` (requests) | `memory/memory_client.py` | 4h | P0 |
| Isolar lógica de memória do DB direto | Refatoração | 4h | P0 |
| Criar SymbioticMemory Adapter | `memory/symbiotic_memory.py` | 3h | P0 |
| Testes com Mock de API | `tests/` | 3h | P0 |

**Entregáveis:**
- [x] Cliente HTTP robusto para memória
- [x] Zero dependências de banco de dados no Core Service

---

## PARTE 5: CRITÉRIOS DE SUCESSO

### 5.1 Critérios Técnicos

| Critério | Meta | Verificação |
|----------|------|-------------|
| Cobertura de Testes | > 90% | pytest --cov |
| Tempo de Resposta API | < 2s (Com Thinking) | Benchmark |
| Conformidade JSON Schema | 100% | Validação Pydantic |
| Isolamento de Containers | 0 conexões DB diretas | Análise de dependências |

### 5.2 Critérios de Produto & Ética

| Critério | Meta | Verificação |
|----------|------|-------------|
| Onboarding Completo | < 10 minutos | Teste de usuário |
| Override Consciente | Disponível em 100% dos vetos | Auditoria de UX |
| Redução de Intervenção | Tendência de queda mensal | Analytics de Longo Prazo |
| Alinhamento Valor-Ação | > 80% detectado | Relatório Semanal |

---

## ASSINATURA

```
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   PLANO TÉCNICO: EXOCÓRTEX ÉTICO E COGNITIVO                         ║
║   Digital Daimon v4.1 — SOPHIA (Safety & Reasoning Layer)            ║
║                                                                      ║
║   "Código seguro para mentes livres."                                ║
║                                                                      ║
║   ┌──────────────────────────────────────────────────────────────┐   ║
║   │  Arquiteto-Chefe: Juan Carlos de Souza                       │   ║
║   │  Revisor Técnico: Gemini 3.0                                 │   ║
║   │  Data: 05 de Dezembro de 2025                                │   ║
║   │  Status: PLANO TÉCNICO APROVADO                              │   ║
║   └──────────────────────────────────────────────────────────────┘   ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

*Documento 2 de 2 — Ver BLUEPRINT_EXOCORTEX_ETICO.md para visão conceitual.*