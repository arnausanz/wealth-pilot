# WealthPilot — Oracle Cloud VM Cheatsheet

> **Valors que necessites tenir a mà:**
> - **IP PÚBLICA:** `79.76.110.205`
> - **DOMINI:** `79-76-110-205.sslip.io`
> - **USUARI SSH:** `ubuntu`
> - **CLAU SSH:** `~/.ssh/id_ed25519`
> - **BD:** `wealthpilot` | Usuari BD: `wealthpilot_db`
> - **Contrasenya BD:** `WealthPilot2026x`
> - **Port BD:** `5433` (⚠️ no és el 5432 estàndard!)
> - **SECRET_KEY app:** `316981b84ae15a43f69dad1bc0798a5aeabe3f7c8f4c4de88f4afc782c408136`
> - **URL app:** `https://79-76-110-205.sslip.io`
> - **Fitxer .env.prod a la VM:** `/opt/wealthpilot/.env.prod`
> - **Basic Auth usuari:** `arnau`
> - **Basic Auth contrasenya:** `qosteH-2caccy-poxkot`
> - **Fitxer htpasswd:** `/etc/nginx/.htpasswd`

> ⚠️ Cada secció indica on s'executa: **[MAC]** o **[VM]**

---

## 1. Connectar-se a la VM

**[MAC]**
```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@79.76.110.205
```

Per sortir:
```bash
exit
```

---

## 2. Gestió del servei WealthPilot (backend)

**[VM]**

```bash
# Estat del servei
sudo systemctl status wealthpilot

# Veure logs en temps real
journalctl -fu wealthpilot

# Veure últims 50 logs
journalctl -u wealthpilot -n 50

# Reiniciar (després d'un deploy)
sudo systemctl restart wealthpilot

# Aturar / Arrencar
sudo systemctl stop wealthpilot
sudo systemctl start wealthpilot
```

> El backend escolta a `127.0.0.1:8000`. Nginx fa el proxy cap a ell.

---

## 3. Deploy d'una nova versió

**[MAC]** — primer puja els canvis:
```bash
cd /Users/arnau/Documents/Projectes/wealth-pilot
git push origin main
```

**[VM]** — executa el script de deploy:
```bash
cd /opt/wealthpilot/app
bash deployment/deploy.sh
```

El script fa automàticament:
1. `git pull`
2. `pip install` dependències noves
3. Build frontend (`npm run build`)
4. `alembic upgrade head` (migracions BD)
5. `systemctl restart wealthpilot`

---

## 4. Connexió a la base de dades

### Opció A — Directament a la VM **[VM]**
```bash
psql -h localhost -p 5433 -U wealthpilot_db -d wealthpilot
# Contrasenya: WealthPilot2026x
```

### Opció B — Túnel SSH des del Mac (per usar TablePlus, DBeaver, etc.)

**[MAC] Terminal 1** — obre el túnel (deixa-la oberta):
```bash
ssh -i ~/.ssh/id_ed25519 -L 5434:localhost:5433 ubuntu@79.76.110.205 -N
```

**[MAC] Terminal 2** — connecta't:
```bash
psql -h localhost -p 5434 -U wealthpilot_db -d wealthpilot
# Contrasenya: WealthPilot2026x
```

O configura TablePlus/DBeaver amb:
- Host: `localhost` | Port: `5434`
- User: `wealthpilot_db` | DB: `wealthpilot` | Password: `WealthPilot2026x`

> ⚠️ Tanca el túnel amb `Ctrl+C` quan acabis.

### Comandes útils dins de psql
```sql
-- Llistar taules
\dt

-- Comptar snapshots
SELECT COUNT(*) FROM net_worth_snapshots;

-- Últim net worth
SELECT snapshot_date, total_net_worth FROM net_worth_snapshots ORDER BY snapshot_date DESC LIMIT 1;

-- Comptar transaccions
SELECT COUNT(*) FROM mw_transactions;

-- Sortir
\q
```

---

## 5. Nginx

**[VM]**
```bash
# Estat
sudo systemctl status nginx

# Testar config (abans de recarregar)
sudo nginx -t

# Recarregar config (sense tallar connexions)
sudo systemctl reload nginx

# Veure logs d'accés
sudo tail -f /var/log/nginx/access.log

# Veure logs d'errors
sudo tail -f /var/log/nginx/error.log
```

Config a: `/etc/nginx/sites-available/wealthpilot`

---

## 6. Certificat SSL (Let's Encrypt)

**[VM]**
```bash
# Veure quan expira el certificat
sudo certbot certificates

# Renovar manualment (normalment es fa sol via cron)
sudo certbot renew

# Forçar renovació (si falta poc per expirar)
sudo certbot renew --force-renewal
```

> La renovació automàtica s'executa dos cops al dia via systemd timer. Caduca cada 90 dies.

---

## 7. Importar backup MoneyWiz

**Pas 1 — Exportar backup des de MoneyWiz [MAC]:**
1. Obre MoneyWiz
2. Menú → **File → Backup → Create Backup**
3. Guarda el `.moneywiz` (o comprimit `.zip`) a qualsevol lloc del Mac

**Pas 2 — Pujar a la VM [MAC]:**
```bash
# Substitueix /path/al/backup pel path real del fitxer
curl -X POST https://79-76-110-205.sslip.io/api/v1/sync/upload \
  -F "file=@/path/al/backup.moneywiz"
```

> Si el fitxer és `.zip`: canvia `.moneywiz` per `.zip` a la comanda.

**Pas 3 — Verifica que s'han importat les dades [VM]:**
```bash
PGPASSWORD='WealthPilot2026x' psql -h localhost -p 5433 -U wealthpilot_db -d wealthpilot \
  -c "SELECT COUNT(*) FROM mw_transactions; SELECT COUNT(*) FROM mw_accounts;"
```

---

## 8. Backup de la base de dades

**[VM]** — backup manual:
```bash
PGPASSWORD='WealthPilot2026x' pg_dump -h localhost -p 5433 -U wealthpilot_db -d wealthpilot \
  | gzip > ~/backup_wealthpilot_$(date +%Y%m%d_%H%M).sql.gz
```

**[MAC]** — descarregar backup:
```bash
scp -i ~/.ssh/id_ed25519 ubuntu@79.76.110.205:~/backup_wealthpilot_*.sql.gz ~/Downloads/
```

**[VM]** — restaurar des de backup:
```bash
gunzip -c ~/backup_wealthpilot_20260328_1200.sql.gz \
  | PGPASSWORD='WealthPilot2026x' psql -h localhost -p 5433 -U wealthpilot_db -d wealthpilot
```

---

## 9. Comprovar estat general de la VM

**[VM]**
```bash
# RAM
free -h

# Disc
df -h /

# Serveis actius (bot + wealthpilot)
sudo systemctl status trading-demo wealthpilot

# Ports en ús (80=nginx, 443=https, 8000=backend, 5433=postgresql)
ss -tlnp | grep -E ':(80|443|8000|5433)'
```

---

## 10. Instal·lar com a PWA a l'iPhone

1. Obre **Safari** a l'iPhone (⚠️ ha de ser Safari, no Chrome)
2. Navega a: `https://79-76-110-205.sslip.io`
3. Prem la icona de **Compartir** (quadrat amb fletxa cap amunt)
4. Desplaça't i prem **"Afegir a la pantalla d'inici"**
5. Posa-li el nom que vulguis → **Afegir**

> L'app s'obre sense barra d'adreça, com una app nativa.
> Per desinstal·lar: mantén premuda la icona → Eliminar app.

---

## 11. Resolució de problemes habituals

### El backend no arrenca
```bash
journalctl -u wealthpilot -n 50
# Busca "Error" o "Exception" als logs
```

### Nginx retorna 502 Bad Gateway
```bash
# El backend ha caigut — reinicia'l
sudo systemctl restart wealthpilot
sudo systemctl status wealthpilot
```

### El certificat SSL ha expirat
```bash
sudo certbot renew --force-renewal
sudo systemctl reload nginx
```

### Veure totes les variables d'entorn del servei
```bash
sudo cat /opt/wealthpilot/.env.prod
```

### Tornar a fer el seed de la BD (si cal)
```bash
cd /opt/wealthpilot/app/backend
/opt/wealthpilot/venv/bin/python scripts/seed.py
```
