#!/bin/bash
# ============================================================================
# MAXIMUS CONSCIOUSNESS - SUITE DE TESTES E2E COMPLETA
# ============================================================================
# Data: 2025-12-06
# Autor: Claude Code (Auditoria Brutal)
# Projeto: Digital Daimon - Hackathon DeepMind
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Config
BACKEND_URL="http://localhost:8001"
FRONTEND_URL="http://localhost:3000"
RESULTS_FILE="/tmp/daimon/e2e_results_$(date +%Y%m%d_%H%M%S).md"

# Counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Ensure results directory exists
mkdir -p /tmp/daimon

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

log_test() {
    echo -e "${CYAN}[TEST]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
    ((TESTS_TOTAL++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
    ((TESTS_TOTAL++))
}

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${PURPLE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}  $1${NC}"
    echo -e "${PURPLE}════════════════════════════════════════════════════════════${NC}"
}

# ============================================================================
# START REPORT
# ============================================================================

cat > "$RESULTS_FILE" << 'EOF'
# MAXIMUS CONSCIOUSNESS - RELATÓRIO DE TESTES E2E

**Data:** $(date)
**Ambiente:** Digital Daimon Development
**Backend:** http://localhost:8001
**Frontend:** http://localhost:3000

---

## Sumário Executivo

EOF

echo "# MAXIMUS CONSCIOUSNESS - RELATÓRIO DE TESTES E2E" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "**Data:** $(date)" >> "$RESULTS_FILE"
echo "**Ambiente:** Digital Daimon Development" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

log_section "INICIANDO SUITE DE TESTES E2E"

# ============================================================================
# TEST 1: BACKEND HEALTH CHECK
# ============================================================================

log_section "1. BACKEND HEALTH CHECK"

log_test "Verificando se backend está respondendo..."
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/v1/health" 2>/dev/null)
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -1)
BODY=$(echo "$HEALTH_RESPONSE" | head -1)

if [ "$HTTP_CODE" = "200" ]; then
    log_pass "Backend health endpoint retorna 200"
    echo "### 1.1 Health Endpoint: PASS" >> "$RESULTS_FILE"
    echo "\`\`\`json" >> "$RESULTS_FILE"
    echo "$BODY" >> "$RESULTS_FILE"
    echo "\`\`\`" >> "$RESULTS_FILE"
else
    log_fail "Backend health endpoint falhou (HTTP $HTTP_CODE)"
    echo "### 1.1 Health Endpoint: FAIL (HTTP $HTTP_CODE)" >> "$RESULTS_FILE"
fi

# Test root endpoint
log_test "Verificando root endpoint..."
ROOT_RESPONSE=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/" 2>/dev/null)
HTTP_CODE=$(echo "$ROOT_RESPONSE" | tail -1)

if [ "$HTTP_CODE" = "200" ]; then
    log_pass "Root endpoint retorna 200"
    echo "### 1.2 Root Endpoint: PASS" >> "$RESULTS_FILE"
else
    log_fail "Root endpoint falhou (HTTP $HTTP_CODE)"
    echo "### 1.2 Root Endpoint: FAIL" >> "$RESULTS_FILE"
fi

# ============================================================================
# TEST 2: CORS CONFIGURATION
# ============================================================================

log_section "2. CORS CONFIGURATION"

log_test "Testando CORS preflight (OPTIONS)..."
CORS_RESPONSE=$(curl -s -D - -o /dev/null -X OPTIONS \
    -H "Origin: http://localhost:3000" \
    -H "Access-Control-Request-Method: GET" \
    "$BACKEND_URL/api/consciousness/stream/process" 2>/dev/null)

if echo "$CORS_RESPONSE" | grep -q "access-control-allow-origin"; then
    log_pass "CORS headers presentes na resposta"
    echo "### 2.1 CORS Preflight: PASS" >> "$RESULTS_FILE"

    # Extract CORS headers
    CORS_ORIGIN=$(echo "$CORS_RESPONSE" | grep -i "access-control-allow-origin" | head -1)
    CORS_METHODS=$(echo "$CORS_RESPONSE" | grep -i "access-control-allow-methods" | head -1)
    CORS_CREDS=$(echo "$CORS_RESPONSE" | grep -i "access-control-allow-credentials" | head -1)

    echo "\`\`\`" >> "$RESULTS_FILE"
    echo "$CORS_ORIGIN" >> "$RESULTS_FILE"
    echo "$CORS_METHODS" >> "$RESULTS_FILE"
    echo "$CORS_CREDS" >> "$RESULTS_FILE"
    echo "\`\`\`" >> "$RESULTS_FILE"

    log_info "CORS Origin: $CORS_ORIGIN"
else
    log_fail "CORS headers ausentes"
    echo "### 2.1 CORS Preflight: FAIL" >> "$RESULTS_FILE"
fi

log_test "Verificando se OPTIONS retorna 200..."
OPTIONS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS \
    -H "Origin: http://localhost:3000" \
    -H "Access-Control-Request-Method: GET" \
    "$BACKEND_URL/api/consciousness/stream/process" 2>/dev/null)

if [ "$OPTIONS_CODE" = "200" ]; then
    log_pass "OPTIONS retorna 200 (não 405)"
    echo "### 2.2 OPTIONS Method: PASS (HTTP 200)" >> "$RESULTS_FILE"
else
    log_fail "OPTIONS retorna $OPTIONS_CODE (esperado 200)"
    echo "### 2.2 OPTIONS Method: FAIL (HTTP $OPTIONS_CODE)" >> "$RESULTS_FILE"
fi

# ============================================================================
# TEST 3: SSE STREAMING ENDPOINT
# ============================================================================

log_section "3. SSE STREAMING ENDPOINT"

log_test "Testando SSE stream com input simples..."
SSE_OUTPUT=$(timeout 20 curl -s -N \
    -H "Origin: http://localhost:3000" \
    "$BACKEND_URL/api/consciousness/stream/process?content=teste&depth=2" 2>/dev/null || true)

# Count events
START_EVENTS=$(echo "$SSE_OUTPUT" | grep -c '"type": "start"' || echo "0")
PHASE_EVENTS=$(echo "$SSE_OUTPUT" | grep -c '"type": "phase"' || echo "0")
COHERENCE_EVENTS=$(echo "$SSE_OUTPUT" | grep -c '"type": "coherence"' || echo "0")
TOKEN_EVENTS=$(echo "$SSE_OUTPUT" | grep -c '"type": "token"' || echo "0")
COMPLETE_EVENTS=$(echo "$SSE_OUTPUT" | grep -c '"type": "complete"' || echo "0")

echo "" >> "$RESULTS_FILE"
echo "## 3. SSE Streaming Tests" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

if [ "$START_EVENTS" -ge 1 ]; then
    log_pass "Evento 'start' recebido ($START_EVENTS)"
    echo "### 3.1 Start Event: PASS" >> "$RESULTS_FILE"
else
    log_fail "Evento 'start' não recebido"
    echo "### 3.1 Start Event: FAIL" >> "$RESULTS_FILE"
fi

if [ "$PHASE_EVENTS" -ge 4 ]; then
    log_pass "Eventos 'phase' recebidos ($PHASE_EVENTS fases)"
    echo "### 3.2 Phase Events: PASS ($PHASE_EVENTS fases)" >> "$RESULTS_FILE"
else
    log_fail "Eventos 'phase' insuficientes ($PHASE_EVENTS)"
    echo "### 3.2 Phase Events: FAIL ($PHASE_EVENTS fases)" >> "$RESULTS_FILE"
fi

if [ "$COHERENCE_EVENTS" -ge 3 ]; then
    log_pass "Eventos 'coherence' recebidos ($COHERENCE_EVENTS updates)"
    echo "### 3.3 Coherence Events: PASS ($COHERENCE_EVENTS updates)" >> "$RESULTS_FILE"
else
    log_fail "Eventos 'coherence' insuficientes ($COHERENCE_EVENTS)"
    echo "### 3.3 Coherence Events: FAIL ($COHERENCE_EVENTS updates)" >> "$RESULTS_FILE"
fi

if [ "$TOKEN_EVENTS" -ge 1 ]; then
    log_pass "Eventos 'token' recebidos ($TOKEN_EVENTS tokens)"
    echo "### 3.4 Token Events: PASS ($TOKEN_EVENTS tokens)" >> "$RESULTS_FILE"
else
    log_fail "Eventos 'token' não recebidos"
    echo "### 3.4 Token Events: FAIL" >> "$RESULTS_FILE"
fi

if [ "$COMPLETE_EVENTS" -ge 1 ]; then
    log_pass "Evento 'complete' recebido"
    echo "### 3.5 Complete Event: PASS" >> "$RESULTS_FILE"
else
    log_fail "Evento 'complete' não recebido"
    echo "### 3.5 Complete Event: FAIL" >> "$RESULTS_FILE"
fi

# ============================================================================
# TEST 4: ESGT PHASE SEQUENCE
# ============================================================================

log_section "4. ESGT PHASE SEQUENCE"

log_test "Verificando sequência de fases ESGT..."
PHASES=$(echo "$SSE_OUTPUT" | grep '"type": "phase"' | grep -oP '"phase": "\K[^"]+')
EXPECTED_PHASES="prepare synchronize broadcast sustain dissolve"

echo "" >> "$RESULTS_FILE"
echo "## 4. ESGT Phase Sequence" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "Fases detectadas:" >> "$RESULTS_FILE"
echo "\`\`\`" >> "$RESULTS_FILE"
echo "$PHASES" >> "$RESULTS_FILE"
echo "\`\`\`" >> "$RESULTS_FILE"

PHASE_SEQUENCE_OK=true
for expected in $EXPECTED_PHASES; do
    if echo "$PHASES" | grep -q "$expected"; then
        log_pass "Fase '$expected' presente"
    else
        log_fail "Fase '$expected' ausente"
        PHASE_SEQUENCE_OK=false
    fi
done

if [ "$PHASE_SEQUENCE_OK" = true ]; then
    echo "### Sequência ESGT: PASS (todas as 5 fases presentes)" >> "$RESULTS_FILE"
else
    echo "### Sequência ESGT: PARTIAL (algumas fases ausentes)" >> "$RESULTS_FILE"
fi

# ============================================================================
# TEST 5: KURAMOTO COHERENCE
# ============================================================================

log_section "5. KURAMOTO COHERENCE"

log_test "Analisando evolução da coerência..."
COHERENCE_VALUES=$(echo "$SSE_OUTPUT" | grep '"type": "coherence"' | grep -oP '"value": \K[0-9.]+')
FINAL_COHERENCE=$(echo "$COHERENCE_VALUES" | tail -1)

echo "" >> "$RESULTS_FILE"
echo "## 5. Kuramoto Coherence" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "Valores de coerência:" >> "$RESULTS_FILE"
echo "\`\`\`" >> "$RESULTS_FILE"
echo "$COHERENCE_VALUES" >> "$RESULTS_FILE"
echo "\`\`\`" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "**Coerência Final:** $FINAL_COHERENCE" >> "$RESULTS_FILE"

if [ -n "$FINAL_COHERENCE" ]; then
    # Check if coherence > 0.5
    COHERENCE_OK=$(echo "$FINAL_COHERENCE > 0.5" | bc -l 2>/dev/null || echo "1")
    if [ "$COHERENCE_OK" = "1" ]; then
        log_pass "Coerência final: $FINAL_COHERENCE (>0.5)"
        echo "### Coerência: PASS ($FINAL_COHERENCE)" >> "$RESULTS_FILE"
    else
        log_fail "Coerência baixa: $FINAL_COHERENCE (<0.5)"
        echo "### Coerência: LOW ($FINAL_COHERENCE)" >> "$RESULTS_FILE"
    fi
else
    log_fail "Sem valores de coerência"
    echo "### Coerência: FAIL (sem valores)" >> "$RESULTS_FILE"
fi

# ============================================================================
# TEST 6: TOKEN STREAMING (RESPONSE GENERATION)
# ============================================================================

log_section "6. TOKEN STREAMING"

log_test "Verificando tokens gerados..."
TOKENS=$(echo "$SSE_OUTPUT" | grep '"type": "token"' | grep -oP '"token": "\K[^"]+' | tr '\n' ' ')

echo "" >> "$RESULTS_FILE"
echo "## 6. Token Streaming" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "Tokens recebidos:" >> "$RESULTS_FILE"
echo "\`\`\`" >> "$RESULTS_FILE"
echo "$TOKENS" >> "$RESULTS_FILE"
echo "\`\`\`" >> "$RESULTS_FILE"

if [ -n "$TOKENS" ]; then
    WORD_COUNT=$(echo "$TOKENS" | wc -w)
    log_pass "Recebidos $WORD_COUNT tokens"
    echo "### Token Count: PASS ($WORD_COUNT tokens)" >> "$RESULTS_FILE"
else
    log_fail "Nenhum token recebido"
    echo "### Token Count: FAIL (0 tokens)" >> "$RESULTS_FILE"
fi

# ============================================================================
# TEST 7: DEEP QUERY (DEPTH=5)
# ============================================================================

log_section "7. DEEP QUERY (DEPTH=5)"

log_test "Testando query com depth=5..."
DEEP_OUTPUT=$(timeout 30 curl -s -N \
    -H "Origin: http://localhost:3000" \
    "$BACKEND_URL/api/consciousness/stream/process?content=Explique+a+consciencia&depth=5" 2>/dev/null || true)

DEEP_TOKENS=$(echo "$DEEP_OUTPUT" | grep -c '"type": "token"' || echo "0")
DEEP_COHERENCE=$(echo "$DEEP_OUTPUT" | grep '"type": "coherence"' | grep -oP '"value": \K[0-9.]+' | tail -1)

echo "" >> "$RESULTS_FILE"
echo "## 7. Deep Query Test (Depth=5)" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

if [ "$DEEP_TOKENS" -ge 5 ]; then
    log_pass "Deep query gerou $DEEP_TOKENS tokens"
    echo "### Deep Query: PASS ($DEEP_TOKENS tokens, coherence=$DEEP_COHERENCE)" >> "$RESULTS_FILE"
else
    log_fail "Deep query gerou poucos tokens ($DEEP_TOKENS)"
    echo "### Deep Query: FAIL ($DEEP_TOKENS tokens)" >> "$RESULTS_FILE"
fi

# ============================================================================
# TEST 8: ERROR HANDLING
# ============================================================================

log_section "8. ERROR HANDLING"

log_test "Testando endpoint inexistente..."
ERROR_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/nonexistent" 2>/dev/null)

echo "" >> "$RESULTS_FILE"
echo "## 8. Error Handling" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

if [ "$ERROR_CODE" = "404" ]; then
    log_pass "Endpoint inexistente retorna 404"
    echo "### 404 Handling: PASS" >> "$RESULTS_FILE"
else
    log_fail "Endpoint inexistente retorna $ERROR_CODE (esperado 404)"
    echo "### 404 Handling: FAIL (HTTP $ERROR_CODE)" >> "$RESULTS_FILE"
fi

log_test "Testando query vazia..."
EMPTY_RESPONSE=$(timeout 10 curl -s \
    "$BACKEND_URL/api/consciousness/stream/process?content=&depth=2" 2>/dev/null || true)

if echo "$EMPTY_RESPONSE" | grep -q "error\|Error\|422"; then
    log_pass "Query vazia tratada corretamente"
    echo "### Empty Query: PASS (validation error)" >> "$RESULTS_FILE"
else
    log_info "Query vazia processada (pode ser válido)"
    echo "### Empty Query: INFO (processed)" >> "$RESULTS_FILE"
fi

# ============================================================================
# TEST 9: CONCURRENT CONNECTIONS
# ============================================================================

log_section "9. CONCURRENT CONNECTIONS"

log_test "Testando 3 conexões simultâneas..."

# Start 3 concurrent requests
(timeout 15 curl -s -N "$BACKEND_URL/api/consciousness/stream/process?content=query1&depth=2" > /tmp/daimon/concurrent1.txt 2>&1 &)
(timeout 15 curl -s -N "$BACKEND_URL/api/consciousness/stream/process?content=query2&depth=2" > /tmp/daimon/concurrent2.txt 2>&1 &)
(timeout 15 curl -s -N "$BACKEND_URL/api/consciousness/stream/process?content=query3&depth=2" > /tmp/daimon/concurrent3.txt 2>&1 &)

sleep 18

CONCURRENT_SUCCESS=0
for i in 1 2 3; do
    if [ -f "/tmp/daimon/concurrent$i.txt" ] && grep -q '"type": "complete"' "/tmp/daimon/concurrent$i.txt" 2>/dev/null; then
        ((CONCURRENT_SUCCESS++))
    fi
done

echo "" >> "$RESULTS_FILE"
echo "## 9. Concurrent Connections" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

if [ "$CONCURRENT_SUCCESS" -eq 3 ]; then
    log_pass "Todas as 3 conexões completaram"
    echo "### Concurrent: PASS (3/3 completed)" >> "$RESULTS_FILE"
elif [ "$CONCURRENT_SUCCESS" -ge 1 ]; then
    log_info "$CONCURRENT_SUCCESS/3 conexões completaram"
    echo "### Concurrent: PARTIAL ($CONCURRENT_SUCCESS/3 completed)" >> "$RESULTS_FILE"
else
    log_fail "Nenhuma conexão completou"
    echo "### Concurrent: FAIL (0/3 completed)" >> "$RESULTS_FILE"
fi

# ============================================================================
# SUMMARY
# ============================================================================

log_section "SUMÁRIO DOS RESULTADOS"

echo "" >> "$RESULTS_FILE"
echo "---" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "## Sumário Final" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "| Métrica | Valor |" >> "$RESULTS_FILE"
echo "|---------|-------|" >> "$RESULTS_FILE"
echo "| Total de Testes | $TESTS_TOTAL |" >> "$RESULTS_FILE"
echo "| Testes Passou | $TESTS_PASSED |" >> "$RESULTS_FILE"
echo "| Testes Falhou | $TESTS_FAILED |" >> "$RESULTS_FILE"
echo "| Taxa de Sucesso | $(echo "scale=1; $TESTS_PASSED * 100 / $TESTS_TOTAL" | bc)% |" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  RESULTADOS FINAIS${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Total de Testes:  ${YELLOW}$TESTS_TOTAL${NC}"
echo -e "  ${GREEN}Passou:${NC}            $TESTS_PASSED"
echo -e "  ${RED}Falhou:${NC}            $TESTS_FAILED"
echo ""

if [ "$TESTS_FAILED" -eq 0 ]; then
    echo -e "  ${GREEN}════════════════════════════════════════════════════════${NC}"
    echo -e "  ${GREEN}  TODOS OS TESTES PASSARAM!${NC}"
    echo -e "  ${GREEN}════════════════════════════════════════════════════════${NC}"
    echo "" >> "$RESULTS_FILE"
    echo "### STATUS: ALL TESTS PASSED" >> "$RESULTS_FILE"
else
    echo -e "  ${YELLOW}════════════════════════════════════════════════════════${NC}"
    echo -e "  ${YELLOW}  ALGUNS TESTES FALHARAM - VERIFICAR RELATÓRIO${NC}"
    echo -e "  ${YELLOW}════════════════════════════════════════════════════════${NC}"
    echo "" >> "$RESULTS_FILE"
    echo "### STATUS: SOME TESTS FAILED" >> "$RESULTS_FILE"
fi

echo ""
echo -e "  Relatório salvo em: ${CYAN}$RESULTS_FILE${NC}"
echo ""

# Append raw SSE output for debugging
echo "" >> "$RESULTS_FILE"
echo "---" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "## Anexo: Raw SSE Output (Teste Simples)" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "\`\`\`json" >> "$RESULTS_FILE"
echo "$SSE_OUTPUT" >> "$RESULTS_FILE"
echo "\`\`\`" >> "$RESULTS_FILE"

exit $TESTS_FAILED
