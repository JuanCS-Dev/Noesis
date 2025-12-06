# 🏛️ DIGITAL DAIMON: O Exocórtex Ético
> *Um sistema metacognitivo para expansão da consciência, filtragem de ruído e alinhamento ético.*

**Kernel:** Maximus 3.0 (Distributed Consciousness)  
**Arquitetura:** Híbrida (Monolito Modular + Microserviços Especializados)  
**Status:** 🟢 Operacional / Em Evolução Ativa  
**Data da Auditoria:** 05 de Dezembro de 2025

## 🎯 Missão
O **Digital Daimon** não é apenas um assistente; é um **sistema imunológico cognitivo**. Ele protege a atenção do usuário contra a economia da atenção, inibe impulsos de curto prazo em favor de objetivos de longo prazo e mantém um registro ético e reflexivo da existência digital.

## 📊 Status do Sistema

O projeto encontra-se em estágio avançado de maturação (**Maximus 3.0**), com a maioria dos serviços migrados para arquitetura moderna (Python 3.12+, `uv`, `docker-compose`).

### 🧠 Núcleo Central (The Monolith)
*   **`maximus_core_service`**: O cérebro do sistema. Contém a integração completa da consciência, governança ética, validação constitucional e módulos de IA avançada. É a fonte da verdade para lógica complexa.
    *   *Status:* ✅ Modernizado (`uv`, Testes 100%, Documentação Extensiva)
    *   *Módulos:* Consciousness (GWT), HitL, Justice (Constitutional AI), Performance, XAI.

### 🛡️ Serviços de Proteção & Controle (Cognitive Firewall)
*   **`digital_thalamus_service`**: Filtro de entrada. Bloqueia ruído e gerencia a atenção.
    *   *Status:* ✅ Modernizado
*   **`prefrontal_cortex_service`**: Inibição e Decisão. O "freio" executivo para impulsos.
    *   *Status:* ✅ Modernizado (Core migrado, legado contido)
*   **`reactive_fabric_core`**: Sistema Imunológico Digital. Detecção de intrusão, honeypots e resposta a incidentes.
    *   *Status:* ✅ Modernizado (Stack de segurança completa)

### ⚖️ Reflexão & Ética (The Mirror)
*   **`metacognitive_reflector`**: O "Júri Interno". Analisa decisões passadas e pune/recompensa virtualmente o sistema.
    *   *Status:* ✅ Modernizado
*   **`ethical_audit_service`**: Auditoria contínua de conformidade com a Constituição do projeto.
    *   *Status:* 🔄 Híbrido (Modernização em andamento)
*   **`episodic_memory`**: Diário autobiográfico do sistema.

### 💓 Homeostase (HCL Stack)
Conjunto de serviços que mantém o equilíbrio "fisiológico" do sistema (Simulated Biorhythms).
*   **`hcl_monitor_service`**: Sensores.
*   **`hcl_analyzer_service`**: Diagnóstico.
*   **`hcl_planner_service`**: Estratégia.
*   **`hcl_executor_service`**: Ação.
    *   *Status Geral:* ✅ Modernizados

### 🔌 Infraestrutura & Ferramentas
*   **`mcp_server`**: Servidor do Model Context Protocol para integração com IDEs e ferramentas locais.
*   **`api_gateway`**: Ponto de entrada unificado.

## 🚀 Como Iniciar

O projeto utiliza `docker-compose` para orquestração. A maioria dos serviços utiliza `uv` para gerenciamento de pacotes, garantindo builds rápidos.

### Pré-requisitos
*   Docker & Docker Compose
*   Python 3.12+ (para desenvolvimento local)
*   `uv` (recomendado)

### Executando o Stack (Exemplo)

Para iniciar o núcleo e os serviços essenciais:

```bash
cd backend/services
# O arquivo docker-compose.yml na raiz de services orquestra o stack
docker-compose up --build -d
```

*Nota: Devido à complexidade e quantidade de serviços, recomenda-se iniciar apenas os módulos necessários para a tarefa atual se a memória for limitada.*

## 🛠️ Desenvolvimento e Padrões

*   **Gerenciamento de Dependências:** `pyproject.toml` + `uv.lock`.
*   **Estrutura de Pastas:** Padrão `api/` (rotas), `core/` (lógica de negócio), `models/` (dados).
*   **Testes:** `pytest`. O `maximus_core_service` possui uma suite de testes massiva que garante a integridade constitucional.

---
*Digital Daimon - Expandindo a Consciência através do Código.*