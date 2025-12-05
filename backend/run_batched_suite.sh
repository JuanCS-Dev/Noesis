#!/bin/bash

# Definition of the Test Environment
export PYTHONPATH=$PYTHONPATH:"/home/maximus/Área de trabalho/Digital Daimon/backend"
VENV="/home/maximus/Área de trabalho/Digital Daimon/.venv/bin/pytest"
BASE_DIR="services/maximus_core_service"
TEST_DIR="$BASE_DIR/tests/unit"

echo "=================================================="
echo "   STARTING SURGICAL TEST EXECUTION PROTOCOL"
echo "   Strategy: Granular batches to isolate memory leaks"
echo "=================================================="

run_batch() {
    NAME=$1
    TARGET=$2
    COV_TARGET=$3
    LOG_FILE=$4
    
    echo "--------------------------------------------------"
    echo "[Batch $NAME] Starting..."
    "$VENV" $TARGET \
        --cov="$COV_TARGET" \
        --cov-report=xml:coverage_$NAME.xml \
        --cov-report=term \
        --continue-on-collection-errors \
        > $LOG_FILE 2>&1
    
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo "[Batch $NAME] SUCCESS."
    else
        echo "[Batch $NAME] FINISHED with Exit Code: $EXIT_CODE (Check $LOG_FILE)"
    fi
    sleep 2 # Cooldown
}

# ----------------------------------------------------------------
# BATCH 1: CONSCIOUSNESS DECONSTRUCTION
# ----------------------------------------------------------------

# 1.1 Exocortex (Core Logic)
run_batch "1_exocortex" \
    "$TEST_DIR/consciousness/exocortex" \
    "$BASE_DIR/src/consciousness/exocortex" \
    "log_1_exocortex.txt"

# 1.2 TIG (Fabric/Sync)
run_batch "2_tig" \
    "$TEST_DIR/consciousness/tig" \
    "$BASE_DIR/src/consciousness/tig" \
    "log_2_tig.txt"

# 1.3 Neuromodulation
run_batch "3_neuromodulation" \
    "$TEST_DIR/consciousness/neuromodulation" \
    "$BASE_DIR/src/consciousness/neuromodulation" \
    "log_3_neuromodulation.txt"

# 1.4 REST of Consciousness (EXCLUDING the killer test)
echo "[Batch 4] Consciousness General (Safe Mode)..."
"$VENV" "$TEST_DIR/consciousness" \
    --ignore="$TEST_DIR/consciousness/test_biomimetic_safety_bridge.py" \
    --ignore="$TEST_DIR/consciousness/exocortex" \
    --ignore="$TEST_DIR/consciousness/tig" \
    --ignore="$TEST_DIR/consciousness/neuromodulation" \
    --cov="$BASE_DIR/src/consciousness" \
    --cov-report=xml:coverage_4_general.xml \
    --cov-report=term \
    --continue-on-collection-errors \
    > log_4_conscious_general.txt 2>&1
echo "[Batch 4] Complete."

# 1.5 The KILLER (Isolated)
echo "[Batch 5] ISOLATED RUN: Biomimetic Safety Bridge..."
"$VENV" "$TEST_DIR/consciousness/test_biomimetic_safety_bridge.py" \
    --cov="$BASE_DIR/src/consciousness" \
    --cov-report=xml:coverage_5_biomimetic.xml \
    --cov-report=term \
    > log_5_killer.txt 2>&1
echo "[Batch 5] Complete."

# ----------------------------------------------------------------
# BATCH 2: REGULATORY (Compliance/Governance)
# ----------------------------------------------------------------
run_batch "6_regulatory" \
    "$TEST_DIR/compliance $TEST_DIR/governance $TEST_DIR/ethics_engine" \
    "$BASE_DIR/compliance" \
    "log_6_regulatory.txt"

# ----------------------------------------------------------------
# BATCH 3: INFRASTRUCTURE 
# ----------------------------------------------------------------
run_batch "7_infra" \
    "$TEST_DIR/performance $TEST_DIR/training $TEST_DIR/federated_learning $TEST_DIR/utils $TEST_DIR/hitl" \
    "$BASE_DIR/performance" \
    "log_7_infra.txt"

echo "=================================================="
echo "   SURGICAL EXECUTION COMPLETE"
echo "=================================================="
