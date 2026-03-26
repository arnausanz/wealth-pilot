# Stack i Arquitectura

> Última actualització: Març 2026

---

## Stack Tecnològic

| Capa | Tecnologia | Versió | Motiu |
|------|-----------|--------|-------|
| **Backend API** | FastAPI | 0.115 | Async natiu, tipat fort, OpenAPI auto-generat |
| **ORM / BD** | SQLAlchemy async + asyncpg | 2.0 / 0.29 | Millor ORM de Python, suport async modern |
| **Migracions** | Alembic | 1.13 | Autogenera migracions des dels models |
| **Validació settings** | pydantic-settings | 2.5 | Type-safe config llegint .env |
| **Base de dades** | PostgreSQL 15 | 15-alpine | Robustesa, JSONB, índexs parcials |
| **Servidor prod** | Gunicorn + UvicornWorker | 22.0 | Multi-worker per producció |
| **Frontend** | Vanilla JS SPA | — | Zero dependencies, zero build step |
| **Gràfics** | Chart.js | CDN | Lleugera, mòbil-friendly |
| **Reverse proxy** | Nginx | alpine | Serveix estàtics + proxy `/api/` |
| **Dev stack** | Docker Compose | — | Aïllament total, un sol `docker compose up` |
| **Prod deploy** | Systemd + Nginx existent | — | VM Oracle Cloud ja té infraestructura |
| **Tests** | pytest + asyncpg | 8.3 | Tests d'integració contra BD real |

---

## Principi Fonamental: Core Immutable + Modules Additius

```
wealth-pilot/
├── backend/
│   ├── core/               ← NI UN SOL CANVI AQUÍ en tota la vida del projecte
│   │   ├── config.py         Pydantic BaseSettings, llegeix .env
│   │   ├── db.py             Engine async, AsyncSessionLocal, Base declarativa
│   │   ├── errors.py         Handlers globals 404/500 amb format JSON consistent
│   │   ├── logging.py        Logging estructurat a stdout (production-ready)
│   │   └── security.py       Placeholder per a API key auth (futur)
│   ├── modules/            ← Tot viu aquí. Cada feature = nova carpeta
│   │   ├── portfolio/        Assets, transaccions, tax lots, preus, dividends
│   │   ├── config/           Escenaris, objectius, paràmetres globals
│   │   ├── sync/             Import MoneyWiz, comptes, categories, transaccions
│   │   ├── simulation/       Motor de projecció, Monte Carlo
│   │   ├── networth/         Snapshots diaris, evolució, milestones
│   │   ├── analytics/        Pressupostos, resums mensuals, patrons de despesa
│   │   ├── market/           Índexs de mercat, tipus de canvi, logs de fetch
│   │   ├── history/          Informes fiscals, guanys realitzats (FIFO)
│   │   ├── realestate/       Propietats, hipoteques, valoracions, lloguers
│   │   ├── pensions/         Plans de pensions, cotitzacions, Seguretat Social
│   │   ├── credit/           Targetes de crèdit, extractes, pagaments
│   │   ├── alerts/           Regles d'alerta, historial de disparaments
│   │   ├── system/           Audit log, API keys, versions, tasques programades
│   │   ├── preferences/      Preferències UI, widgets dashboard, templates
│   │   └── tags/             Etiquetes, notes, relacions many-to-many
│   ├── tests/              ← Suite de tests (pytest, integració real)
│   ├── scripts/            ← Seed, utilitats
│   ├── alembic/            ← Migracions de BD
│   └── main.py             ← Màxim 50 línies. Registra routers. No creix mai.
├── frontend/
│   ├── core/               ← NI UN SOL CANVI AQUÍ
│   │   ├── router.js         Hash-based SPA router
│   │   ├── api.js            HTTP client centralitzat
│   │   ├── store.js          Estat global lleuger
│   │   └── events.js         Event bus sense acoplament
│   └── modules/            ← Cada pantalla = nova carpeta
├── tests/
│   └── run_tests.sh        ← Entry point per a `make test`
├── deployment/             ← Config prod: Nginx, Systemd, deploy.sh
├── docs/                   ← Roadmap + Implementation docs
└── docker-compose.yml      ← Stack complet en un sol fitxer
```

**Regla d'or:** Afegir una nova feature = crear `backend/modules/nom_feature/` i registrar el router a `main.py`. Cap fitxer de `core/` es modifica mai.

---

## Regla CORS_ORIGINS (bug fix important)

pydantic-settings v2 intenta fer `json.loads()` sobre qualsevol camp `list[str]`. Amb un valor com `http://localhost:8080,http://localhost:3000` (sense cometes JSON) llança `JSONDecodeError` **abans** que s'executi cap validador.

**Solució adoptada:**
```python
# core/config.py
CORS_ORIGINS: str = "http://localhost:8080"  # str, NO list[str]

# main.py
allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")]
```

---

## Estratègia de Desplegament

```
Local dev:     Docker Compose   → docker compose up
Production:    Systemd native   → /etc/systemd/system/wealthpilot.service
```

**Diferència clau a l'`.env`:**
- Local: `DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/wealthpilot` (hostname `db` = servei Docker)
- Producció: `DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/wealthpilot` (TimescaleDB local)

La VM d'Oracle Cloud ja té PostgreSQL (TimescaleDB), Python 3.12, Nginx i Systemd. La migració a producció és `git pull + pip install + alembic upgrade head + systemctl restart`. **No cal Docker a producció.**
