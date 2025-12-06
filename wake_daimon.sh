#!/bin/bash
set -euo pipefail

# Configuration
PROJECT_DIR="/home/maximus/Área de trabalho/Digital Daimon"
SERVICES_DIR="$PROJECT_DIR/backend/services"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
VENV_PIP="$PROJECT_DIR/.venv/bin/pip"
LOG_DIR="/tmp/daimon"

# Portas do Daimon
PORTS=(8000 8001 3000)

# Initialize PYTHONPATH if not set
export PYTHONPATH="${PYTHONPATH:-}"

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}⚡ Waking the Daimon...${NC}"

# Função para limpar portas
clean_ports() {
    echo -e "${YELLOW}🧹 Limpando portas...${NC}"
    for port in "${PORTS[@]}"; do
        pid=$(lsof -t -i :"$port" 2>/dev/null || true)
        if [ -n "$pid" ]; then
            echo -e "  Matando processo na porta $port (PID: $pid)"
            kill -9 $pid 2>/dev/null || true
            sleep 0.5
        fi
    done
    # Também mata containers Docker que podem estar bloqueando
    docker stop api_gateway 2>/dev/null || true
    echo -e "${GREEN}✓ Portas limpas${NC}"
}

# Create log directory
mkdir -p "$LOG_DIR"

# Limpar portas antes de iniciar
clean_ports

# Function to install service if needed (for src/ layout packages)
install_service() {
    local service_dir="$1"
    local service_name="$2"

    if [ -f "$service_dir/pyproject.toml" ] && [ -d "$service_dir/src" ]; then
        # New src/ layout - install as package
        if ! "$VENV_PYTHON" -c "import $service_name" 2>/dev/null; then
            echo -e "${YELLOW}Installing $service_name...${NC}"
            "$VENV_PIP" install -e "$service_dir" -q
        fi
    fi
}

# Function to start a service
start_service() {
    local name="$1"
    local port="$2"
    local module_path="$3"
    local service_dir="$SERVICES_DIR/$name"

    if ! lsof -i :"$port" > /dev/null 2>&1; then
        echo -e "Starting $name on :$port..."

        # Install if it's a src/ layout package
        install_service "$service_dir" "$name"

        # Start using package path (works because package is installed)
        "$VENV_PYTHON" -m uvicorn "$module_path" \
            --host 0.0.0.0 --port "$port" \
            > "$LOG_DIR/${name}.log" 2>&1 &

        # Wait for health check
        echo -n "Waiting for $name"
        count=0
        while ! curl -s "http://localhost:$port/health" > /dev/null 2>&1; do
            echo -n "."
            sleep 1
            ((count++))
            if [ $count -ge 15 ]; then
                echo -e "\n${RED}Failed to start $name. Check $LOG_DIR/${name}.log${NC}"
                tail -20 "$LOG_DIR/${name}.log"
                exit 1
            fi
        done
        echo -e " ${GREEN}Online.${NC}"
    else
        echo -e "$name is ${GREEN}Active${NC} on :$port"
    fi
}

# Start maximus_core_service (Tier 4 - still using old layout, needs PYTHONPATH)
if ! lsof -i :8001 > /dev/null 2>&1; then
    echo -e "Starting Neural Core (Backend on :8001)..."
    cd "$SERVICES_DIR/maximus_core_service"
    export PYTHONPATH="$SERVICES_DIR/maximus_core_service:$PYTHONPATH"
    "$VENV_PYTHON" -m uvicorn main:app --host 0.0.0.0 --port 8001 > "$LOG_DIR/maximus_core_service.log" 2>&1 &
    cd "$PROJECT_DIR"

    echo -n "Waiting for Neural Core"
    count=0
    while ! curl -s http://localhost:8001/v1/health > /dev/null 2>&1; do
        echo -n "."
        sleep 1
        ((count++))
        if [ $count -ge 15 ]; then
            echo -e "\n${RED}Failed to start backend. Check $LOG_DIR/maximus_core_service.log${NC}"
            tail -20 "$LOG_DIR/maximus_core_service.log"
            exit 1
        fi
    done
    echo -e " ${GREEN}Online.${NC}"
else
    echo -e "Neural Core is ${GREEN}Active${NC} on :8001"
fi

# Start API Gateway (Tier 1 - migrated to src/ layout)
start_service "api_gateway" 8000 "api_gateway.api.routes:app"

echo -e "${GREEN}System ready.${NC} Backend :8001 | Gateway :8000"

# Launch CLI
echo -e "${CYAN}Entering Consciousness Stream...${NC}"
"$VENV_PYTHON" "$PROJECT_DIR/cli_tester.py"
