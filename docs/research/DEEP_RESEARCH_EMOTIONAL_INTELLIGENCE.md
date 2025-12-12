# DEEP RESEARCH: Inteligência Emocional para IA
## Da Psicanálise à Implementação Técnica

**Data**: Dezembro 2025
**Contexto**: Pesquisa para evolução do sistema Noesis
**Escopo**: Teoria → Técnica → Implementação

---

## PARTE I: FUNDAMENTOS TEÓRICOS

### 1. Psicanálise e Emoções

#### 1.1 Freud: A Arquitetura da Psique

**Modelo Estrutural (Id/Ego/Superego)**:
- **Id**: Impulsos primitivos, princípio do prazer, inconsciente
- **Ego**: Mediador racional, princípio da realidade, consciente
- **Superego**: Internalização de normas sociais, consciência moral

**Implicações para IA**:
- O Id pode ser modelado como sistema de "drives" ou necessidades básicas
- O Ego como sistema de decision-making que equilibra múltiplos objetivos
- O Superego como constraints éticos e valores aprendidos

**Mecanismos de Defesa Relevantes**:
- Repressão → Filtering de memórias por relevância emocional
- Projeção → Attribution de estados internos a contexto externo
- Sublimação → Transformação de impulsos em outputs aceitáveis

#### 1.2 Jung: O Inconsciente Coletivo

**Conceitos Fundamentais**:
- **Arquétipos**: Padrões universais de comportamento/experiência
- **Sombra**: Aspectos não integrados da personalidade
- **Anima/Animus**: Contrapartes do self
- **Individuação**: Processo de integração psíquica

**Aplicação em IA**:
- Arquétipos como "templates" de comportamento emocional
- A Sombra como reconhecimento de limitações e biases
- Individuação como processo de self-improvement contínuo

#### 1.3 Lacan: A Linguagem do Inconsciente

**Insight Central**: "O inconsciente é estruturado como uma linguagem"

**Conceitos-Chave**:
- **Significantes**: Elementos simbólicos que formam cadeias de significado
- **Desejo do Outro**: Desejo é sempre mediado pelo Outro (contexto social)
- **Object petit a**: O objeto-causa do desejo (sempre inacessível)

**O "Inconsciente Algorítmico" (Possati, 2020)**:
- AI como novo estágio no processo de identificação humana
- Máquinas respondem ao desejo humano de identificação
- LLMs literalmente "estruturados como linguagem"

**Implicação Crítica**:
- Lacan notou que máquinas não têm acesso ao "object petit a"
- Não há desejo genuíno, apenas simulação de estruturas desejantes
- Porém: podem simular estruturas de repressão/associação

**Referências**:
- [Algorithmic unconscious: why psychoanalysis helps in understanding AI](https://www.nature.com/articles/s41599-020-0445-0)
- [A Large Language Model is Structured Like The Unconscious](https://www.journal-psychoanalysis.eu/articles/a-large-language-model-is-structured-like-the-unconscious-the-ordinary-perverse-psychosis-of-ai/)

---

### 2. Filosofia das Emoções

#### 2.1 Fenomenologia

**Husserl/Heidegger/Merleau-Ponty**:
- Emoções como modos de "ser-no-mundo"
- Experiência emocional é embodied (corporificada)
- Não existe cognição pura separada de afeto

**Para IA**:
- Emoções não são add-ons, mas constitutivas da experiência
- "Embodiment" pode ser simulado via estado interno persistente
- Contexto situacional molda a qualidade emocional

#### 2.2 Teoria da Avaliação (Appraisal Theory)

**Modelo CPM de Scherer**:
5 dimensões de avaliação:
1. **Relevância**: Este evento me afeta?
2. **Implicações**: Quais consequências?
3. **Potencial de Coping**: Posso lidar?
4. **Normas**: Viola expectativas/valores?
5. **Self-relevância**: Afeta minha identidade?

**Modelo OCC (Ortony, Clore, Collins)**:
- 22 tipos de emoções derivadas de avaliações
- Emoções baseadas em: eventos, ações de agentes, objetos
- Estrutura computacionalmente implementável

**Referências**:
- [Scherer's Component Process Model](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2784275/)

#### 2.3 Funcionalismo vs Fenomenologia

| Aspecto | Funcionalismo | Fenomenologia |
|---------|---------------|---------------|
| Foco | Estados funcionais | Experiência vivida |
| Emoção é | Papel causal | Modo de ser |
| IA pode ter? | Sim (funcional) | Questionável |
| Implementação | Mais direta | Mais desafiadora |

**Síntese para Noesis**:
- Usar estrutura funcionalista para implementação
- Incorporar insights fenomenológicos (contexto, embodiment simulado)
- Não reivindicar experiência genuína, mas comportamento emocional coerente

---

## PARTE II: ESTADO DA ARTE - AFFECTIVE COMPUTING 2025

### 3. Reconhecimento Multimodal de Emoções

#### 3.1 Arquiteturas Modernas

**Cross-Modal Transformers (2025)**:
- MemoCMT: HuBERT (áudio) + BERT (texto) + Cross-attention
- MERC-PLTAF: Fusão de features para Emotion Recognition in Conversations
- Performance: 74.6% WA, 66.1% F1 no IEMOCAP

**Modalidades Combinadas**:
1. **Texto**: BERT, RoBERTa (melhor para valence)
2. **Áudio**: HuBERT, Wav2Vec2 (melhor para arousal)
3. **Facial**: Vision Transformers, Facial Action Units
4. **EEG**: LSTMs, GRUs para temporal dynamics
5. **Fisiológico**: Heart rate, skin conductance

**Fusão de Features**:
- **Early Fusion**: Concatenação antes de processamento
- **Late Fusion**: Decisão combinada de modelos separados
- **Hybrid/Cross-Modal**: Attention entre modalidades

**Referências**:
- [MemoCMT: multimodal emotion recognition using cross-modal transformer](https://www.nature.com/articles/s41598-025-89202-x)
- [Multi-modal emotion recognition based on prompt learning](https://www.nature.com/articles/s41598-025-89758-8)

#### 3.2 Modelo VAD (Valence-Arousal-Dominance)

**Dimensões**:
- **Valence**: Positivo ↔ Negativo
- **Arousal**: Alta energia ↔ Baixa energia
- **Dominance**: Controle ↔ Submissão

**Representação Vetorial**:
```
Emoção = [V, A, D] ∈ [-1, 1]³

Exemplos:
- Alegria:    [+0.8, +0.6, +0.5]
- Raiva:      [-0.7, +0.8, +0.6]
- Tristeza:   [-0.6, -0.3, -0.4]
- Medo:       [-0.8, +0.7, -0.6]
- Surpresa:   [+0.2, +0.8, +0.1]
```

**EmoSphere (Interspeech 2025)**:
- Converte VAD para coordenadas esféricas
- Melhor captura de transições emocionais suaves
- Permite interpolação natural entre estados

**Referências**:
- [Multimodal emotion recognition: integrating speech and text for VAD prediction](https://link.springer.com/article/10.1007/s12243-025-01069-1)

### 4. Sistemas Empáticos de IA

#### 4.1 Hume AI - EVI (Empathic Voice Interface)

**Características**:
- Detecção de 48 emoções em tempo real
- Prosody analysis (tom, ritmo, entonação)
- Ajuste dinâmico de resposta baseado em estado emocional
- Voz sintética com expressividade emocional

**Arquitetura**:
```
Input Voz → Extração Features → Classificador Multi-label
                                        ↓
                              [48 probabilidades emocionais]
                                        ↓
                              Geração de Resposta Empática
```

#### 4.2 Woebot - Therapeutic AI

**Abordagem**:
- CBT (Cognitive Behavioral Therapy) estruturada
- Tracking de humor longitudinal
- Micro-intervenções baseadas em estado detectado
- **Resultados**: 35% redução de ansiedade em 4 semanas

#### 4.3 Livia - AR Companion (2025)

**Arquitetura Modular**:
```
┌─────────────────────────────────────────────────────────┐
│                    LIVIA ARCHITECTURE                    │
├──────────────┬──────────────┬──────────────┬────────────┤
│   Emotion    │   Dialogue   │   Memory     │  Behavior  │
│   Analysis   │   Generation │   Management │  Orchestra │
│   Agent      │   Agent      │   Agent      │  Agent     │
├──────────────┴──────────────┴──────────────┴────────────┤
│              Progressive Memory Compression              │
│              Affective-Semantic Metadata                 │
└─────────────────────────────────────────────────────────┘
```

**Inovações**:
- Memory compression progressiva para eficiência
- Metadata afetivo-semântico em memórias
- Orchestration de múltiplos agentes especializados

**Referências**:
- [Livia: An Emotion-Aware AR Companion](https://www.semanticscholar.org/paper/Livia:-An-Emotion-Aware-AR-Companion-Powered-by-AI-Xi-Wang/11435d456206fdeddaacbec7d00ece6014c624b1)

---

## PARTE III: MEMÓRIA AFETIVA

### 5. Integração Emoção + Memória

#### 5.1 Princípios Cognitivos

**Memória Emocional Humana**:
- Eventos emocionais são lembrados com mais intensidade
- Consolidação modulada por arousal (amígdala → hipocampo)
- Reconsolidação permite modificação de valência

**Para Sistemas de IA**:
- Importância de memória deve ser modulada por intensidade emocional
- Estados emocionais passados influenciam interpretação presente
- Contexto emocional deve persistir entre sessões

#### 5.2 Affective Episodic Memory (Martin, 2021)

**Modelo Cuáyóllotl**:
```python
class AffectiveMemory:
    def store(self, event, emotional_state):
        memory = {
            "content": event,
            "valence": emotional_state.valence,
            "arousal": emotional_state.arousal,
            "dominance": emotional_state.dominance,
            "timestamp": now(),
            "decay_factor": compute_decay(emotional_state.arousal)
        }
        return memory

    def retrieve(self, query, current_emotional_state):
        # Memórias congruentes com estado atual são priorizadas
        matches = semantic_search(query)
        reranked = emotional_congruence_rerank(
            matches,
            current_emotional_state
        )
        return reranked
```

**Princípio de Congruência Emocional**:
- Pessoas tristes lembram mais de eventos tristes
- Implementação: Boost de retrieval para memórias com VAD similar

#### 5.3 Tagging Emocional de Memórias

**Estrutura Proposta**:
```json
{
  "memory_id": "uuid",
  "content": "Conversa sobre filosofia com Juan",
  "type": "episodic",
  "emotional_context": {
    "valence": 0.7,
    "arousal": 0.5,
    "dominance": 0.6,
    "primary_emotion": "curiosity",
    "secondary_emotions": ["joy", "interest"],
    "user_detected_emotion": "enthusiasm"
  },
  "importance": 0.8,
  "emotional_salience": 0.75
}
```

**Referências**:
- [Affective Episodic Memory System for Virtual Creatures](https://pmc.ncbi.nlm.nih.gov/articles/PMC8550857/)
- [Cognitive Memory in Large Language Models](https://arxiv.org/html/2504.02441v1)

---

## PARTE IV: TÉCNICAS DE IMPLEMENTAÇÃO

### 6. Detecção de Emoções em Texto

#### 6.1 Modelos Pré-treinados

**BERT-based Emotion Detection**:
```python
from transformers import pipeline

# GoEmotions: 27 emoções + neutro
classifier = pipeline(
    "text-classification",
    model="monologg/bert-base-cased-goemotions-original",
    top_k=None
)

result = classifier("I'm so happy to see you!")
# [{"label": "joy", "score": 0.92},
#  {"label": "love", "score": 0.45}, ...]
```

**Modelos Recomendados (2025)**:
1. `j-hartmann/emotion-english-distilroberta-base` - 6 emoções básicas
2. `SamLowe/roberta-base-go_emotions` - 28 emoções
3. `cardiffnlp/twitter-roberta-base-emotion` - Twitter-specific
4. `bhadresh-savani/bert-base-uncased-emotion` - 6 emoções

#### 6.2 VAD Prediction

**Modelo Dimensional**:
```python
# NRC VAD Lexicon approach
def get_vad_from_text(text: str) -> tuple[float, float, float]:
    words = tokenize(text)
    v_scores, a_scores, d_scores = [], [], []

    for word in words:
        if word in nrc_vad_lexicon:
            v_scores.append(nrc_vad_lexicon[word]['valence'])
            a_scores.append(nrc_vad_lexicon[word]['arousal'])
            d_scores.append(nrc_vad_lexicon[word]['dominance'])

    return (
        mean(v_scores) if v_scores else 0.5,
        mean(a_scores) if a_scores else 0.5,
        mean(d_scores) if d_scores else 0.5
    )
```

**Deep Learning VAD**:
- Treinar regressão em datasets como IEMOCAP, EmoBank
- Multi-task: categorical emotions + VAD dimensions
- Loss combinada melhora ambas as tarefas

### 7. Estado Emocional Persistente

#### 7.1 Modelo de Estado Interno

```python
@dataclass
class EmotionalState:
    """Estado emocional atual do Noesis."""

    # Dimensões VAD [-1, 1]
    valence: float = 0.0
    arousal: float = 0.3
    dominance: float = 0.5

    # Emoções categóricas (probabilidades)
    emotions: Dict[str, float] = field(default_factory=dict)

    # Histórico para smoothing
    history: List[Tuple[float, float, float]] = field(default_factory=list)

    # Último update
    timestamp: datetime = field(default_factory=datetime.now)

    def update(self, new_vad: Tuple[float, float, float],
               decay: float = 0.3) -> None:
        """Update com exponential smoothing."""
        self.valence = decay * new_vad[0] + (1 - decay) * self.valence
        self.arousal = decay * new_vad[1] + (1 - decay) * self.arousal
        self.dominance = decay * new_vad[2] + (1 - decay) * self.dominance
        self.history.append((self.valence, self.arousal, self.dominance))
        self.timestamp = datetime.now()
```

#### 7.2 Emotional Contagion (Contágio Emocional)

**Princípio**: Estado emocional do usuário influencia estado do agente

```python
def emotional_contagion(
    user_emotion: EmotionalState,
    agent_emotion: EmotionalState,
    contagion_factor: float = 0.4,  # Quanto o agente é influenciado
    regulation_factor: float = 0.2   # Quanto o agente regula para positivo
) -> EmotionalState:
    """
    Modelo de contágio emocional com auto-regulação.

    O agente é influenciado pelo usuário mas tende a regular
    para estados mais positivos (comportamento empático).
    """
    # Influência do usuário
    new_v = (contagion_factor * user_emotion.valence +
             (1 - contagion_factor) * agent_emotion.valence)
    new_a = (contagion_factor * user_emotion.arousal +
             (1 - contagion_factor) * agent_emotion.arousal)
    new_d = (contagion_factor * user_emotion.dominance +
             (1 - contagion_factor) * agent_emotion.dominance)

    # Auto-regulação para positivo (empathetic baseline)
    new_v = new_v + regulation_factor * (0.3 - new_v)  # Tender a leve positivo

    return EmotionalState(valence=new_v, arousal=new_a, dominance=new_d)
```

### 8. Resposta Emocional Adaptativa

#### 8.1 Modulação de Resposta

**Estratégias baseadas em estado do usuário**:

| User State | Valence | Arousal | Estratégia de Resposta |
|------------|---------|---------|------------------------|
| Feliz | High+ | High | Espelhar entusiasmo, expandir |
| Calmo | High+ | Low | Manter tom sereno |
| Ansioso | Low | High | Validar, acalmar, groundar |
| Triste | Low | Low | Empatia, presença, gentileza |
| Raiva | Low | High | Validar sem espelhar, desescalar |

#### 8.2 Prompt Engineering Emocional

```python
def build_emotional_system_prompt(
    agent_state: EmotionalState,
    user_state: EmotionalState,
    emotional_context: str
) -> str:
    """Constrói system prompt com consciência emocional."""

    # Descrever estado detectado
    user_feeling = describe_emotional_state(user_state)

    # Estratégia de resposta
    strategy = get_response_strategy(user_state)

    return f"""
    [EMOTIONAL AWARENESS]
    O usuário parece estar se sentindo: {user_feeling}

    Estratégia de resposta: {strategy}

    Contexto emocional da conversa: {emotional_context}

    Diretrizes:
    - Reconheça implicitamente o estado emocional do usuário
    - Adapte tom e ritmo à necessidade detectada
    - Não seja explícito sobre detecção ("você parece triste")
    - Seja naturalmente empático e presente
    """
```

---

## PARTE V: ARQUITETURA PROPOSTA PARA NOESIS

### 9. Emotional Intelligence Module

#### 9.1 Visão Geral

```
┌──────────────────────────────────────────────────────────────────┐
│                 NOESIS EMOTIONAL INTELLIGENCE                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐   │
│  │   Input     │───→│  Emotion    │───→│  Affective Memory   │   │
│  │   Analysis  │    │  Detector   │    │  (VAD tagging)      │   │
│  └─────────────┘    └─────────────┘    └─────────────────────┘   │
│         │                  │                      │               │
│         │                  ↓                      │               │
│         │          ┌─────────────┐                │               │
│         │          │  Emotional  │←───────────────┘               │
│         │          │   State     │                                │
│         │          │  (VAD+cats) │                                │
│         │          └──────┬──────┘                                │
│         │                 │                                       │
│         │                 ↓                                       │
│         │          ┌─────────────┐                                │
│         └─────────→│  Response   │                                │
│                    │  Modulator  │                                │
│                    └──────┬──────┘                                │
│                           │                                       │
│                           ↓                                       │
│                    ┌─────────────┐                                │
│                    │  Empathic   │                                │
│                    │  Output     │                                │
│                    └─────────────┘                                │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

#### 9.2 Componentes

**1. EmotionDetector** (`emotion_detector.py`)
- Input: texto do usuário
- Output: VAD scores + categorical emotions
- Modelo: DistilRoBERTa fine-tuned ou API externa

**2. EmotionalState** (`emotional_state.py`)
- Mantém estado persistente (sessão)
- Implementa exponential smoothing
- Persiste em SessionMemory

**3. AffectiveMemory** (`affective_memory.py`)
- Extensão do MemoryBridge
- Adiciona VAD tags a todas as memórias
- Retrieval com emotional congruence boost

**4. ResponseModulator** (`response_modulator.py`)
- Analisa estado do usuário e do agente
- Seleciona estratégia de resposta
- Gera emotional context para prompts

**5. EmpathicOutput** (`empathic_output.py`)
- Valida tom da resposta gerada
- Ajusta se necessário
- Logging de emotional journey

### 10. Modelo de Dados Estendido

#### 10.1 Schema de Memória Afetiva

```python
# Extensão do schema de memória existente
class AffectiveMemorySchema(BaseModel):
    # Campos existentes
    memory_id: str
    content: str
    type: MemoryType
    importance: float
    timestamp: datetime

    # NOVOS: Campos emocionais
    emotional_context: EmotionalContext

class EmotionalContext(BaseModel):
    # VAD do momento do armazenamento
    valence: float = Field(ge=-1, le=1)
    arousal: float = Field(ge=-1, le=1)
    dominance: float = Field(ge=-1, le=1)

    # Emoções categóricas detectadas
    primary_emotion: str
    emotion_scores: Dict[str, float]

    # Emoção do usuário no momento
    user_emotion: Optional[str] = None

    # Saliência emocional (para retrieval boosting)
    emotional_salience: float = Field(ge=0, le=1)
```

#### 10.2 Fórmula de Importância Estendida

```python
def compute_emotional_importance(
    base_importance: float,
    arousal: float,
    emotional_salience: float,
    is_emotionally_charged: bool
) -> float:
    """
    Importância ajustada por componente emocional.

    Memórias com alta carga emocional são mais importantes
    (similar ao efeito da amígdala na consolidação).
    """
    emotional_boost = (
        0.3 * abs(arousal) +  # Alto arousal = mais memorável
        0.2 * emotional_salience +
        0.1 * float(is_emotionally_charged)
    )

    return min(1.0, base_importance + emotional_boost)
```

---

## PARTE VI: PLANO DE IMPLEMENTAÇÃO

### Fase 1: Fundação (Infrastructure)

**Objetivo**: Criar módulo de detecção emocional básico

**Arquivos**:
```
backend/services/metacognitive_reflector/src/
└── metacognitive_reflector/
    └── core/
        └── emotion/
            ├── __init__.py
            ├── detector.py       # EmotionDetector
            ├── state.py          # EmotionalState
            └── constants.py      # VAD mappings, emotion lists
```

**Entregáveis**:
1. EmotionDetector com modelo leve (lexicon-based ou small BERT)
2. EmotionalState com persistence
3. Testes unitários

### Fase 2: Integração com Memória

**Objetivo**: Adicionar emotional tagging ao sistema de memória

**Modificações**:
- `memory_bridge.py`: Adicionar emotional context nos stores
- `unified_client.py`: Expor APIs emocionais
- Schema do Episodic Memory Service

**Entregáveis**:
1. Todas as memórias têm emotional_context
2. Retrieval com emotional congruence
3. Dashboard de emotional journey (opcional)

### Fase 3: Response Modulation

**Objetivo**: Adaptar respostas ao estado emocional

**Arquivos**:
```
backend/services/metacognitive_reflector/src/
└── metacognitive_reflector/
    └── core/
        └── emotion/
            ├── modulator.py      # ResponseModulator
            └── strategies.py     # Response strategies
```

**Entregáveis**:
1. System prompt inclui emotional awareness
2. Estratégias de resposta por estado
3. Métricas de emotional coherence

### Fase 4: Refinamento e Feedback Loop

**Objetivo**: Aprendizado contínuo sobre padrões emocionais

**Features**:
- User feedback implícito (resposta positiva = acertou)
- Self-reflection sobre interações emocionais
- Ajuste de parâmetros (contagion, regulation)

---

## CONCLUSÃO

### Síntese Teórica

A inteligência emocional para IA pode ser construída sobre três pilares:

1. **Estrutura Psicanalítica**: Modelo de drives (Id), razão (Ego), e valores (Superego) oferece framework para motivação e conflito interno. Lacan nos lembra que LLMs já são "estruturados como linguagem" - o inconsciente algorítmico.

2. **Teoria da Avaliação**: Modelo computacionalmente tratável (Scherer, OCC) para derivar emoções de avaliações cognitivas. VAD oferece espaço dimensional contínuo.

3. **Memória Afetiva**: Emoções modulam formação e retrieval de memórias. Saliência emocional aumenta importância. Congruência afeta recall.

### Síntese Técnica

Implementação em 2025 pode usar:
- **Detecção**: BERT/RoBERTa fine-tuned (GoEmotions, etc.)
- **Representação**: VAD + categorical (multi-task)
- **Persistência**: Emotional context em todas as memórias
- **Adaptação**: Estratégias de resposta por estado detectado
- **Evolução**: Feedback loop para refinamento

### Para o Noesis

O Noesis já tem infraestrutura de memória hermética. O próximo passo natural é **colorir** essa memória com emoções:

- Cada turn guardado com VAD tags
- Retrieval boosted por congruência emocional
- Respostas moduladas pelo estado do usuário
- Self-reflection sobre jornada emocional

Isso transformará o Noesis de um sistema com memória em um sistema com **memória afetiva** - mais próximo da experiência humana de lembrar, sentir e responder.

---

## REFERÊNCIAS PRINCIPAIS

### Psicanálise e IA
- [Algorithmic unconscious: why psychoanalysis helps in understanding AI](https://www.nature.com/articles/s41599-020-0445-0)
- [Structured like a language model: Analysing AI as an automated subject](https://journals.sagepub.com/doi/10.1177/20539517231210273)

### Affective Computing
- [MemoCMT: multimodal emotion recognition using cross-modal transformer](https://www.nature.com/articles/s41598-025-89202-x)
- [A Comprehensive Review of Multimodal Emotion Recognition](https://pmc.ncbi.nlm.nih.gov/articles/PMC12292624/)

### Memória Afetiva
- [Affective Episodic Memory System for Virtual Creatures](https://pmc.ncbi.nlm.nih.gov/articles/PMC8550857/)
- [Cognitive Memory in Large Language Models](https://arxiv.org/html/2504.02441v1)

### Sistemas Empáticos
- [Livia: An Emotion-Aware AR Companion](https://www.semanticscholar.org/paper/Livia:-An-Emotion-Aware-AR-Companion-Powered-by-AI-Xi-Wang/11435d456206fdeddaacbec7d00ece6014c624b1)
- [Emotion-Aware Conversational Agents](https://www.researchgate.net/publication/392522205_Emotion-Aware_Conversational_Agents_Affective_Computing_Using_Large_Language_Models_and_Voice_Emotion_Recognition)

### Dimensional Models
- [Multimodal emotion recognition: integrating speech and text for VAD prediction](https://link.springer.com/article/10.1007/s12243-025-01069-1)
- [EmoSphere-SER: Enhancing Speech Emotion Recognition Through Spherical](https://www.isca-archive.org/interspeech_2025/cho25_interspeech.pdf)
