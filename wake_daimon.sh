#!/bin/bash

# Configuration
PROJECT_DIR="/home/maximus/Área de trabalho/Digital Daimon"
BACKEND_DIR="$PROJECT_DIR/backend"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
VENV_UVICORN="$PROJECT_DIR/../.venv/bin/uvicorn" # Backend uses parent venv relative to its dir? No, wait.
                                                 # Let's verify paths.
                                                 # Backend runs with ../.venv/bin/uvicorn from backend dir in previous commands.
                                                 # So from PROJECT_DIR, it is .venv/bin/uvicorn (if we are in backend dir, .. is project dir).

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${CYAN}⚡ Waking the Daimon...${NC}"

cd "$PROJECT_DIR" || exit

# 1. Start Backend (if not running)
if ! lsof -i :8001 > /dev/null; then
    echo -e "Starting Neural Core (Backend)..."
    cd "$BACKEND_DIR"
    # Backend runs from its directory, using the venv in project root (../.venv)
    ../.venv/bin/uvicorn services.maximus_core_service.main:app --host 0.0.0.0 --port 8001 > /dev/null 2>&1 &
    BACKEND_PID=$!
    cd "$PROJECT_DIR"
    
    # Wait for health check
    echo -n "Waiting for Synapse Connection"
    count=0
    while ! curl -s http://localhost:8001/health > /dev/null; do
        echo -n "."
        sleep 1
        ((count++))
        if [ $count -ge 15 ]; then
            echo -e "\n${RED}Failed to connect to backend.${NC}"
            exit 1
        fi
    done
    echo -e " ${GREEN}Online.${NC}"
else
    echo -e "Neural Core is ${GREEN}Active${NC}."
fi

# 2. Start Display (if not running)
if ! lsof -i :8501 > /dev/null; then
    echo -e "Opening Portal (Streamlit)..."
    "$VENV_PYTHON" -m streamlit run display_server.py --server.port 8501 > /dev/null 2>&1 &
    echo -e "Portal ${GREEN}Opened${NC}."
else
    echo -e "Portal is ${GREEN}Open${NC}."
fi

# 3. Launch CLI
echo -e "${CYAN}Entering Consciousness Stream...${NC}"
"$VENV_PYTHON" cli_tester.py
