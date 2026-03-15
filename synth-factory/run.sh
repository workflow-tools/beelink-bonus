#!/usr/bin/env bash
# ============================================================================
# Synth-Factory Launch Script
# ============================================================================
#
# One-command deployment and generation for the VilseckKI data factory.
#
# Usage:
#   ./run.sh housing-management-jp         # Full run with monitoring
#   ./run.sh housing-management-jp --resume # Resume interrupted run
#   ./run.sh --dry-run housing-management-jp  # Test with 5 docs
#   ./run.sh --health                        # Check Ollama status
#   ./run.sh --list                          # List available configs
#   ./run.sh --status                        # Check running jobs
#
# Prerequisites:
#   - Ollama running locally (ollama serve)
#   - Model pulled: ollama pull llama3.1:70b-instruct-q4_K_M
#   - Python 3.10+ with: pip install pydantic pyyaml httpx pandas
#
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ─── Config ────────────────────────────────────────────────────────
CONFIGS_DIR="$SCRIPT_DIR/configs"
OUTPUT_DIR="$SCRIPT_DIR/output"
LOGS_DIR="$SCRIPT_DIR/logs"
PID_DIR="$SCRIPT_DIR/.pids"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'  # No Color

# ─── Functions ─────────────────────────────────────────────────────

print_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════╗"
    echo "║  VilseckKI Synth-Factory                     ║"
    echo "║  Long-Text Document Generation Pipeline      ║"
    echo "╚══════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_dependencies() {
    local missing=0

    # Python
    if ! command -v python3 &>/dev/null; then
        echo -e "${RED}✗ python3 not found${NC}"
        missing=1
    else
        echo -e "${GREEN}✓ python3 $(python3 --version 2>&1 | awk '{print $2}')${NC}"
    fi

    # Python packages
    for pkg in pydantic yaml httpx pandas; do
        if python3 -c "import $pkg" 2>/dev/null; then
            echo -e "${GREEN}✓ $pkg${NC}"
        else
            echo -e "${RED}✗ $pkg not installed${NC}"
            missing=1
        fi
    done

    # Ollama
    if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
        local models
        models=$(curl -sf http://localhost:11434/api/tags | python3 -c "import sys,json; [print(f'  - {m[\"name\"]}') for m in json.load(sys.stdin).get('models',[])]" 2>/dev/null || echo "  (could not list models)")
        echo -e "${GREEN}✓ Ollama is running${NC}"
        echo -e "${BLUE}  Available models:${NC}"
        echo "$models"
    else
        echo -e "${RED}✗ Ollama is not running (start with: ollama serve)${NC}"
        missing=1
    fi

    return $missing
}

estimate_time() {
    local config_file="$1"
    local records
    records=$(python3 -c "
import yaml
with open('$config_file') as f:
    cfg = yaml.safe_load(f)
doc_tables = cfg.get('document_tables', [])
doc_types = {dt['name']: dt for dt in cfg.get('document_types', [])}
total_segments = 0
total_records = 0
for dt in doc_tables:
    total_records += dt['records']
    dtype = doc_types.get(dt['document_type'], {})
    segs = dtype.get('segments', [])
    for seg in segs:
        if seg.get('segment_type') == 'list_field':
            avg_items = ((seg.get('list_min', 1) + seg.get('list_max', 3)) / 2)
            total_segments += int(avg_items) * dt['records']
        else:
            total_segments += dt['records']
print(f'{total_records} {total_segments}')
" 2>/dev/null || echo "0 0")

    local num_records num_segments
    num_records=$(echo "$records" | awk '{print $1}')
    num_segments=$(echo "$records" | awk '{print $2}')

    # Estimate: ~60-90 sec per segment on 70B (use 75 as average)
    local est_seconds=$(( num_segments * 75 ))
    local est_hours=$(( est_seconds / 3600 ))
    local est_days=$(echo "scale=1; $est_seconds / 86400" | bc 2>/dev/null || echo "?")

    echo -e "${BLUE}Estimate for ${num_records} documents, ${num_segments} total LLM calls:${NC}"
    if [ "$est_hours" -lt 24 ]; then
        echo -e "  ${YELLOW}~${est_hours} hours${NC}"
    else
        echo -e "  ${YELLOW}~${est_days} days${NC}"
    fi
    echo ""
}

run_generation() {
    local config_name="$1"
    shift
    local extra_args=("$@")

    local config_file="$CONFIGS_DIR/${config_name}.yaml"
    if [ ! -f "$config_file" ]; then
        echo -e "${RED}Config not found: $config_file${NC}"
        echo "Available configs:"
        ls -1 "$CONFIGS_DIR"/*.yaml 2>/dev/null | xargs -I{} basename {} .yaml | sed 's/^/  /'
        exit 1
    fi

    mkdir -p "$LOGS_DIR" "$PID_DIR" "$OUTPUT_DIR"

    echo -e "${BLUE}Config:${NC} $config_file"
    estimate_time "$config_file"

    # Check for existing run
    local pid_file="$PID_DIR/${config_name}.pid"
    if [ -f "$pid_file" ]; then
        local old_pid
        old_pid=$(cat "$pid_file")
        if kill -0 "$old_pid" 2>/dev/null; then
            echo -e "${YELLOW}⚠ A generation is already running for $config_name (PID: $old_pid)${NC}"
            echo "  Use: ./run.sh --status"
            echo "  Or:  kill $old_pid"
            exit 1
        else
            rm -f "$pid_file"
        fi
    fi

    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local log_file="$LOGS_DIR/${timestamp}_${config_name}.log"

    echo -e "${GREEN}Starting generation...${NC}"
    echo -e "  Log: ${CYAN}$log_file${NC}"
    echo ""

    # Run in background with nohup
    nohup python3 run.py "$config_file" "${extra_args[@]}" \
        > >(tee -a "$log_file") \
        2> >(tee -a "$log_file" >&2) &

    local pid=$!
    echo "$pid" > "$pid_file"

    echo -e "${GREEN}Running in background (PID: $pid)${NC}"
    echo ""
    echo -e "Monitor progress:"
    echo -e "  ${CYAN}tail -f $log_file${NC}"
    echo -e "  ${CYAN}./run.sh --status${NC}"
    echo -e "  ${CYAN}./run.sh --monitor $config_name${NC}"
    echo ""
    echo -e "To stop:"
    echo -e "  ${CYAN}kill $pid${NC}"
    echo -e "  Then resume later with: ${CYAN}./run.sh $config_name --resume${NC}"
}

run_foreground() {
    local config_name="$1"
    shift
    local extra_args=("$@")

    local config_file="$CONFIGS_DIR/${config_name}.yaml"
    if [ ! -f "$config_file" ]; then
        echo -e "${RED}Config not found: $config_file${NC}"
        exit 1
    fi

    echo -e "${BLUE}Config:${NC} $config_file"
    estimate_time "$config_file"
    echo -e "${GREEN}Starting generation (foreground)...${NC}"
    echo ""

    python3 run.py "$config_file" "${extra_args[@]}"
}

show_status() {
    echo -e "${BLUE}Running jobs:${NC}"
    local found=0
    if [ -d "$PID_DIR" ]; then
        for pid_file in "$PID_DIR"/*.pid; do
            [ -f "$pid_file" ] || continue
            local name
            name=$(basename "$pid_file" .pid)
            local pid
            pid=$(cat "$pid_file")

            if kill -0 "$pid" 2>/dev/null; then
                found=1
                # Check for progress files
                local progress_file="$OUTPUT_DIR/$name/.progress"
                local progress_info=""
                if [ -d "$progress_file" ]; then
                    local lines
                    lines=$(wc -l "$progress_file"/*.jsonl 2>/dev/null | tail -1 | awk '{print $1}')
                    progress_info=" (${lines:-0} docs completed)"
                fi

                # Get elapsed time
                local elapsed=""
                if command -v ps &>/dev/null; then
                    elapsed=$(ps -o etime= -p "$pid" 2>/dev/null | tr -d ' ')
                fi

                echo -e "  ${GREEN}●${NC} $name  PID=$pid  elapsed=${elapsed:-?}$progress_info"
            else
                echo -e "  ${RED}●${NC} $name  PID=$pid  (stopped)"
                rm -f "$pid_file"
            fi
        done
    fi

    if [ "$found" -eq 0 ]; then
        echo -e "  ${YELLOW}No running jobs${NC}"
    fi

    # Show recent outputs
    echo ""
    echo -e "${BLUE}Recent outputs:${NC}"
    if [ -d "$OUTPUT_DIR" ]; then
        ls -dt "$OUTPUT_DIR"/*/ 2>/dev/null | head -5 | while read -r dir; do
            local name
            name=$(basename "$dir")
            local size
            size=$(du -sh "$dir" 2>/dev/null | awk '{print $1}')
            echo -e "  $name  (${size:-?})"
        done
    else
        echo -e "  ${YELLOW}No outputs yet${NC}"
    fi
}

monitor_job() {
    local config_name="$1"

    # Find the latest log for this config
    local latest_log
    latest_log=$(ls -t "$LOGS_DIR"/*"${config_name}"*.log 2>/dev/null | head -1)

    if [ -z "$latest_log" ]; then
        echo -e "${RED}No log found for: $config_name${NC}"
        exit 1
    fi

    echo -e "${BLUE}Monitoring: $latest_log${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop monitoring (generation continues in background)${NC}"
    echo ""

    # Show progress summary, then tail
    echo -e "${CYAN}── Recent Progress ──${NC}"
    grep -E "(Document DOC-|progress:|PIPELINE COMPLETE)" "$latest_log" | tail -10
    echo -e "${CYAN}── Live Log ──${NC}"
    tail -f "$latest_log"
}

run_dry_run() {
    local config_name="$1"
    local config_file="$CONFIGS_DIR/${config_name}.yaml"

    if [ ! -f "$config_file" ]; then
        echo -e "${RED}Config not found: $config_file${NC}"
        exit 1
    fi

    echo -e "${YELLOW}DRY RUN: Generating 5 documents to test pipeline${NC}"

    # Create a temp config with records=5
    local tmp_config="/tmp/dryrun_${config_name}.yaml"
    python3 -c "
import yaml
with open('$config_file') as f:
    cfg = yaml.safe_load(f)
for dt in cfg.get('document_tables', []):
    dt['records'] = 5
cfg['metadata']['name'] = cfg['metadata']['name'] + '-dryrun'
cfg['packaging']['create_zip'] = False
with open('$tmp_config', 'w') as f:
    yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False)
print('Dry-run config created: $tmp_config')
"

    echo ""
    estimate_time "$tmp_config"
    echo -e "${GREEN}Running...${NC}"
    echo ""

    python3 run.py "$tmp_config"

    echo ""
    echo -e "${GREEN}Dry run complete!${NC}"
    echo -e "Check output in: ${CYAN}$OUTPUT_DIR/${NC}"
    rm -f "$tmp_config"
}

# ─── Main ──────────────────────────────────────────────────────────

print_banner

case "${1:-}" in
    --help|-h|"")
        echo "Usage:"
        echo "  ./run.sh <config-name>              Run generation in background"
        echo "  ./run.sh <config-name> --foreground  Run in foreground (see all output)"
        echo "  ./run.sh <config-name> --resume      Resume interrupted run"
        echo "  ./run.sh --dry-run <config-name>     Test with 5 documents"
        echo "  ./run.sh --health                    Check Ollama + dependencies"
        echo "  ./run.sh --status                    Show running jobs & outputs"
        echo "  ./run.sh --monitor <config-name>     Live tail of generation log"
        echo "  ./run.sh --list                      List available configs"
        echo ""
        echo "Available configs:"
        ls -1 "$CONFIGS_DIR"/*.yaml 2>/dev/null | xargs -I{} basename {} .yaml | sed 's/^/  /' || echo "  (none found)"
        ;;

    --health)
        echo -e "${BLUE}Checking dependencies...${NC}"
        echo ""
        check_dependencies
        ;;

    --status)
        show_status
        ;;

    --list)
        echo -e "${BLUE}Available configs:${NC}"
        for f in "$CONFIGS_DIR"/*.yaml; do
            [ -f "$f" ] || continue
            name=$(basename "$f" .yaml)
            desc=$(python3 -c "
import yaml
with open('$f') as fh:
    cfg = yaml.safe_load(fh)
print(cfg.get('metadata', {}).get('description', '(no description)')[:80])
" 2>/dev/null || echo "(could not read)")
            echo -e "  ${GREEN}$name${NC}"
            echo "    $desc"
            echo ""
        done
        ;;

    --dry-run)
        if [ -z "${2:-}" ]; then
            echo -e "${RED}Usage: ./run.sh --dry-run <config-name>${NC}"
            exit 1
        fi
        run_dry_run "$2"
        ;;

    --monitor)
        if [ -z "${2:-}" ]; then
            echo -e "${RED}Usage: ./run.sh --monitor <config-name>${NC}"
            exit 1
        fi
        monitor_job "$2"
        ;;

    *)
        config_name="$1"
        shift

        # Check for special flags
        foreground=0
        extra_args=()
        for arg in "$@"; do
            if [ "$arg" = "--foreground" ] || [ "$arg" = "-f" ]; then
                foreground=1
            else
                extra_args+=("$arg")
            fi
        done

        if [ "$foreground" -eq 1 ]; then
            run_foreground "$config_name" "${extra_args[@]}"
        else
            run_generation "$config_name" "${extra_args[@]}"
        fi
        ;;
esac
