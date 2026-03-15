#!/bin/bash
# ============================================================================
# Nightly Synthetic Data Factory Run
#
# Crontab entry (Linux):
#   0 22 * * * /opt/vilseckki/factory/cron/nightly-run.sh
#
# Task Scheduler entry (Windows):
#   Trigger: Daily at 22:00
#   Action: bash.exe -c "/c/VilseckKI/factory/cron/nightly-run.sh"
#
# This script:
# 1. Checks if a generation is already running (prevents double-runs)
# 2. Picks the highest-priority config that needs regeneration
# 3. Runs the pipeline with a time limit (kills at 06:00)
# 4. Logs everything
# ============================================================================

set -euo pipefail

# ─── Configuration ────────────────────────────────────────────────
FACTORY_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOCKFILE="${FACTORY_DIR}/cron/.factory.lock"
CONFIGS_DIR="${FACTORY_DIR}/configs"
LOG_DIR="${FACTORY_DIR}/logs"
VENV_DIR="${FACTORY_DIR}/venv"
MAX_RUNTIME_HOURS=8  # Kill after 8 hours (22:00 → 06:00)

# ─── Lock Check ───────────────────────────────────────────────────
if [ -f "$LOCKFILE" ]; then
    PID=$(cat "$LOCKFILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Factory already running (PID $PID). Exiting."
        exit 0
    else
        echo "Stale lockfile found (PID $PID not running). Cleaning up."
        rm -f "$LOCKFILE"
    fi
fi

# Create lockfile
echo $$ > "$LOCKFILE"
trap "rm -f $LOCKFILE" EXIT

# ─── Activate Python Environment ─────────────────────────────────
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate" 2>/dev/null || source "$VENV_DIR/Scripts/activate" 2>/dev/null
fi

# ─── Find Next Config to Run ─────────────────────────────────────
# Priority: configs are processed in alphabetical order.
# A config is "due" if its output doesn't exist or is older than the config file.

SELECTED_CONFIG=""
for config_file in "$CONFIGS_DIR"/*.yaml; do
    [ -f "$config_file" ] || continue

    config_name=$(basename "$config_file" .yaml)

    # Skip test configs
    if [[ "$config_name" == test-* ]]; then
        continue
    fi

    # Check if output exists and is newer than config
    output_dir="${FACTORY_DIR}/output"
    latest_link="${output_dir}/${config_name}/latest"

    if [ ! -L "$latest_link" ] || [ "$config_file" -nt "$latest_link" ]; then
        SELECTED_CONFIG="$config_file"
        echo "Selected config: $config_name (needs generation)"
        break
    else
        echo "Skipping $config_name (output is current)"
    fi
done

if [ -z "$SELECTED_CONFIG" ]; then
    echo "All configs are up to date. Nothing to generate."
    exit 0
fi

# ─── Run Pipeline with Time Limit ────────────────────────────────
echo "Starting generation at $(date)"
echo "Config: $SELECTED_CONFIG"
echo "Max runtime: ${MAX_RUNTIME_HOURS}h"

cd "$FACTORY_DIR"
timeout "${MAX_RUNTIME_HOURS}h" python run.py "$SELECTED_CONFIG" 2>&1 | \
    tee -a "${LOG_DIR}/$(date +%Y-%m-%d)_nightly.log"

EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 124 ]; then
    echo "WARNING: Generation timed out after ${MAX_RUNTIME_HOURS}h"
elif [ $EXIT_CODE -ne 0 ]; then
    echo "ERROR: Generation failed with exit code $EXIT_CODE"
else
    echo "Generation completed successfully at $(date)"
fi

exit $EXIT_CODE
