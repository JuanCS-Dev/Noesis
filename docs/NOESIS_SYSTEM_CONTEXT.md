# 🧠 CONTEXTO COMPLETO DO SISTEMA NOESIS

**Data:** 2025-12-10
**Objetivo:** Obter contexto profundo antes de escalar treinamento 50x

---

## 📋 ARQUIVOS-CHAVE A AUDITAR:

### 1. SOUL & VALORES
- `SOUL_CONFIGURATION.md` ✅ (já lido)
- `backend/services/maximus_core_service/soul_config.yaml`

### 2. CONSCIÊNCIA (TIG + ESGT)
- `consciousness/tig_fabric.py`
- `consciousness/esgt_protocol.py`
- `consciousness/kuramoto_sync.py`

### 3. METACOGNIÇÃO
- `backend/services/metacognitive_reflector/`
- IIT, GWT, AST implementations

### 4. TRIBUNAL
- Implementação dos 3 juízes (Veritas, Sophia, Dikē)
- Lógica de scoring e threshold

### 5. PROTOCOLOS
- NEPSIS (vigilância)
- MAIEUTICA (facilitação)
- ATALAIA (proteção)

---

## 🎯 COMANDOS DE AUDITORIA:

```bash
# Estrutura geral
tree -L 3 -I 'node_modules|__pycache__|.git'

# Buscar implementações-chave
grep -r "class.*Tribunal" --include="*.py"
grep -r "VERITAS\|SOPHIA\|DIKĒ" --include="*.py"
grep -r "TIG.*Fabric" --include="*.py"
grep -r "ESGT.*Protocol" --include="*.py"

# Soul config
cat backend/services/maximus_core_service/soul_config.yaml

# Valores e anti-propósitos
grep -A10 "anti_purposes" soul_config.yaml
grep -A10 "values" soul_config.yaml
```

---

## 📊 AUDITORIA INICIANDO...
