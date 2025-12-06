# PPBPR Step 4: The Tactical Plan
## Roteiro de Implementação: Mnemosyne + Kaggle Display

**Objetivo**: Entregar o sistema funcional com "Infinite Context" e "Neuro-Display" em 3 dias (Sprint Kaggle).

---

### Phase 1: The Base (Knowledge Engine) - HOJE
*Foco: Fazer o Daimon ler o diretório `knowledge_base` e injetar no prompt.*

- [ ] **1.1 Estrutura de Arquivos**: Criar diretório e colocar arquivos `.md` e `.txt` de teste.
- [ ] **1.2 Upgrade no `knowledge_engine.py`**:
    - Implementar cache em memória simples (Tier 1).
    - Criar função `retrieve_context(query)`.
- [ ] **1.3 Rota `/journal` v2**:
    - Adicionar parâmetro `use_memory=True`.
    - Injetar o contexto recuperado antes do prompt de sistema.

### Phase 2: The Brain (Thinking & Routing) - AMANHÃ
*Foco: Melhorar a qualidade do pensamento usando o contexto.*

- [ ] **2.1 Prompt Engineering**:
    - Atualizar `EXOCORTEX_SYSTEM_PROMPT` para instruir o uso de citações.
    - Ex: "Baseado no documento `[doc_name]`, percebo que..."
- [ ] **2.2 Shadow Integration**:
    - Fazer a "Análise de Sombra" cruzar o input atual com o histórico.
    - Ex: "Você disse hoje que está cansado, mas no dia 01/12 disse que estava 'energizado'. O que mudou?" (Contradição).

### Phase 3: The Face (Kaggle Display) - DEPOIS DE AMANHÃ
*Foco: Visualização para o vídeo de submissão.*

- [ ] **3.1 Streamlit Dashboard (`display_server.py`)**:
    - Criar um app simples em Streamlit que consome a API.
    - Coluna Esquerda: Chat.
    - Coluna Direita: "Exocortex Activity" (Logs visuais, Arquivos lidos).
- [ ] **3.2 Event Streaming**:
    - Refatorar o endpoint `/journal` para retornar *Streaming Response* (se houver tempo) ou um objeto JSON rico com todas as etapas.

### Phase 4: Refine & Record
- [ ] **4.1 Teste de Estresse**: Carregar 10 arquivos pesados e medir latência.
- [ ] **4.2 Gravação do Vídeo**: Roteiro de demonstração mostrando "Memória" e "Consciência".

---

## Ação Imediata (Next Step)
Aprovar este plano e iniciar **Phase 1: The Base**.
