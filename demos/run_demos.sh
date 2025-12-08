#!/bin/bash
# =============================================================================
# NOESIS DEMO RUNNER
# =============================================================================
# Run all demos in sequence for the hackathon presentation

set -e
cd "$(dirname "$0")/.."

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                                      ║${NC}"
echo -e "${CYAN}║   🧠 NOESIS DEMONSTRATION SUITE                                     ║${NC}"
echo -e "${CYAN}║   Google DeepMind Hackathon 2025                                    ║${NC}"
echo -e "${CYAN}║                                                                      ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}Available demos:${NC}"
echo "  1. consciousness_demo.py  - Full interactive demo"
echo "  2. benchmark_visual.py    - LLM performance benchmark"
echo "  3. tribunal_showcase.py   - Ethical reasoning showcase"
echo ""

read -p "Select demo (1-3) or 'all': " choice

case $choice in
    1)
        python demos/consciousness_demo.py
        ;;
    2)
        python demos/benchmark_visual.py
        ;;
    3)
        python demos/tribunal_showcase.py
        ;;
    all)
        echo -e "\n${GREEN}Running all demos...${NC}\n"
        python demos/benchmark_visual.py
        read -p "Press ENTER for next demo..."
        python demos/tribunal_showcase.py
        read -p "Press ENTER for full demo..."
        python demos/consciousness_demo.py
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo -e "\n${GREEN}✓ Demo complete${NC}\n"
