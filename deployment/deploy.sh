#!/usr/bin/env bash
# Deploy script — Oracle Cloud VM
# Executa des de la VM: bash deployment/deploy.sh

set -euo pipefail

APP_DIR="/opt/wealthpilot/app"
VENV="$APP_DIR/../venv"
SERVICE="wealthpilot"

echo "── WealthPilot Deploy ──────────────────────"

echo "→ Pull del codi..."
cd "$APP_DIR"
git pull origin main

echo "→ Instal·lant dependències..."
"$VENV/bin/pip" install --quiet -r backend/requirements.txt

echo "→ Executant migracions..."
cd "$APP_DIR/backend"
"$VENV/bin/alembic" upgrade head

echo "→ Reiniciant servei..."
sudo systemctl restart "$SERVICE"
sudo systemctl is-active --quiet "$SERVICE" && echo "✓ Servei actiu" || (echo "✗ Error: servei no arranca" && exit 1)

echo "── Deploy completat ────────────────────────"
