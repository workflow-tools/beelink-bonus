#!/usr/bin/env bash
# ============================================================================
# Court Case Scraper — Launch Script
# ============================================================================
#
# Scrapes Japanese and German court databases for real estate / housing
# dispute decisions, extracting document references and flaw patterns.
#
# Usage:
#   ./scrape.sh japan --bulk              # All Japanese real estate queries
#   ./scrape.sh germany --bulk            # All German Mietrecht queries
#   ./scrape.sh both --bulk               # Both countries
#   ./scrape.sh japan --search "敷金返還"  # Single Japanese query
#   ./scrape.sh germany --search "Nebenkostenabrechnung fehlerhaft"
#   ./scrape.sh taxonomy                  # Generate flaw taxonomies from scraped data
#
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════╗"
echo "║  Court Case Scraper                          ║"
echo "║  Real Estate & Housing Dispute Mining         ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# Check dependencies
check_deps() {
    local missing=0
    for pkg in httpx bs4; do
        if ! python3 -c "import $pkg" 2>/dev/null; then
            echo -e "${RED}✗ Missing: $pkg${NC}"
            missing=1
        fi
    done
    if [ "$missing" -eq 1 ]; then
        echo -e "${YELLOW}Installing dependencies...${NC}"
        pip install -r requirements.txt --break-system-packages 2>/dev/null || \
        pip install -r requirements.txt
    fi
    echo -e "${GREEN}✓ Dependencies OK${NC}"
}

check_deps

case "${1:-help}" in
    japan|jp)
        shift
        echo -e "${GREEN}Running Japan court scraper...${NC}"
        python3 scrapers/japan_courts.py "$@"
        ;;
    germany|de)
        shift
        echo -e "${GREEN}Running Germany court scraper...${NC}"
        python3 scrapers/germany_courts.py "$@"
        ;;
    both)
        shift
        echo -e "${GREEN}Running both scrapers...${NC}"
        echo -e "${CYAN}── Japan ──${NC}"
        python3 scrapers/japan_courts.py "$@"
        echo ""
        echo -e "${CYAN}── Germany ──${NC}"
        python3 scrapers/germany_courts.py "$@"
        ;;
    taxonomy)
        echo -e "${GREEN}Generating flaw taxonomies from scraped data...${NC}"
        python3 scrapers/japan_courts.py --taxonomy
        python3 scrapers/germany_courts.py --taxonomy
        echo ""
        echo -e "${CYAN}Taxonomy files:${NC}"
        echo "  output/japan/flaw_taxonomy.json"
        echo "  output/germany/flaw_taxonomy.json"
        ;;
    help|--help|-h|*)
        echo "Usage:"
        echo "  ./scrape.sh japan --bulk              Scrape all Japanese RE queries"
        echo "  ./scrape.sh germany --bulk            Scrape all German Mietrecht queries"
        echo "  ./scrape.sh both --bulk               Both countries"
        echo "  ./scrape.sh japan --search \"敷金返還\"  Single search"
        echo "  ./scrape.sh germany --search \"Nebenkostenabrechnung\""
        echo "  ./scrape.sh taxonomy                  Generate flaw reports"
        echo ""
        echo "Options:"
        echo "  --max N       Max results per query (default: 50)"
        echo "  --resume      Skip already-scraped cases"
        echo ""
        echo "Output:"
        echo "  output/japan/   — Japanese case data (JSONL)"
        echo "  output/germany/ — German case data (JSONL)"
        echo "  */flaw_taxonomy.json — Extracted flaw patterns"
        ;;
esac
