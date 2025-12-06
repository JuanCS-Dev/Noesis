# PPBPR Step 3: The Mnemosyne Blueprint
## Arquitetura de Memória Infinita & Visualização de Pensamento

**Status**: 🔵 DRAFT
**Contexto**: Kaggle Gemini 3 Competition (6 Days Left)
**Core Concept**: "Atenção sem Contexto é Nada."

---

## 1. A Arquitetura "Dynamic Holism"
Baseada na pesquisa (Step 2), abandonamos a ideia de RAG puro. O Daimon v4.0 utilizará uma hierarquia de memória projetada para **emular a intimidade do NotebookLM** com a **potência do Gemini 3.0**.

### O Pipeline de Memória (The Mnemosyne Stack)

```mermaid
graph TD
    UserQuery[User Input] --> Router{Self-Route Gateway}
    
    subgraph Tier 1: Hot Cache (The Active Mind)
        Router -->|High Relevance| CachedContext[Gemini 3 Flash Cached]
        CachedContext -->|Docs: Diário + Projetos Atuais| SystemPrompt
    end
    
    subgraph Tier 2: Warm RAG (The Library)
        Router -->|Specific Fact Retrieval| VectorDB[ChromaDB Local]
        VectorDB -->|Top-20 Chunks| ContextBuilder
        ContextBuilder --> SystemPrompt
    end
    
    SystemPrompt --> ThinkingEngine[Gemini 3 Pro (Reasoning)]
    ThinkingEngine --> Output
```

### Decisões Técnicas Chave
1.  **Tier 1 (Hot Cache)**: Injeção de Contexto Completo (~200k tokens) para os arquivos mais vitais (ex: os últimos 3 meses de Journaling). Isso garante que o Daimon "sabe quem você é" sem precisar buscar nada.
2.  **Tier 2 (Warm RAG)**: Apenas para arquivos antigos ou técnicos (ex: PDFs de papers).
3.  **Self-Route**: O Daimon decide se precisa ler a biblioteca ou se responde com o que tem na "memória ativa".

---

## 2. The Kaggle Winning Feature: "Neuro-Symbolic Display"
O usuário pediu "Streaming de Pensamento". Como o NotebookLM tem o "Audio Overview", o Daimon terá o **"Consciousness Stream"**.
Não vamos apenas mostrar texto. Vamos mostrar **Atividade Neural**.

### 2.1 O Conceito Visual
Uma interface web (Streamlit ou React simples) que acompanha o CLI, exibindo:

1.  **Painel de Ativação Mnêmica (Memory Heatmap)**
    *   Quando o Daimon "lembra" de algo do Tier 1, o documento brilha.
    *   *Exemplo*: "Recuperando: `diario_2025_11_12.md` (Relevância: 98%)".
    
2.  **O Fluxo de Pensamento (The Ribbon)**
    *   Em vez de texto estático, o `reasoning_trace` flui como uma fita de teletipo ou ondas.
    *   *Visual*: `[System 2] Detecting Shadow... Comparing with 'fear_of_loss.md'... Formulationg empathy.`

3.  **Indicadores de Sombra (Jungian Radar)**
    *   Um gráfico de radar mostrando em tempo real o arquétipo ativo (Tirano, Vítima, Guerreiro).

### 2.2 Estrutura de Resposta (JSON-L Stream)
O backend não enviará apenas texto. Enviará eventos:

```json
{"event": "memory_access", "doc": "diario_2025.txt", "segment": "L140-150"}
{"event": "shadow_detect", "archetype": "The Victim", "confidence": 0.88}
{"event": "thought_chunk", "content": "Analyzing user fatigue..."}
{"event": "final_response", "content": "Você parece exausto..."}
```

---

## 3. Integração com o Core Existente
*   **Conexão**: O novo `knowledge_engine.py` se torna o fornecedor de contexto da classe `ConsciousnessBridge` (definida no *Florescimento*).
*   **Prompt**: Atualizamos o System Prompt para incluir: "Você tem acesso à memória do usuário. Use-a para validar ou refutar as percepções dele."

## Conclusão do Blueprint
Transformamos o Daimon de um **Chatbot** para um **Visualizador de Consciência**. O jurado do Kaggle não apenas lerá a resposta; ele **verá o Daimon pensando e lembrando**.
