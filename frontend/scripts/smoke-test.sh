#!/bin/bash
# NOESIS Pre-Demo Smoke Test
# Run this before recording the hackathon video

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                               ║${NC}"
echo -e "${CYAN}║   ${BOLD}NOESIS PRE-DEMO SMOKE TEST${NC}${CYAN}                                 ║${NC}"
echo -e "${CYAN}║   Google DeepMind Hackathon                                   ║${NC}"
echo -e "${CYAN}║                                                               ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if services are running
echo -e "${BOLD}[1/5] Checking Backend Services...${NC}"

# MAXIMUS Core Service (Critical)
if curl -s --max-time 3 http://localhost:8001/api/consciousness/reactive-fabric/metrics > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} MAXIMUS Core Service (8001) - ONLINE"
    MAXIMUS_OK=true
else
    echo -e "  ${RED}✗${NC} MAXIMUS Core Service (8001) - OFFLINE"
    MAXIMUS_OK=false
fi

# Metacognitive Reflector (Optional)
if curl -s --max-time 3 http://localhost:8002/api/reflector/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Metacognitive Reflector (8002) - ONLINE"
else
    echo -e "  ${YELLOW}⚠${NC} Metacognitive Reflector (8002) - OFFLINE (Tribunal will show offline)"
fi

# API Gateway (Optional)
if curl -s --max-time 3 http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} API Gateway (8000) - ONLINE"
else
    echo -e "  ${YELLOW}⚠${NC} API Gateway (8000) - OFFLINE"
fi

echo ""
echo -e "${BOLD}[2/5] Checking Frontend...${NC}"

# Frontend
if curl -s --max-time 5 http://localhost:3000 > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Frontend (3000) - ONLINE"
    FRONTEND_OK=true
else
    echo -e "  ${RED}✗${NC} Frontend (3000) - OFFLINE"
    FRONTEND_OK=false
fi

echo ""
echo -e "${BOLD}[3/5] Testing SSE Streaming...${NC}"

# Test SSE endpoint (critical for demo)
SSE_RESPONSE=$(curl -s --max-time 3 -H "Accept: text/event-stream" \
    "http://localhost:8001/api/consciousness/stream/sse" 2>&1 | head -1)
if [[ $SSE_RESPONSE == *"data:"* ]] || [[ $? -eq 0 ]]; then
    echo -e "  ${GREEN}✓${NC} SSE Streaming - FUNCTIONAL"
else
    echo -e "  ${YELLOW}⚠${NC} SSE Streaming - Could not verify"
fi

echo ""
echo -e "${BOLD}[4/5] Testing WebSocket...${NC}"

# WebSocket check (non-critical)
if command -v websocat &> /dev/null; then
    WS_TEST=$(timeout 2 websocat -t ws://localhost:8001/api/consciousness/ws 2>&1 || true)
    if [[ ! -z "$WS_TEST" ]]; then
        echo -e "  ${GREEN}✓${NC} WebSocket - FUNCTIONAL"
    else
        echo -e "  ${YELLOW}⚠${NC} WebSocket - Could not verify (non-critical)"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} WebSocket - Skipped (websocat not installed)"
fi

echo ""
echo -e "${BOLD}[5/5] Checking Data Quality...${NC}"

# Check metrics data structure
if [ "$MAXIMUS_OK" = true ]; then
    METRICS=$(curl -s --max-time 3 http://localhost:8001/api/consciousness/reactive-fabric/metrics)
    if echo "$METRICS" | grep -q "health_score"; then
        echo -e "  ${GREEN}✓${NC} Metrics Data - VALID STRUCTURE"
    else
        echo -e "  ${YELLOW}⚠${NC} Metrics Data - Unexpected structure"
    fi
fi

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"

# Final verdict
if [ "$MAXIMUS_OK" = true ] && [ "$FRONTEND_OK" = true ]; then
    echo ""
    echo -e "${GREEN}${BOLD}  ✓ ALL CRITICAL SYSTEMS OPERATIONAL${NC}"
    echo -e "${GREEN}${BOLD}  → READY FOR DEMO RECORDING${NC}"
    echo ""
    echo -e "  Open ${CYAN}http://localhost:3000${NC} in your browser"
    echo ""
    exit 0
else
    echo ""
    echo -e "${RED}${BOLD}  ✗ CRITICAL SERVICES OFFLINE${NC}"
    echo ""
    if [ "$MAXIMUS_OK" = false ]; then
        echo -e "  Run: ${YELLOW}./wake_daimon.sh${NC}"
        echo -e "  Or:  ${YELLOW}cd backend && docker-compose up maximus_core_service${NC}"
    fi
    if [ "$FRONTEND_OK" = false ]; then
        echo -e "  Run: ${YELLOW}cd frontend && npm run dev${NC}"
    fi
    echo ""
    exit 1
fi

