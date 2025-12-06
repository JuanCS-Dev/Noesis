# PPBPR Step 1: The Deep Research Prompt (Golden 2025 Edition)

**Instrução**: Copie e cole este prompt no **Gemini 3 Pro (Web / Advanced)** para gerar a pesquisa fundamental.

---

### PROMPT DE PESQUISA PROFUNDA: PROJETO MNEMOSYNE (Data Base: Dez/2025)

**Role**: Você atua como Senior AI Research Scientist e Chief Architect no Google DeepMind.

**Contexto do Projeto**:
Estamos desenvolvendo o **DIGITAL DAIMON v4.0**, um sistema de "Simbiose/Exocórtex" rodando localmente (Python/FastAPI).
- **Core**: `maximus-core-service` (Lógica de consciência, ESGT, Thinking Mode).
- **Cérebro Atual**: Gemini 3.0 Pro (via API).
- **Objetivo Atual**: Integrar capacidades de **Infinite Context / Deep Memory**, inspiradas no milagre técnico do **Google NotebookLM** (Dezembro 2025).

**A Tese**: "Atenção sem Contexto é Nada". Queremos que o Daimon deixe de ser um modelo "stateless" e passe a ter acesso profundo e imediato à base de conhecimento do usuário (Diários, PDFs, Código), agindo como um Espelho Psicológico fundamentado na história real do indivíduo.

---

### SUA MISSÃO
Realize uma pesquisa profunda (Deep Research) que vá da **Ciência Teórica** à **Prática de Engenharia**, cobrindo os seguintes pilares críticos para Dezembro de 2025:

#### 1. O Estado da Arte (SOTA) em Dez/2025
- **NotebookLM Architecture**: Como o Google resolveu o problema de ingestão massiva e "Source Grounding"? Não quero suposições de 2024. Busque papers/docs técnicos recentes sobre a infraestrutura de "Audio Overview" e "Deep Grounding" do NotebookLM atual.
- **RAG vs. Infinite Context**: Com o Gemini 3.0 suportando janelas de contexto gigantescas (>2M tokens), o RAG (Vector DB) ainda é necessário para bases de conhecimento pessoais (< 1GB)? Ou a ingestão bruta ("Whole Context Injection") é superior em qualidade de raciocínio "holístico"?
- **Cognitive Science**: Cite papers recentes (2024-2025) sobre "Extended Mind" e "External Memory in AI" que validem a importância de dar "história" para a IA gerar empatia real.

#### 2. Integração Técnica com `maximus-core`
- Como integrar essa inteligência no nosso backend existente (`services/maximus_core_service`)?
- **API do NotebookLM**: Existe endpoint oficial em Dez/2025 para "conversar com um notebook"? Se sim, qual a spec?
- **Alternativa "NotebookLM-at-Home"**: Se não houver API, desenhe a arquitetura para emularmos isso usando a API do Gemini 3.0 Pro diretamente.
    - Como estruturar o prompt para evitar "Lost in the Middle"?
    - Caching de contexto (Context Caching API) é viável financeiramente para um usuário solo?

#### 3. UX de Simbiose
- Como o "Daimon" deve apresentar essa memória ao usuário? (Ex: Citações visuais como no NotebookLM? "Thinking Trace" mostrando a leitura dos documentos?)

---

### FORMATO DE SAÍDA (O Paper)
Gere um **Relatório Técnico (Monografia)** completo em Markdown.
- **Seção 1**: Fundamentação Teórica (Scientific Grounding).
- **Seção 2**: Análise de Viabilidade Técnica (NotebookLM API vs. Native Context).
- **Seção 3**: Blueprint de Arquitetura Recomendada para o Daimon v4.0.

Seja extremamente técnico, visionário e fundamentado na realidade de Dezembro de 2025.
