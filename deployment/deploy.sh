#!/usr/bin/env bash
# WealthPilot — Deploy script
# Executa des de la VM: cd /opt/wealthpilot/app && bash deployment/deploy.sh
#
# Fa: git pull → pip install → frontend build → alembic migrate → restart service

set -euo pipefail

APP_DIR="/opt/wealthpilot/app"
VENV="/opt/wealthpilot/venv"
DIST="/opt/wealthpilot/dist"
SERVICE="wealthpilot"

echo "────────────────────────────────────────────"
echo "  WealthPilot Deploy — $(date '+%Y-%m-%d %H:%M')"
echo "────────────────────────────────────────────"

# 1. Pull codi
echo "→ [1/5] Git pull..."
cd "$APP_DIR"
git pull origin main

# 2. Backend dependencies
echo "→ [2/5] Backend dependencies..."
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -r backend/requirements.txt

# 3. Frontend build
echo "→ [3/5] Frontend build (npm)..."
cd "$APP_DIR/frontend"
npm ci --silent
npm run build --silent
# Copia el dist a /opt/wealthpilot/dist (nginx el serveix des d'aquí)
rm -rf "$DIST"
cp -r dist "$DIST"
echo "   ✓ Build copiat a $DIST"

# 4. Migracions BD
echo "→ [4/5] Migracions..."
cd "$APP_DIR/backend"
set -a && source /opt/wealthpilot/.env.prod && set +a
"$VENV/bin/alembic" upgrade head

# 5. Restart backend
echo "→ [5/5] Reiniciant servei..."
sudo systemctl restart "$SERVICE"
sleep 2
sudo systemctl is-active --quiet "$SERVICE" && echo "   ✓ Servei actiu" || {
    echo "   ✗ El servei no ha arrencat. Logs:"
    sudo journalctl -u "$SERVICE" --no-pager -n 20
    exit 1
}

echo "────────────────────────────────────────────"
echo "  Deploy completat correctament"
echo "────────────────────────────────────────────"
