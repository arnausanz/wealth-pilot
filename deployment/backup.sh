#!/usr/bin/env bash
# Backup diari de PostgreSQL — afegir al cron:
# 0 3 * * * /opt/wealthpilot/app/deployment/backup.sh

set -euo pipefail

source /opt/wealthpilot/.env.prod

BACKUP_DIR="/opt/wealthpilot/backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILE="$BACKUP_DIR/wealthpilot_$DATE.sql.gz"
KEEP_DAYS=7

mkdir -p "$BACKUP_DIR"

pg_dump "$POSTGRES_DB" | gzip > "$FILE"
echo "Backup creat: $FILE"

# Eliminar backups antics
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$KEEP_DAYS -delete
echo "Backups antics eliminats (> ${KEEP_DAYS} dies)"
