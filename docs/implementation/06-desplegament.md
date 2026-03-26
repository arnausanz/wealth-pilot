# Desplegament — Docker Local i Oracle Cloud

> Última actualització: Març 2026

---

## Local (Docker Compose)

### Requisits
- Docker Desktop (Mac) o Docker Engine (Linux)
- `make` (preinstal·lat a macOS)

### Comandes del dia a dia

```bash
make dev          # Arranca tot el stack (DB + backend + frontend) amb hot reload
make dev-bg       # Idem però en background
make down         # Para els contenidors
make logs         # Segueix els logs en temps real

make migrate      # Aplica migracions pendents (alembic upgrade head)
make migration name="descripcio"   # Genera nova migració per autogenerate
make seed         # Executa el seed script (idempotent)
make test         # Executa tots els tests

make db-shell     # Entra a psql directament
make clean        # Elimina contenidors + volums (esborra la BD local!)
make clean-all    # Idem + elimina imatges locals
```

### Stack de serveis

| Servei | Port extern | Descripció |
|--------|------------|-----------|
| `db` | 5432 | PostgreSQL 15 Alpine amb healthcheck |
| `backend` | 8000 | FastAPI + uvicorn --reload (hot reload) |
| `frontend` | 8080 | Nginx servint estàtics + proxy `/api/` → backend |

La URL principal de treball és **`http://localhost:8080`** (sempre via Nginx, no directament al backend).

### Volums
- `postgres_data`: persistent entre `down`/`up`. Només `make clean` l'esborra.
- `./backend:/app`: mount del codi per a hot reload del backend.

---

## Producció (Oracle Cloud — Systemd)

### Prerequisits a la VM
La VM ja té tot el necessari:
- PostgreSQL (TimescaleDB) corrent
- Python 3.12 instal·lat
- Nginx configurat
- Systemd

### Setup inicial (una sola vegada)

```bash
# 1. Crear BD i usuari
sudo -u postgres psql
CREATE DATABASE wealthpilot;
CREATE USER wealthpilot_user WITH PASSWORD 'password-segura';
GRANT ALL PRIVILEGES ON DATABASE wealthpilot TO wealthpilot_user;
\q

# 2. Clonar i configurar
git clone <repo> /opt/wealthpilot/app
python3.12 -m venv /opt/wealthpilot/venv
/opt/wealthpilot/venv/bin/pip install -r /opt/wealthpilot/app/backend/requirements.txt

# 3. Crear .env.prod
cp /opt/wealthpilot/app/.env.prod.example /opt/wealthpilot/.env.prod
nano /opt/wealthpilot/.env.prod
# Canviar: DATABASE_URL (usa @localhost, no @db), ENV=production, LOG_LEVEL=info

# 4. Migrar i fer seed
cd /opt/wealthpilot/app/backend
/opt/wealthpilot/venv/bin/alembic upgrade head
/opt/wealthpilot/venv/bin/python scripts/seed.py

# 5. Systemd service
sudo cp /opt/wealthpilot/app/deployment/wealthpilot.service /etc/systemd/system/
sudo systemctl enable wealthpilot
sudo systemctl start wealthpilot

# 6. Nginx virtual host
sudo cp /opt/wealthpilot/app/deployment/nginx.conf /etc/nginx/sites-available/wealthpilot
sudo ln -s /etc/nginx/sites-available/wealthpilot /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### Deploy continu (cada vegada que hi ha canvis)

```bash
/opt/wealthpilot/app/deployment/deploy.sh
```

Script complet (`deployment/deploy.sh`):
```bash
git pull
pip install -r backend/requirements.txt
alembic upgrade head
systemctl restart wealthpilot
```

### Diferència crítica Local vs Producció

| | Local (Docker) | Producció (Oracle) |
|--|----------------|-------------------|
| `DATABASE_URL` host | `@db:5432` | `@localhost:5432` |
| `ENV` | `development` | `production` |
| `LOG_LEVEL` | `debug` | `info` |
| Servidor WSGI | uvicorn --reload | gunicorn -w 2 |
| BD | PostgreSQL 15 (Docker) | TimescaleDB (systemd) |

---

## Fitxers de Configuració de Producció

### `deployment/wealthpilot.service`
Systemd service que arranca Gunicorn amb 2 workers UvicornWorker:
```ini
[Service]
User=wealthpilot
WorkingDirectory=/opt/wealthpilot/app/backend
EnvironmentFile=/opt/wealthpilot/.env.prod
ExecStart=/opt/wealthpilot/venv/bin/gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
Restart=always
```

### `deployment/nginx.conf`
- Serveix `/` → fitxers estàtics del frontend
- Proxy `/api/` → `http://127.0.0.1:8000` (FastAPI)
- SPA fallback: `try_files $uri /index.html` (necessari per a la hash navigation)
- Bloc HTTPS comentat (activar quan hi hagi domini + Let's Encrypt)

### `.env.prod.example`
Trackat per git (sense secrets reals). Documenta totes les variables que cal definir a la VM.

---

## Ports a Oracle Cloud (OCI)

Si la app no és accessible des de l'exterior:
1. OCI Console → Networking → VCN → Security Lists → Add Ingress Rule (port 80 i 443)
2. A la VM: `sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT`

---

## HTTPS (quan hi hagi domini)

```bash
sudo certbot --nginx -d domini.exemple.com
# Auto-renovació ja configurada via cron a la VM (cada 90 dies)
```
