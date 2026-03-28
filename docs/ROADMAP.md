# WealthPilot — Roadmap de Desenvolupament

> Versió: 1.7 | Data: Març 2026 | Estat: En curs — Fase 0 ✅ + Fase 1 ✅ + Fase 2 ✅ + Fase 3 ✅ completades, 155 tests verds (108 backend + 47 frontend)

---

## Aclariments Tècnics Importants

### Desenvolupament en mòbil — necessito simulador?

**No per a V1.0.** La app és una PWA (Progressive Web App), el que significa que corre al navegador.
Per simular mòbil durant el desenvolupament:

- **Opció principal (recomanada):** Chrome DevTools → `F12` → icona de mòbil ("Toggle device toolbar") → selecciona iPhone 14 Pro (390×844). Perfecte per al dia a dia, zero friccions.
- **Test en dispositiu real (iPhone/iPad):** Connecta Mac i iPhone a la mateixa WiFi. Obre `http://[IP-del-Mac]:8080` des del Safari de l'iPhone. Sense cap configuració extra.
- **Capacitor (V2 — futur):** Aquí sí cal Xcode + iOS Simulator. Però això és molt més endavant.

**Resum:** Desenvolupa en Chrome, testa en el teu iPhone per WiFi local quan vulguis validar UX real. No cal res més fins a Capacitor.

### Estratègia de desplegament (local → Oracle Cloud)

```
Local dev:     Docker Compose   (aïllament total, postgres local, hot reload, zero conflictes)
Production:    Systemd native   (la VM ja té Nginx, Python 3.12, TimescaleDB/PostgreSQL corrent)
```

**Local:** `docker compose up` = tot el stack en un sol comandament, perfecte per desenvolupar.

**Producció (Oracle Cloud):** La VM ja té infraestructura. **No cal Docker a prod.**
- PostgreSQL: `CREATE DATABASE wealthpilot;` sobre la instància TimescaleDB existent (estalvia RAM i simplicitat)
- Python 3.12 (el que ja hi ha instal·lat)
- Nginx: afegir un virtual host nou al Nginx existent
- Systemd: un nou servei `.service` per a FastAPI (igual que altres projectes a la VM)
- Let's Encrypt/Certbot: ja configurat, afegir el domini quan estigui disponible

**Migrar a producció** = `git pull` + `pip install -r requirements.txt` + `alembic upgrade head` + `systemctl restart wealthpilot`

### Filosofia d'Escalabilitat — El Core que no es toca mai

El principi fonamental: **afegir un nou mòdul = crear una carpeta nova**. Mai tocar codi existent.

```
backend/
  core/           ← NI UN SOL CANVI AQUÍ en tota la vida del projecte
    db.py           (connexió, sessions, base ORM)
    config.py       (Pydantic settings, .env loader)
    errors.py       (error handlers estàndard)
    logging.py      (structured logging)
    security.py     (auth headers, rate limiting futur)
  modules/        ← Aquí viu tot. Cada mòdul = carpeta autocontinguda
    portfolio/
      router.py
      models.py
      schemas.py
      service.py
    simulation/
      router.py
      ...
    analytics/      ← Nou mòdul? Crea la carpeta. Registra el router. Llestos.
      router.py
      ...
  main.py         ← Registra routers. Màxim 30 línies. No creix mai.
```

```
frontend/
  core/           ← NI UN SOL CANVI AQUÍ
    router.js       (SPA navigation)
    api.js          (HTTP client centralitzat)
    store.js        (estat global lleuger)
    events.js       (event bus)
  modules/        ← Cada pantalla/feature = mòdul independent
    dashboard/
    portfolio/
    simulation/
    analytics/      ← Nova pantalla? Crea la carpeta. Registra la ruta. Llestos.
```

---

## Fases del Roadmap

---

## FASE 0 — Infraestructura & Arquitectura Base ✅
**Objectiu:** Entorn de desenvolupament 100% funcional i preparat per créixer sense límits. Tot dockeritzat des del minut 0.
**Estat:** Completada al 100%. 64 taules a la BD, seed aplicat, 36 tests verds (`make test`).

### 0.1 Estructura de directoris del projecte ✅
> Creada tota l'estructura `backend/core/`, `backend/modules/`, `frontend/core/`, `frontend/modules/`, `deployment/` i `docs/`. El principi és immutable: `core/` no es toca mai; cada nova feature viu en una carpeta nova dins `modules/`.

- [x] Crear l'estructura de carpetes completa (`backend/`, `frontend/`, `deployment/`, `docs/`)
- [x] Crear `backend/core/` amb els fitxers base (db.py, config.py, errors.py, logging.py)
- [x] Crear `backend/modules/` buit (cada mòdul s'afegirà aquí)
- [x] Crear `frontend/core/` i `frontend/modules/`
- [x] Crear `.gitignore` complet (Python, Node, Docker, .env, __pycache__, etc.)
- [x] Crear `.env` local + `.env.prod.example` per a Oracle Cloud *(no hi ha .env.example — el .env real és local i gitignored)*

### 0.2 Docker Compose local ✅
> Tres serveis orquestrats: `db` (Postgres 15 amb healthcheck), `backend` (FastAPI amb hot reload via volume mount), `frontend` (Nginx servint estàtics i fent proxy de `/api/` al backend). Volum persistent `postgres_data` i `Makefile` per a les operacions del dia a dia.

- [x] `docker-compose.yml` amb 3 serveis: `db` (postgres:15), `backend` (FastAPI), `frontend` (Nginx)
- [x] Volum persistent per a PostgreSQL (`postgres_data`)
- [x] Hot reload per al backend en local (mount del codi + `--reload`)
- [x] Nginx servint els estàtics del frontend + proxy `/api/` al backend
- [x] Health checks per a tots els serveis
- [x] `Makefile` amb comandes útils: `make dev`, `make logs`, `make db-shell`, `make migrate`

### 0.3 Backend Core (FastAPI skeleton) ✅
> `main.py` de menys de 40 línies registra CORS i routers; `core/` conté configuració (pydantic-settings llegint `.env`), motor de BD (SQLAlchemy async + pool), error handlers globals i logging estructurat a stdout. Afegir un mòdul nou = una línia a `main.py`, la resta no es toca.

- [x] `main.py`: app FastAPI, CORS, middleware, registre de routers — màxim 40 línies
- [x] `core/config.py`: Pydantic BaseSettings llegint `.env` (DATABASE_URL, ENV, LOG_LEVEL, etc.)
- [x] `core/db.py`: Engine SQLAlchemy async, SessionLocal, Base declarativa, dependency `get_db`
- [x] `core/errors.py`: Handlers globals per a 404, 422, 500 amb format JSON consistent
- [x] `core/logging.py`: Logging production-ready des del dia 1
- [x] Endpoint `GET /health` retornant versió i env → verificat `{"status":"ok"}`
- [x] Endpoint `GET /api/v1/` retornant llista de mòduls disponibles

### 0.4 Frontend Core (SPA skeleton) ✅
> SPA en vanilla JS (zero frameworks, zero build step) amb router per hash (`#/dashboard`, etc.), client HTTP centralitzat que emet events de loading/error, event bus per comunicació entre mòduls sense acoplament, i store lleuger. El sistema de disseny en `css/variables.css` defineix tots els tokens que usaran els mòduls.

- [x] `index.html` minimalista amb mounting point i imports
- [x] `core/router.js`: Router SPA basat en hash amb lazy-load de mòduls
- [x] `core/api.js`: Client HTTP centralitzat (fetch wrapper amb error handling i events)
- [x] `core/store.js`: Estat global mínim reactiu via events
- [x] `core/events.js`: Event bus per comunicació entre mòduls sense acoplament
- [x] `manifest.json` PWA + `service-worker.js` (cache-first per estàtics, network-first per `/api/`)
- [x] CSS: `variables.css` (design tokens dark theme), `base.css`, `components.css` (cards, badges, nav, skeletons...)

### 0.5 Base de Dades & Migracions ✅
> Schema "astronomicament gran" de 64 taules repartides en 15 mòduls (portfolio, config, sync, simulation, networth, analytics, market, history, realestate, pensions, credit, alerts, system, preferences, tags). SQLAlchemy 2.0 (`Mapped`/`mapped_column`). Primera migració Alembic aplicada. Seed idempotent amb 8 assets, 24 escenaris, 7 contribucions, 18 paràmetres, 2 objectius, 4 índexs de mercat i 8 widgets de dashboard.

- [x] Alembic inicialitzat i configurat per a migracions incrementals (async)
- [x] Schema complet en models SQLAlchemy — 64 taules en 15 mòduls (pensa en gran: millor esborrar que crear)
- [x] Primera migració Alembic aplicada (`make migrate`)
- [x] Seed script idempotent amb totes les dades inicials (`make seed`)

### 0.6 Validació Fase 0 ✅
> Stack completament verificat: backend responent, BD amb 64 taules i seed aplicat, 36 tests automàtics passant en verd (`make test`). Test suite cobreix: connexió BD, presència de totes les taules, índexs, constraints úniques, dades seed, i tots els endpoints de l'API.

- [x] `docker compose up` arranca sense errors (`make dev`)
- [x] `GET /health` retorna 200 → `{"status":"ok","version":"0.1.0","env":"development"}`
- [x] Connexió a PostgreSQL verificada — 64 taules creades i verificades per tests
- [x] Frontend servit per Nginx a `http://localhost:8080`
- [x] Migracions executades correctament (`make migrate`)
- [x] Seed aplicat: 8 assets, escenaris, contribucions i paràmetres a la BD (`make seed`)
- [x] **36 tests automàtics passant** (`make test`) — BD, seed i API coberts

---

## FASE 1 — Integracions de Dades Externes
**Objectiu:** Obtenir preus reals de Yahoo Finance i importar dades de MoneyWiz. Aquests serveis alimentaran tota la resta.

### 1.1 Servei Yahoo Finance ✅

Gap fill robust que descarrega tot l'historial des de la data d'inceptació, recupera automàticament dels outages, i serveix preus des de la BD amb cache de 5 min. 53 tests automàtics verds.

- [x] `modules/market/service.py`: servei complet amb gap fill, cache i stale detection
- [x] `fill_all_gaps(db)`: gap fill per asset (MAX price_date → download des de allà), batches per start_date, ON CONFLICT DO NOTHING, commit per ticker, log a price_fetch_logs
- [x] `get_current_prices(db)`: window function (ROW_NUMBER PARTITION BY asset_id), cache 5 min, stale detection (3 dies ETF, 1 dia crypto), canvi 1d en % i €
- [x] `get_asset_price_history(db, asset_id, days)`: historial OHLCV amb LAG per a change_pct
- [x] Gestió robusta: batch download → fallback individual amb retry exponential (3 intents)
- [x] Lifespan a `main.py`: gap fill automàtic a l'arrencada (non-fatal si Yahoo no respon)
- [x] `modules/market/router.py`: 4 endpoints (`/prices`, `/prices/{id}`, `/refresh`, `/history/{id}`)
- [x] `modules/market/schemas.py`: 5 schemas Pydantic v2 (AssetPriceOut, MarketPricesResponse, GapFillResponse, PriceHistoryPoint, AssetPriceHistoryResponse)
- [x] `backend/tests/test_market.py`: 17 tests d'integració (taules BD + endpoints API)
- [x] Fix NullPool als tests: fixture `_use_null_pool` a conftest.py resol el problema de "Future attached to different loop" entre event loops de pytest-asyncio

### 1.2 Servei MoneyWiz Parser ✅
Estratègia **mirror complet**: la BD és còpia fidel del darrer backup. Upsert de tot + prune del que ja no hi és. Shares i símbol de cada transacció d'inversió extrets de `ZNUMBEROFSHARES`/`ZSYMBOL1`. `records_skipped` ara significa registres eliminats (mirror purge).

- [x] `modules/sync/service.py`: lògica d'extracció del `.zip` → SQLite intern de MoneyWiz (Core Data, taula `ZSYNCOBJECT`)
- [x] Parser de comptes (`mw_accounts`): 7 tipus (checking, savings, cash, credit, loan, investment, forex)
- [x] Parser de categories (`mw_categories`): jerarquia resoluble en 2 passos (pares primer, self-join per FKs)
- [x] Parser de transaccions (`mw_transactions`): 6 tipus, imports positius, timestamps Apple epoch, category via JOIN
- [x] Parser inversions: `investment_buy`/`investment_sell` amb `shares` (ZNUMBEROFSHARES) i `mw_symbol` (ZSYMBOL1)
- [x] Estratègia mirror: `ON CONFLICT DO UPDATE` + `_prune_removed()` esborra el que ja no és al ZIP
- [x] `modules/sync/router.py`: `POST /api/v1/sync/upload`, `GET /api/v1/sync/status`, `GET /api/v1/sync/batches`
- [x] Audit trail complet: `ImportBatch` sempre es crea (status=failed si hi ha error)
- [x] Trigger post-upload: crida `networth_service.generate_snapshot()` automàticament (non-fatal)
- [x] 34 tests: schema BD, parser pur (sense BD), endpoints + test d'idempotència

### 1.3 Snapshot de Net Worth ✅
Total des de `mw_accounts.current_balance` (font de veritat). Desglossat per asset via `shares × preu YF`. Idempotent per data. Trigger automàtic post-sync. Scripts CLI per a ús diari.

- [x] `modules/networth/service.py`: `generate_snapshot()` — cash + inv + liab des de MW, posicions (shares × preu) per asset
- [x] `modules/networth/router.py`: `POST /api/v1/networth/snapshot`, `GET /api/v1/networth/history?period=1y`
- [x] `modules/networth/models.py`: `NetWorthSnapshot`, `AssetSnapshot` (uq_networth_date, CASCADE delete)
- [x] `modules/networth/schemas.py`: `GenerateSnapshotResponse`, `NetWorthHistoryResponse`, `NetWorthSnapshotOut`, `AssetSnapshotOut`
- [x] Trigger automàtic: `process_upload()` crida `generate_snapshot(trigger_source="sync")` post-import
- [x] `change_eur` / `change_pct` calculats vs. snapshot anterior (no necessàriament el dia anterior)
- [x] `scripts/net_worth.py` + `make net-worth`: resum CLI amb comptes, posicions per asset, P&L, últim snapshot
- [x] `tests/test_networth.py`: 15 tests (schema BD, endpoints POST/GET, lògica de servei amb dades sintètiques)

---

## FASE 2 — MVP V1.0: Dashboard & Portfolio ✅
**Objectiu:** Primera pantalla funcional amb dades reals. El moment "wow" del projecte.
**Estat:** Completada al 100%. Dashboard + Portfolio visuals amb dades reals. 47 tests frontend verds.

### 2.1 Backend Portfolio API ✅
> `modules/portfolio/` amb lògica de rebalanceig i resum. Networth history amb `asset_snapshots` complets (display_name, ticker_yf, color_hex, pnl_eur). Fix crítics: camp `unrealized_pnl_eur` → `pnl_eur` (alineació frontend/backend), i el router retornava `asset_snapshots: []` hardcoded.

- [x] `modules/portfolio/service.py`:
  - [x] `get_portfolio_summary()`: net worth total, canvi diari, % canvi
  - [x] `get_asset_breakdown()`: per asset via `asset_snapshots` — shares, preu, valor, cost basis, P&L €, P&L %, pes real
  - [x] `get_rebalancing()`: assets sobreponderat/infraponderat + import a moure, ordent per urgència
  - [ ] `get_on_track_status()`: compara net worth vs. projecció base *(Fase 3 — requereix motor simulació)*
- [x] `modules/portfolio/router.py`:
  - [x] `GET /api/v1/portfolio/summary`
  - [x] `GET /api/v1/portfolio/rebalance`
- [x] Fix `networth/router.py`: ara retorna `asset_snapshots` amb JOIN a `assets` (display_name, ticker_yf, color_hex)
- [ ] Cost basis FIFO *(Fase 3 — implementat amb cost basis simple ara; FIFO quan s'implementi historial fiscal)*

### 2.2 Frontend Dashboard ✅
> React 18 + TypeScript + Vite 5. Design system Liquid Glass. SVG pur per a tots els gràfics. TanStack Query + Zustand. 47 tests Vitest.

- [x] Scaffold complet amb Vite + React + TypeScript (`frontend/` reorganitzat)
- [x] Design tokens CSS (dark/light via classe `<html>.dark`) + Card, NavBar, StatusDot, TimeSelector
- [x] `features/dashboard/`: HeroValue, ChartSection (PortfolioChart morfing SVG), StatusCards, Allocation (DonutChart + llista), TopMovers, Alerts
- [x] GoalRing SVG per a l'objectiu d'habitatge
- [x] Loading skeletons + timestamp actualització + StatusDot live/stale

### 2.3 Frontend Portfolio ✅
- [x] `features/portfolio/PortfolioScreen.tsx`: llista assets amb shares, preu actual, valor €, P&L €/%, pes cartera
- [x] Cards agrupades amb border radius fluid (primera/última/intermèdies)
- [x] Bottom NavBar: Inici | Cartera | (Sim | Hist | Config pendents)

### 2.4 Validació Fase 2 ✅
- [x] Net worth real visible al Dashboard: 23.862,98 € (dades MoneyWiz + YF)
- [x] 5 assets amb preus reals a la cartera (Japan i Europe Defence sense posició actual)
- [x] DonutChart + gràfic morfing renderitzats correctament (390px)
- [x] Rebalanceig: MSCI World +31.31% (sobreponderat), Japan -6% (missing)
- [x] Dark/light toggle via Zustand + classe `<html>.dark`
- [x] Endpoints verificats: `/api/v1/portfolio/summary`, `/api/v1/portfolio/rebalance`, `/api/v1/networth/history`

---

## FASE 3 — MVP V1.0: Simulació & Historial ✅
**Objectiu:** Motor de simulació + historial de transaccions. Tancar V1.0 MVP funcional.
**Estat:** Completada al 100%. Motor de simulació + historial operatius. TypeScript 0 errors.

### 3.1 Backend Motor de Simulació ✅
> `modules/simulation/`: motor pur (`engine.py`) + servei + router. Retorn ponderat per pesos actuals de cartera. Objectiu habitatge inclòs al gràfic (línia groga).

- [x] `modules/simulation/engine.py`: funció pura `project()` — FV = PV×(1+r)^n + PMT×[(1+r)^n−1]/r; helper `cagr()`, `monthly_rate()`
- [x] Retorn ponderat de cartera: blended = Σ(weight_i × return_i) dels actuals de l'últim snapshot
- [x] 3 escenaris llegits de la taula `scenarios`: adverse (2.42%), base (6.38%), optimistic (10.34%)
- [x] `GET /api/v1/simulation/scenarios` — escenaris + contribucions actives + cartera actual
- [x] `GET /api/v1/simulation/project?horizon_years=10&monthly_contribution=X` — projecció 3 escenaris
  - Retorna sèrie mensual completa per a cada escenari (121 punts per 10 anys)
  - Mètriques: end_value, total_return_eur/pct, cagr_pct, total_contributions_eur
  - Objectiu habitatge: target_amount + target_date des de la taula `objectives`
- [ ] Cache de resultats en `simulation_results` *(futur — peticions freqüents s'acceleren ja que TanStack Query fa caching al client)*
- [ ] Contribucions extraordinàries *(Fase 4)*

### 3.2 Backend Historial ✅
> `modules/history/`: transaccions paginades + resum per asset amb P&L calculat des de preus actuals YF.

- [x] `modules/history/service.py`:
  - [x] `get_transactions()`: paginació + filtres (tx_type, ticker_yf, date_from, date_to)
  - [x] `get_investment_summary()`: per asset — shares, total invertit, cost mig, valor actual, P&L €/%
- [x] `modules/history/router.py`:
  - [x] `GET /api/v1/history/transactions` — 1.471 transaccions paginades
  - [x] `GET /api/v1/history/investments` — resum per asset amb preus YF actuals
- [ ] `GET /api/v1/history/tax-report?year=2025` — plusvàlues IRPF *(Fase 4 — requereix implementació FIFO)*

### 3.3 Frontend Simulació ✅
> `features/simulation/SimulationScreen.tsx` + `components/charts/ProjectionChart.tsx` (SVG reutilitzable)

- [x] `ProjectionChart.tsx`: SVG 3 línies (adverse/base/optimistic) amb animació d'entrada (700ms, ease-out cubic)
  - Àrea sombreada entre advers i optimista, línia d'objectiu (groga puntejada), dots al final
  - X-axis: etiquetes d'anys adaptatives, Y-axis: format k/M€
- [x] `SimulationScreen.tsx`:
  - Slider d'horitzó 1–30 anys amb marks clickables
  - Cards de resultat per escenari (end value, rendiment %, CAGR)
  - ContributionInfo: aportació mensual + total aportat a l'horitzó
  - Taula de retorns ponderats per escenari
  - Línia objectiu habitatge visible al gràfic si dins del rang

### 3.4 Frontend Historial ✅
> `features/history/HistoryScreen.tsx` — investment summary + llista de transaccions

- [x] Resum inversions: total invertit, P&L total €/%, llistat per asset amb shares/cost mig/P&L
- [x] Transaccions paginades (25/pàgina) amb filtres per tipus (pills)
- [x] Paginació amb "Anterior / Següent"
- [x] TransactionRow: tipus badge, descripció, data, import, shares per inversions

### 3.5 PWA — Instal·lació Mòbil
- [ ] `manifest.json` complet: icones múltiples, theme_color, display: standalone
- [ ] Banner "Afegir a pantalla d'inici" per iOS Safari
- [ ] Test instal·lació com a PWA a iPhone real

### 3.6 Validació V1.0 MVP
- [x] Dashboard → Portfolio → Simulació → Historial navegables
- [x] MoneyWiz backup sincronitzat (1.471 transaccions)
- [x] Simulació 10 anys: base €125.742, advers €98.718, optimista €160.911
- [x] TypeScript 0 errors (`make check-fe`)
- [ ] App instal·lable com a PWA a l'iPhone *(Fase 4)*
- [ ] **V1.0 MVP FUNCIONAL LOCAL — MILESTONE 1** 🎯 *(pendent validació visual per l'usuari)*

---

## FASE 4 — V2.0: Gestió de Configuració via UI
**Objectiu:** Zero fitxers de configuració. Tot editable des de la interfície.

### 4.1 Backend Config APIs (CRUD complet)
- [ ] `modules/config/router.py` amb endpoints per a:
  - [ ] `GET/PUT /api/v1/config/assets` — llistar i editar assets (nom, ticker, target weight, actiu/inactiu)
  - [ ] `POST /api/v1/config/assets` — afegir nou asset
  - [ ] `GET/PUT /api/v1/config/contributions` — contribucions mensuals (import, dia del mes, asset destí)
  - [ ] `GET/PUT /api/v1/config/extraordinary` — contribucions extraordinàries (data futura, import, asset)
  - [ ] `GET/PUT /api/v1/config/scenarios` — retorns esperats per escenari i asset
  - [ ] `GET/PUT /api/v1/config/objectives` — objectius financers (home purchase: preu, data, % necessari)
  - [ ] `GET/PUT /api/v1/config/parameters` — paràmetres globals (balanç cash, tipus d'interès, etc.)
- [ ] Validació estricta: target weights han de sumar 100% (o alerta si no)
- [ ] Historial de canvis en `parameters` (qui canvià què i quan, per auditoria)

### 4.2 Frontend Configuració
- [ ] `modules/config/index.js` — menú de configuració amb sub-seccions
- [ ] **Gestió d'Assets**: taula editable inline, toggle actiu/inactiu, afegir nou asset amb formulari
- [ ] **Contribucions Mensuals**: llista amb import i asset editable, indicador "pròxima execució"
- [ ] **Contribucions Extraordinàries**: calendari o llista, marcar com executada
- [ ] **Escenaris de Retorn**: grid d'inputs (asset × escenari = % anual)
- [ ] **Objectius Financers**: formulari per editar home purchase goal, afegir nous objectius
- [ ] **Paràmetres Globals**: formulari genèric que llegeix la `parameters` table dinàmicament
- [ ] Feedback visual: toast de confirmació en guardar, vermell si hi ha error de validació

### 4.3 Validació Fase 4
- [ ] Afegir un nou asset des de la UI → apareix immediatament al portfolio
- [ ] Modificar target weight → rebalanceig actualitzat al dashboard
- [ ] Canviar retorns d'escenari → simulació recalculada automàticament
- [ ] Tots els canvis persistits a PostgreSQL

---

## FASE 5 — V2.0: Analítica Personal & Simulador Obert
**Objectiu:** Anàlisi profunda de finances personals i simulador de qualsevol escenari imaginable.

### 5.1 Backend Analítica Personal
- [ ] `modules/analytics/service.py`:
  - [ ] `get_expense_breakdown(year, month)`: top 10 categories, % del total
  - [ ] `get_networth_evolution(period)`: net worth mensual últims N mesos
  - [ ] `get_savings_comparison(year)`: estalvi real vs. planificat mes a mes
  - [ ] `get_alerts()`: categories > +30% mitjana, estalvi < -20% objectiu
  - [ ] `get_income_expenses_summary(month)`: ingressos vs. despeses vs. inversió
- [ ] `modules/analytics/router.py`:
  - [ ] `GET /api/v1/analytics/expenses?year=2025&month=3`
  - [ ] `GET /api/v1/analytics/networth?period=12m`
  - [ ] `GET /api/v1/analytics/savings?year=2025`
  - [ ] `GET /api/v1/analytics/alerts`

### 5.2 Backend Simulador Obert
- [ ] `modules/simulation/open_simulator.py`:
  - [ ] Suport escenaris amb nom (guardar a `simulations` table)
  - [ ] Override de qualsevol paràmetre per escenari (ingressos, despeses, contribucions, retorns, events puntuals)
  - [ ] Comparació fins a 3 escenaris simultanis (retorna les 3 sèries en una sola crida)
  - [ ] Events de vida modelables: canvi de feina (+€500/mes), compra de casa (−€80k en data X)
- [ ] `GET /api/v1/simulation/saved` — llista escenaris guardats
- [ ] `POST /api/v1/simulation/compare` — compara N escenaris, retorna sèries temporals

### 5.3 Frontend Analítica Personal
- [ ] `modules/analytics/index.js` amb sub-vistes
- [ ] **Despeses per Categoria**: bar chart horitzontal top 10, filtrable per mes
- [ ] **Evolució Net Worth**: line chart mensual amb anotacions d'events importants
- [ ] **Estalvi Real vs. Planificat**: grouped bar chart mes a mes
- [ ] **Alertes Automàtiques**: llista de desviacions detectades amb severitat

### 5.4 Frontend Simulador Obert
- [ ] `modules/simulation/open.js`
- [ ] Llista d'escenaris guardats (ex: "Actual", "Canvi de feina", "Casa 2029")
- [ ] Editor d'escenari: sliders + inputs per a cada paràmetre modificable
- [ ] Preview en temps real de la projecció mentre es canvien sliders
- [ ] Comparació side-by-side de fins a 3 escenaris (3 línies al gràfic + taula de milestones)
- [ ] Botó "Guardar escenari" amb nom personalitzat

### 5.5 Validació V2.0 Complet ✅
- [ ] Breakdown de despeses renderitzat des de dades reals de MoneyWiz
- [ ] Escenari "Canvi de feina" creat i comparat amb "Actual" gràficament
- [ ] Net worth evolution dels últims 12 mesos visible
- [ ] **V2.0 FUNCIONAL LOCAL — MILESTONE 2** 🎯

---

## FASE 6 — Migració a Oracle Cloud (Producció)
**Objectiu:** Desplegar sobre la infraestructura existent de la VM. La VM ja té PostgreSQL (TimescaleDB), Python 3.12, Nginx i Systemd — cap instal·lació nova necessària.

### 6.1 Preparació del codi per a producció
- [ ] Variables d'entorn separades: `.env.dev` (local Docker) i `.env.prod` (VM)
- [ ] `requirements.txt` tancat amb versions exactes (`pip freeze > requirements.txt`)
- [ ] Afegir `gunicorn` com a servidor WSGI per a producció (vs. `uvicorn --reload` en dev)
- [ ] Script `deployment/deploy.sh`: `git pull` + `pip install` + `alembic upgrade head` + `systemctl restart wealthpilot`
- [ ] Validar que no hi ha cap path hardcoded ni secret al codi

### 6.2 Oracle Cloud VM — Configuració (infraestructura ja existent)
- [ ] Obrir ports 80 i 443 a la **Security List d'OCI** (pas crític, sovint oblidat)
- [ ] Obrir ports 80 i 443 a `iptables` del sistema si hi ha firewall local actiu
- [ ] Crear base de dades: `CREATE DATABASE wealthpilot;` sobre la instància TimescaleDB existent
- [ ] Crear usuari PostgreSQL dedicat: `CREATE USER wealthpilot_user WITH PASSWORD '...';`
- [ ] Crear entorn virtual Python: `python3.12 -m venv /opt/wealthpilot/venv`
- [ ] Clonar repo a `/opt/wealthpilot/app`

### 6.3 Systemd Service per a FastAPI
- [ ] Crear `/etc/systemd/system/wealthpilot.service`:
  ```ini
  [Unit]
  Description=WealthPilot FastAPI Backend
  After=network.target postgresql.service

  [Service]
  User=wealthpilot
  WorkingDirectory=/opt/wealthpilot/app/backend
  EnvironmentFile=/opt/wealthpilot/.env.prod
  ExecStart=/opt/wealthpilot/venv/bin/gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
  Restart=always

  [Install]
  WantedBy=multi-user.target
  ```
- [ ] `systemctl enable wealthpilot && systemctl start wealthpilot`

### 6.4 Nginx Virtual Host
- [ ] Afegir fitxer a `/etc/nginx/sites-available/wealthpilot`:
  - Servir `/` → fitxers estàtics del frontend
  - Proxy `/api/` → `http://127.0.0.1:8000`
- [ ] `nginx -t && systemctl reload nginx`

### 6.5 HTTPS & Domini (quan estigui disponible)
- [ ] Certbot: `certbot --nginx -d [domini]` (auto-renovació cada 90 dies ja configurada a la VM)
- [ ] HSTS headers activats a Nginx
- [ ] *Sense domini: accés per IP pública és suficient per a les fases inicials*

### 6.6 Backup & Recuperació
- [ ] Script diari: `pg_dump wealthpilot | gzip > /backups/wealthpilot-$(date +%Y%m%d).sql.gz`
- [ ] Retenció 7 dies locals + Oracle Object Storage (gratuït fins 20GB) per a 30 dies
- [ ] Script de restore documentat i testat en local abans de desplegar
- [ ] Cron job: `0 3 * * * /opt/wealthpilot/scripts/backup.sh`

### 6.7 Monitoratge Bàsic
- [ ] UptimeRobot (free tier): monitoreja `GET /health` cada 5 minuts
- [ ] Logs: `journalctl -u wealthpilot` + rotació automàtica via systemd
- [ ] Alerta simple d'espai en disc (script cron)

### 6.8 Validació Migració ✅
- [ ] App accessible per IP pública de Oracle Cloud
- [ ] MoneyWiz sync funcionant des de l'iPhone en xarxa mòbil (no WiFi local)
- [ ] Backup automàtic executat i restauració testada
- [ ] **PRODUCCIÓ LIVE — MILESTONE 3** 🎯

---

## FASE 7 — iOS Natiu amb Capacitor (Opcional, Futur)
**Objectiu:** Empaquetar la PWA com a app nativa d'iOS per a millor UX i distribució via TestFlight.

### 7.1 Integració Capacitor
- [ ] Instal·lar `@capacitor/core` i `@capacitor/ios`
- [ ] `capacitor.config.json`: apunta al servidor de producció
- [ ] Revisar plugins necessaris: `@capacitor/push-notifications`, `@capacitor/share`, `@capacitor/haptics`
- [ ] Generar projecte Xcode (`npx cap add ios`)

### 7.2 iOS Shortcut per MoneyWiz Sync
- [ ] Shortcut d'iOS que: detecta nou backup de MoneyWiz → puja a `POST /api/v1/sync/upload` automàticament
- [ ] Autenticació amb API key (header `X-API-Key`)
- [ ] Notificació push post-sync

### 7.3 Distribució TestFlight
- [ ] Apple Developer Account (€99/any)
- [ ] Build via Xcode + arxivat
- [ ] Distribució interna via TestFlight

---

## FASE 8+ — Features Futures (Backlog)
*Ordenades per valor percebut, no necessàriament en aquest ordre.*

### Nous Mòduls
- [ ] **Immobles**: afegir immobles al net worth (valor estimat, hipoteca, rendibilitat)
- [ ] **Pensions**: integrar Seguretat Social + plans de pensions privats
- [ ] **Targetes de crèdit**: tracking de límit, deute pendent, venciments
- [ ] **Divises**: exposició a divisa per asset, cobertura natural

### Millores de Simulació
- [ ] Inflació com a paràmetre explícit (valor real vs. nominal)
- [ ] Modelació de jubilació (quan puc jubilar-me amb X€/mes?)
- [ ] Monte Carlo simulation (N iteracions aleatòries → distribució de resultats)
- [ ] Optimitzador de cartera (Markowitz o versió simplificada)

### Millores d'UX
- [ ] Mode fosc / clar (ara sempre fosc)
- [ ] Widgets iOS (Capacitor + WidgetKit)
- [ ] Notificacions push per alertes (desviació > threshold)
- [ ] Exportació PDF d'informes (fiscal anual, resum de cartera)
- [ ] Múltiples monedes (ara sempre EUR)

### Integracions Externes
- [ ] Importació automàtica des de broker (Interactive Brokers API, si aplica)
- [ ] Integració Bizum/Revolut per despeses ràpides
- [ ] Open Banking (PSD2) per importar moviments bancaris directament

### Infraestructura
- [ ] Redis per a cache de preus (TTL configurable, evitar rate limit Yahoo)
- [ ] Celery + Redis per a tasques asíncrones (recàlcul simulacions en background)
- [ ] CI/CD pipeline (GitHub Actions: test → build → deploy)
- [ ] Tests automatitzats: pytest per backend, Playwright per frontend E2E

---

## Principis d'Arquitectura No Negociables

| Principi | Implementació |
|----------|---------------|
| API-first | Tot passa per `/api/v1/`. La UI mai calcula res. |
| Single source of truth | PostgreSQL és l'únic lloc on viuen paràmetres i configuració |
| Idempotent per defecte | Pujar el mateix backup 2 vegades → 0 efectes secundaris |
| Mòdul = carpeta | Afegir feature = crear carpeta. Cap fitxer core es toca. |
| Versionat des del dia 1 | `/api/v1/` prefix. Alembic per a DB. Semver per a releases. |
| Mobile-first | Totes les vistes dissenyades per 390px primer, desktop après |
| Zero paràmetres en codi | Qualsevol número configurable va a `parameters` table |

---

## Eines de Desenvolupament Recomanades

| Eina | Ús |
|------|----|
| **Chrome DevTools** | Simulació mòbil (iPhone 14 Pro, 390×844) en local |
| **TablePlus / DBeaver** | Client PostgreSQL visual per inspeccionar dades |
| **Bruno / Insomnia** | Test d'endpoints API (alternativa a Postman, sense cloud) |
| **http://[IP-Mac]:8080** | Test en iPhone/iPad real per WiFi sense cap configuració extra |

---

*Última actualització: 26 Març 2026 — Fase 0 (0.1–0.4) completada i verificada*
