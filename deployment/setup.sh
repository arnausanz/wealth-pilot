#!/usr/bin/env bash
# WealthPilot — First-time setup script per a Oracle Cloud VM (Ubuntu/Debian)
#
# PREREQUISITS: VM Ubuntu 22.04+, SSH com a usuari amb sudo
# EXECUCIÓ: bash deployment/setup.sh
#
# Fa:
#   1. Instal·la nginx, certbot, nodejs, python3-venv
#   2. Crea usuari wealthpilot + estructura de directoris
#   3. Clona el repo a /opt/wealthpilot/app
#   4. Crea entorn virtual Python + instal·la dependències
#   5. Configura nginx amb sslip.io + Let's Encrypt
#   6. Instal·la servei systemd
#   7. Seed de la BD

set -euo pipefail

# ─── CONFIGURACIÓ — EDITA AQUÍ ABANS D'EXECUTAR ───────────────────────────────
REPO_URL="https://github.com/USUARI/wealth-pilot.git"  # ← canvia per la teva URL
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="wealthpilot"
DB_USER="wealthpilot_db"
DB_PASS="CANVIA_AQUESTA_CONTRASENYA"   # ← canvia per una contrasenya segura
SECRET_KEY="CANVIA_AQUESTA_SECRET_KEY" # ← genera amb: openssl rand -hex 32
# ──────────────────────────────────────────────────────────────────────────────

BASE_DIR="/opt/wealthpilot"
APP_DIR="$BASE_DIR/app"
VENV_DIR="$BASE_DIR/venv"
DIST_DIR="$BASE_DIR/dist"
LOG_DIR="$BASE_DIR/logs"
SERVICE_USER="wealthpilot"

# Detecta IP pública i construeix el domini sslip.io
PUBLIC_IP=$(curl -s --max-time 5 ifconfig.me || curl -s --max-time 5 icanhazip.com)
if [[ -z "$PUBLIC_IP" ]]; then
    echo "ERROR: No s'ha pogut detectar la IP pública."
    exit 1
fi
SSLIP_DOMAIN="${PUBLIC_IP//./-}.sslip.io"
echo ""
echo "════════════════════════════════════════════"
echo "  WealthPilot Setup — Oracle Cloud VM"
echo "  IP pública: $PUBLIC_IP"
echo "  Domini: https://$SSLIP_DOMAIN"
echo "════════════════════════════════════════════"
echo ""

# ─── 1. Sistema ───────────────────────────────────────────────────────────────
echo "[1/8] Instal·lant paquets del sistema..."
sudo apt-get update -q
sudo apt-get install -y -q \
    nginx certbot python3-certbot-nginx \
    python3.12 python3.12-venv python3-pip \
    nodejs npm git curl \
    postgresql-client  # només client, la BD ja és existent

# ─── 2. Usuari i directoris ───────────────────────────────────────────────────
echo "[2/8] Creant usuari i directoris..."
sudo useradd --system --no-create-home --shell /bin/false "$SERVICE_USER" 2>/dev/null || true
sudo mkdir -p "$APP_DIR" "$VENV_DIR" "$DIST_DIR" "$LOG_DIR"

# ─── 3. Clonar repo ──────────────────────────────────────────────────────────
echo "[3/8] Clonant repositori..."
if [[ -d "$APP_DIR/.git" ]]; then
    echo "   Repo ja existeix, fent pull..."
    cd "$APP_DIR" && sudo git pull origin main
else
    sudo git clone "$REPO_URL" "$APP_DIR"
fi

# ─── 4. Python venv + deps ───────────────────────────────────────────────────
echo "[4/8] Creant entorn virtual Python..."
sudo python3.12 -m venv "$VENV_DIR"
sudo "$VENV_DIR/bin/pip" install --quiet --upgrade pip
sudo "$VENV_DIR/bin/pip" install --quiet -r "$APP_DIR/backend/requirements.txt"

# ─── 5. Frontend build ───────────────────────────────────────────────────────
echo "[5/8] Build del frontend..."
cd "$APP_DIR/frontend"
sudo npm ci --silent
sudo npm run build --silent
sudo cp -r dist "$DIST_DIR"
echo "   ✓ Frontend build a $DIST_DIR"

# ─── 6. Fitxers de configuració ──────────────────────────────────────────────
echo "[6/8] Configurant fitxers..."

# .env.prod
sudo tee "$BASE_DIR/.env.prod" > /dev/null << EOF
# WealthPilot — Producció
ENV=production
APP_VERSION=2.0.0

DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}
SECRET_KEY=${SECRET_KEY}

CORS_ORIGINS=https://${SSLIP_DOMAIN}
LOG_LEVEL=INFO
EOF
sudo chmod 600 "$BASE_DIR/.env.prod"
echo "   ✓ .env.prod creat"

# Nginx config (substitueix DOMAIN_PLACEHOLDER)
sudo cp "$APP_DIR/deployment/nginx.conf" /etc/nginx/sites-available/wealthpilot
sudo sed -i "s/DOMAIN_PLACEHOLDER/$SSLIP_DOMAIN/g" /etc/nginx/sites-available/wealthpilot

# Activa el site
sudo ln -sf /etc/nginx/sites-available/wealthpilot /etc/nginx/sites-enabled/wealthpilot
# Desactiva default si existeix
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx
sudo nginx -t
echo "   ✓ Nginx configurat"

# Systemd service
sudo cp "$APP_DIR/deployment/wealthpilot.service" /etc/systemd/system/wealthpilot.service
sudo systemctl daemon-reload
sudo systemctl enable wealthpilot
echo "   ✓ Systemd service instal·lat"

# ─── 7. BD + Seed ────────────────────────────────────────────────────────────
echo "[7/8] Configurant base de dades..."
# Crea BD i usuari si no existeixen
sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};" 2>/dev/null || true

# Migracions
cd "$APP_DIR/backend"
sudo "$VENV_DIR/bin/alembic" upgrade head

# Seed (si la taula assets és buida)
ASSET_COUNT=$(sudo -u postgres psql -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM assets;" 2>/dev/null | tr -d ' ' || echo "0")
if [[ "$ASSET_COUNT" == "0" ]]; then
    echo "   BD buida, executant seed..."
    sudo "$VENV_DIR/bin/python" scripts/seed.py
fi

# ─── 8. SSL + Arrencada ──────────────────────────────────────────────────────
echo "[8/8] Obtenint certificat SSL (Let's Encrypt)..."
sudo mkdir -p /var/www/certbot
# Arrenca nginx primer en HTTP per al challenge
sudo systemctl start nginx
sudo certbot --nginx -d "$SSLIP_DOMAIN" \
    --non-interactive --agree-tos \
    --email "admin@${SSLIP_DOMAIN}" \
    --redirect

# Arrenca el backend
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$BASE_DIR"
sudo systemctl start wealthpilot
sleep 3
sudo systemctl is-active --quiet wealthpilot && echo "   ✓ Backend actiu" || {
    echo "   ✗ Backend no arranca. Logs:"
    sudo journalctl -u wealthpilot --no-pager -n 30
    exit 1
}

# Renova SSL automàticament (cron)
(sudo crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet && systemctl reload nginx") | sudo crontab -

echo ""
echo "════════════════════════════════════════════"
echo "  Setup completat!"
echo "  URL: https://$SSLIP_DOMAIN"
echo "  Instal·la PWA: obre la URL al Safari iOS"
echo "         → Compartir → Afegir a pantalla d'inici"
echo "════════════════════════════════════════════"
