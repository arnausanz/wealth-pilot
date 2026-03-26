#!/usr/bin/env bash
# run_tests.sh — Executa tots els testos del projecte contra el stack Docker.
# Ús: ./tests/run_tests.sh  o bé: make test
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " WealthPilot — Test Suite"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Verify the stack is running
if ! docker compose ps backend --status running --quiet 2>/dev/null | grep -q .; then
    echo "[!] El stack no està corrent. Executant 'docker compose up -d'..."
    docker compose up -d
    echo "[~] Esperant que els serveis estiguin llestos..."
    sleep 5
fi

echo ""
echo "▶ Backend tests (pytest)"
echo "─────────────────────────────────────────────────────"
docker compose exec backend python -m pytest tests/ -v --tb=short --no-header 2>&1
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Tots els testos completats."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
