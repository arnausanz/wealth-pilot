# WealthPilot — Product Requirements Document
**Versió:** 2.0  
**Data:** 23 març 2026  
**Estat:** ✅ Aprovat per a desenvolupament  
**Arquitectura:** Full-stack · PostgreSQL · FastAPI · PWA + Capacitor iOS  

---

## Taula de continguts

1. [Visió i definició del projecte](#1-visió-i-definició-del-projecte)
2. [Usuari i context](#2-usuari-i-context)
3. [Arquitectura global](#3-arquitectura-global)
4. [Base de dades — Esquema complet](#4-base-de-dades--esquema-complet)
5. [Features V1.0 — WealthPilot Core](#5-features-v10--wealthpilot-core)
6. [Features V2.0 — WealthPilot Full](#6-features-v20--wealthpilot-full)
7. [Mockups visuals](#7-mockups-visuals)
8. [Stack tecnològic](#8-stack-tecnològic)
9. [Estructura del projecte](#9-estructura-del-projecte)
10. [Planning de desenvolupament](#10-planning-de-desenvolupament)
11. [Apèndixs](#11-apèndixs)

---

## 1. Visió i definició del projecte

### Visió

**WealthPilot** és una plataforma personal de gestió patrimonial i analítica financera dissenyada per a un únic usuari. Integra dades d'inversió en temps real, historial complet de finances personals, i un motor de simulació obert que permet modelar qualsevol escenari financer futur.

L'aplicació és **completament customitzable des de la UI**: tots els paràmetres (aportacions, actius, escenaris, objectius) es poden modificar en temps real sense tocar codi ni configuració externa.

### Problemes que resol

| Problema | Solució WealthPilot |
|---|---|
| No hi ha vista consolidada del patrimoni en temps real | Dashboard amb preus via Yahoo Finance API |
| Les simulacions s'han de fer manualment i no s'actualitzen | Motor de simulació adaptativa connectat a dades reals |
| No es pot saber si l'estratègia va "on track" | Comparació automàtica real vs. projecció |
| Els paràmetres (aportacions, escenaris) estan en fitxers | BD PostgreSQL editable des de la UI |
| No hi ha analítica de despeses personals | Importació i anàlisi de transaccions MoneyWiz |
| No es poden modelar escenaris vitals (canvi feina, compra pis) | Simulador obert amb escenaris guardats |

### Principi de disseny fonamental

> **Tot el que es pot configurar, es configura des de la UI. Cap paràmetre requereix editar codi o fitxers.**

Això inclou: actius, tickers, pesos objectiu, rendiments esperats, aportacions mensuals, aportacions extraordinàries, objectius financers, escenaris de simulació, i qualsevol variable futura.

---

## 2. Usuari i context

### Perfil

- **Edat:** 30 anys · **País:** Espanya (fiscalitat espanyola)
- **Perfil inversor:** Moderat, aversió a pèrdues fortes, horitzó 15+ anys
- **Objectiu financer primari:** Construir patrimoni + entrada habitatge en 3-4 anys
- **Comportament:** Molt metòdic, actualitza MoneyWiz diàriament
- **Dispositius:** iPhone (principal), iPad, Mac
- **Nivell tècnic:** Intermedi-avançat (Python, JS) — col·labora amb IA per al desenvolupament

### Cartera actual

| Actiu | Ticker MoneyWiz | Ticker Yahoo Finance | Pes objectiu |
|---|---|---|---|
| MSCI World | EUNL | IWDA.AS | 22% |
| Or físic | PPFB | PHAU.L | 12% |
| MSCI Europe | EUNK | IMAE.MI | 10% |
| MSCI EM IMI | IS3N | IS3N.AS | 5% |
| Japó | CSJP | CSJP.AS | 6% |
| Defensa Europa | WDEF | WDEF.MI | 5% |
| Bitcoin | BTC | BTC-EUR | 2% |
| Efectiu | — | — | 25-30% |

### Aportacions mensuals actuals (editables des de la UI)

| Actiu | Import | Dia del mes |
|---|---|---|
| MSCI Europe | 75 € | 2 |
| MSCI EM IMI | 75 € | 2 |
| Japó | 50 € | 2 |
| MSCI World | 25 € | 2 |
| Or físic | 25 € | 2 |
| Defensa Europa | 25 € | 2 |
| Bitcoin | 25 € | 2 |
| **Total inversió** | **300 €** | |
| Efectiu (estalvi) | 375 € | — |

### Fonts de dades

| Font | Contingut | Freqüència |
|---|---|---|
| MoneyWiz backup (.zip SQLite) | Totes les transaccions financeres personals | Manual / iOS Shortcut diari |
| Yahoo Finance API | Preus actuals dels ETFs i BTC | En temps real (cada consulta) |
| PostgreSQL (BD pròpia) | Paràmetres, configuració, escenaris, resultats | Persistència permanent |

---

## 3. Arquitectura global

```
┌─────────────────────────────────────────────────────────┐
│  FONTS EXTERNES                                         │
│                                                         │
│  MoneyWiz (iOS)          Yahoo Finance API              │
│  backup .zip (SQLite)    preus temps real               │
│       │                        │                        │
│       └──────────┬─────────────┘                        │
└──────────────────┼──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  ORACLE CLOUD FREE TIER · Ubuntu 22.04                  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  PostgreSQL 15                                  │   │
│  │  Base de dades principal                        │   │
│  │  · Cartera i transaccions                       │   │
│  │  · Configuració editable                        │   │
│  │  · Finances personals (MoneyWiz)                │   │
│  │  · Simulacions guardades                        │   │
│  │  · Snapshots de net worth                       │   │
│  └──────────────────┬──────────────────────────────┘   │
│                     │                                   │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │  FastAPI (Python 3.11+)                         │   │
│  │  API REST                                       │   │
│  │                                                 │   │
│  │  /api/portfolio    → posicions + preus reals    │   │
│  │  /api/simulation   → projeccions adaptatives    │   │
│  │  /api/history      → historial transaccions     │   │
│  │  /api/analytics    → analítica finances pers.   │   │
│  │  /api/scenarios    → CRUD escenaris simulació   │   │
│  │  /api/config       → CRUD paràmetres globals    │   │
│  │  /api/assets       → CRUD actius i pesos        │   │
│  │  /api/contributions→ CRUD aportacions           │   │
│  │  /api/upload       → ingesta backup MoneyWiz    │   │
│  └──────────────────┬──────────────────────────────┘   │
│                     │                                   │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │  Nginx                                          │   │
│  │  Reverse proxy + HTTPS (Let's Encrypt)          │   │
│  │  Serveix la web app estàtica                    │   │
│  └──────────────────┬──────────────────────────────┘   │
└─────────────────────┼───────────────────────────────────┘
                      │ HTTPS · JSON
           ┌──────────┴──────────┐
           ▼                     ▼
  ┌────────────────┐   ┌─────────────────────┐
  │  Web App PWA   │   │  Capacitor iOS App  │
  │  Instal·lable  │   │  (V2.0, opcional)   │
  │  via Safari    │   │  via Xcode sideload │
  └────────────────┘   └─────────────────────┘
           │
           ▼
  ┌────────────────────────────────────────┐
  │  iOS Shortcut                          │
  │  Puja backup MoneyWiz → /api/upload    │
  │  Trigger: manual o programat (8h)      │
  └────────────────────────────────────────┘
```

### Principis d'arquitectura

1. **Single source of truth:** La BD PostgreSQL és l'única font de veritat per a paràmetres i configuració. Cap fitxer de configuració extern.
2. **Separació clara:** La UI mai fa càlculs. Tot el processament és al backend. La UI només mostra i edita.
3. **API-first:** Totes les funcionalitats s'exposen via API REST. Permet afegir qualsevol client futur (web, mòbil, script) sense canviar el backend.
4. **Idempotència a la ingesta:** Pujar el mateix backup MoneyWiz dues vegades no duplica dades. La ingesta és idempotent per data + import + ticker.

---

## 4. Base de dades — Esquema complet

### Decisió tecnològica: PostgreSQL 15

**Per què PostgreSQL i no SQLite:**

| Criteri | PostgreSQL | SQLite |
|---|---|---|
| Concurrència | Excel·lent (MVCC) | Limitada (file locks) |
| JSON natiu | JSONB indexable | Limitat |
| Escalabilitat | Sense límit pràctic | Fins a ~100GB |
| Suport Oracle Ubuntu | Natiu, packages oficials | Sí però menys optimitzat |
| Futures extensions | TimescaleDB, partitioning | No |
| Backup i replicació | pg_dump, streaming replication | Manual |

Per a un projecte personal amb potencial de créixer, PostgreSQL és la decisió correcta.

---

### Esquema SQL complet

```sql
-- ═══════════════════════════════════════════════════
-- CAPA 1: CARTERA D'INVERSIÓ
-- ═══════════════════════════════════════════════════

-- Actius definits (editables des de UI)
CREATE TABLE assets (
    id              SERIAL PRIMARY KEY,
    ticker_mw       VARCHAR(20) UNIQUE NOT NULL,  -- ticker intern MoneyWiz (EUNL)
    ticker_yf       VARCHAR(20) NOT NULL,          -- ticker Yahoo Finance (IWDA.AS)
    name            VARCHAR(100) NOT NULL,
    display_name    VARCHAR(50) NOT NULL,
    asset_type      VARCHAR(20) NOT NULL,          -- 'etf', 'crypto', 'cash', 'commodity'
    currency        VARCHAR(5) DEFAULT 'EUR',
    color_hex       VARCHAR(7),                    -- per als gràfics (#3b82f6)
    is_active       BOOLEAN DEFAULT TRUE,
    target_weight   DECIMAL(5,2),                  -- % objectiu (22.00)
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Aportacions mensuals planificades (editables des de UI)
CREATE TABLE contributions (
    id              SERIAL PRIMARY KEY,
    asset_id        INTEGER REFERENCES assets(id),
    amount          DECIMAL(10,2) NOT NULL,        -- import en EUR
    day_of_month    INTEGER DEFAULT 2,
    start_date      DATE NOT NULL,
    end_date        DATE,                          -- NULL = indefinit
    is_active       BOOLEAN DEFAULT TRUE,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Aportacions extraordinàries planificades (editables des de UI)
CREATE TABLE extraordinary_contributions (
    id              SERIAL PRIMARY KEY,
    asset_id        INTEGER REFERENCES assets(id),
    planned_date    DATE NOT NULL,
    amount          DECIMAL(10,2) NOT NULL,
    executed        BOOLEAN DEFAULT FALSE,
    executed_date   DATE,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Transaccions (importades de MoneyWiz, immutables)
CREATE TABLE transactions (
    id              SERIAL PRIMARY KEY,
    mw_date         TIMESTAMPTZ NOT NULL,
    asset_id        INTEGER REFERENCES assets(id),
    tx_type         VARCHAR(20) NOT NULL,          -- 'buy', 'sell', 'interest', 'saveback'
    amount_eur      DECIMAL(12,4) NOT NULL,        -- negatiu = compra
    shares          DECIMAL(16,8),                 -- unitats
    price_per_share DECIMAL(12,4),                 -- preu per unitat
    notes           TEXT,
    mw_description  TEXT,                          -- descripció original de MoneyWiz
    import_batch    VARCHAR(50),                   -- identificador de la ingesta
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(mw_date, asset_id, amount_eur, shares)  -- evita duplicats en reimportació
);

-- ═══════════════════════════════════════════════════
-- CAPA 2: CONFIGURACIÓ EDITABLE
-- ═══════════════════════════════════════════════════

-- Escenaris de rendiment (editables des de UI)
CREATE TABLE scenarios (
    id              SERIAL PRIMARY KEY,
    asset_id        INTEGER REFERENCES assets(id),
    scenario_type   VARCHAR(20) NOT NULL,          -- 'adverse', 'base', 'optimistic'
    annual_return   DECIMAL(6,3) NOT NULL,         -- percentatge (7.000 = 7%)
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(asset_id, scenario_type)
);

-- Objectius financers vitals (editables des de UI)
CREATE TABLE objectives (
    id              SERIAL PRIMARY KEY,
    key             VARCHAR(50) UNIQUE NOT NULL,   -- 'home_purchase', 'retirement', etc.
    name            VARCHAR(100) NOT NULL,
    target_amount   DECIMAL(12,2) NOT NULL,
    target_date     DATE,
    current_amount  DECIMAL(12,2) DEFAULT 0,       -- calculat automàticament
    notes           TEXT,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Paràmetres globals del sistema (editables des de UI)
CREATE TABLE parameters (
    key             VARCHAR(100) PRIMARY KEY,
    value           TEXT NOT NULL,
    value_type      VARCHAR(20) NOT NULL,          -- 'decimal', 'integer', 'string', 'boolean', 'date'
    description     TEXT,
    category        VARCHAR(50),                   -- 'portfolio', 'personal', 'simulation'
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Valors inicials de paràmetres
INSERT INTO parameters (key, value, value_type, description, category) VALUES
    ('monthly_savings_cash', '375', 'decimal', 'Estalvi mensual en efectiu (EUR)', 'personal'),
    ('monthly_investment_total', '300', 'decimal', 'Total aportació mensual a inversió (EUR)', 'personal'),
    ('cash_balance', '6600', 'decimal', 'Saldo efectiu actual (EUR)', 'portfolio'),
    ('cash_annual_rate', '2.5', 'decimal', 'Tipus anual compte remunerat (%)', 'portfolio'),
    ('min_cash_percentage', '25', 'decimal', 'Llindar mínim efectiu (% patrimoni)', 'portfolio'),
    ('tax_rate_tier1', '19', 'decimal', 'Tipus impositiu plusvàlues fins 6.000 EUR (%)', 'personal'),
    ('tax_rate_tier2', '21', 'decimal', 'Tipus impositiu plusvàlues 6.000-50.000 EUR (%)', 'personal'),
    ('tax_rate_tier3', '23', 'decimal', 'Tipus impositiu plusvàlues 50.000-200.000 EUR (%)', 'personal'),
    ('tax_rate_tier4', '28', 'decimal', 'Tipus impositiu plusvàlues >200.000 EUR (%)', 'personal');

-- ═══════════════════════════════════════════════════
-- CAPA 3: FINANCES PERSONALS (MoneyWiz)
-- ═══════════════════════════════════════════════════

-- Comptes bancaris (de MoneyWiz)
CREATE TABLE mw_accounts (
    id              SERIAL PRIMARY KEY,
    mw_name         VARCHAR(100) UNIQUE NOT NULL,  -- nom tal com apareix al MoneyWiz
    account_type    VARCHAR(20),                   -- 'checking', 'investment', 'cash', 'savings'
    currency        VARCHAR(5) DEFAULT 'EUR',
    include_in_net_worth BOOLEAN DEFAULT TRUE,
    current_balance DECIMAL(12,2),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Categories de despesa (de MoneyWiz)
CREATE TABLE mw_categories (
    id              SERIAL PRIMARY KEY,
    full_path       VARCHAR(200) UNIQUE NOT NULL,  -- 'Oci ► Bars i Restaurants'
    parent_category VARCHAR(100),                  -- 'Oci'
    child_category  VARCHAR(100),                  -- 'Bars i Restaurants'
    display_name    VARCHAR(100),
    color_hex       VARCHAR(7),
    icon            VARCHAR(50)
);

-- Totes les transaccions de MoneyWiz (finances personals)
CREATE TABLE mw_transactions (
    id              SERIAL PRIMARY KEY,
    mw_date         DATE NOT NULL,
    account_name    VARCHAR(100) NOT NULL,
    amount          DECIMAL(12,2) NOT NULL,
    description     TEXT,
    category_path   VARCHAR(200),
    payee           TEXT,
    notes           TEXT,
    transfer_to     VARCHAR(100),                  -- si és una transferència
    tx_type         VARCHAR(20),                   -- 'expense', 'income', 'transfer', 'investment'
    is_investment   BOOLEAN DEFAULT FALSE,
    import_batch    VARCHAR(50),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(mw_date, account_name, amount, description)
);

-- ═══════════════════════════════════════════════════
-- CAPA 4: SIMULACIONS OBERTES
-- ═══════════════════════════════════════════════════

-- Escenaris de simulació guardats (editables des de UI)
CREATE TABLE simulations (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    description     TEXT,
    is_default      BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Paràmetres específics per a cada simulació
CREATE TABLE simulation_params (
    id              SERIAL PRIMARY KEY,
    simulation_id   INTEGER REFERENCES simulations(id) ON DELETE CASCADE,
    param_key       VARCHAR(100) NOT NULL,         -- 'monthly_income', 'asset_EUNL_return', etc.
    param_value     TEXT NOT NULL,
    param_type      VARCHAR(20) NOT NULL,
    description     TEXT,
    UNIQUE(simulation_id, param_key)
);

-- Resultats cached de simulacions (regenerats automàticament)
CREATE TABLE simulation_results (
    id              SERIAL PRIMARY KEY,
    simulation_id   INTEGER REFERENCES simulations(id) ON DELETE CASCADE,
    horizon_months  INTEGER NOT NULL,
    scenario_type   VARCHAR(20) NOT NULL,
    result_data     JSONB NOT NULL,                -- sèrie temporal completa
    generated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════
-- CAPA 5: NET WORTH HISTÓRIC
-- ═══════════════════════════════════════════════════

-- Snapshot diari del patrimoni total
CREATE TABLE net_worth_snapshots (
    id              SERIAL PRIMARY KEY,
    snapshot_date   DATE UNIQUE NOT NULL,
    total_net_worth DECIMAL(12,2) NOT NULL,
    investments_value DECIMAL(12,2),
    cash_value      DECIMAL(12,2),
    crypto_value    DECIMAL(12,2),
    other_value     DECIMAL(12,2),
    asset_breakdown JSONB,                         -- valor per actiu aquell dia
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════
-- ÍNDEXS PER A RENDIMENT
-- ═══════════════════════════════════════════════════

CREATE INDEX idx_transactions_date ON transactions(mw_date);
CREATE INDEX idx_transactions_asset ON transactions(asset_id);
CREATE INDEX idx_mw_transactions_date ON mw_transactions(mw_date);
CREATE INDEX idx_mw_transactions_category ON mw_transactions(category_path);
CREATE INDEX idx_mw_transactions_account ON mw_transactions(account_name);
CREATE INDEX idx_net_worth_date ON net_worth_snapshots(snapshot_date);
CREATE INDEX idx_simulation_results ON simulation_results(simulation_id, horizon_months);
```

---

## 5. Features V1.0 — WealthPilot Core

### F1.1 — Dashboard principal

Vista d'entrada. Mostra un resum complet del patrimoni en temps real.

**Camps i fonts de dades:**

| Camp | Font | Càlcul |
|---|---|---|
| Patrimoni total | BD + Yahoo Finance | Σ(unitats × preu actual) + efectiu |
| Variació diària | Yahoo Finance | Σ(unitats × variació dia) |
| On Track | BD (simulació base) vs. real | Diferència % respecte projecció del dia |
| Progrés habitatge | BD (objectives) + paràmetres | efectiu_actual / target_amount × 100 |
| Alertes actives | BD (assets.target_weight) vs. real | Desviacions > 5% |

**Regles de negoci:**
- Semàfor verd: patrimoni real ≥ 95% del simulat
- Semàfor groc: entre 85% i 95%
- Semàfor vermell: < 85% o actiu absent amb target_weight > 0

---

### F1.2 — Cartera detallada

Vista completa de totes les posicions.

**Per cada actiu:**
- Valor actual (unitats × preu Yahoo Finance en temps real)
- Unitats acumulades (calculades de transactions)
- Preu mig ponderat de compra (FIFO)
- Capital aportat vs. valor actual
- Guany/pèrdua en EUR i %
- Pes real vs. target_weight (de assets)
- Semàfor de desviació
- Acció suggerida automàtica

**Gràfic donut:** distribució real vs. objectiu, interactiu per segment.

---

### F1.3 — Simulació adaptativa

**Mode A — Projecció futura:**
```
valor_futur(actiu, dies) =
    valor_actual × (1 + annual_return/365)^dies
    + Σ contribucions_mensuals × (1 + annual_return/365)^dies_restants
    + aportacions_extraordinaries_pendents
```

**Mode B — Creixement necessari:**
```
creixement_necessari(actiu) =
    (valor_objectiu - valor_actual - aportacions_futures) / valor_actual × 100
```

**Controls interactius:**
- Slider d'horitzó: 3 mesos – 5 anys (qualsevol punt)
- Selector escenari: Advers / Base / Optimista
- Mode What-If: camp de text lliure per modificar qualsevol paràmetre temporalment
- Visualització: quant és estalvi teu vs. rendiment de mercat

---

### F1.4 — Historial de transaccions

Llegit de la taula `transactions` (importada de MoneyWiz).

**Per transacció:** data, actiu, tipus, import, unitats, preu/unitat.

**Filtres:** per actiu, any/mes, tipus (compra/venda/interès).

**Resum per actiu:** total aportat, unitats, preu mig, rendiment acumulat.

**Apartat fiscal:** vendes realitzades, plusvàlua, impost estimat per trams espanyols.

---

### F1.5 — Sincronització MoneyWiz

**Endpoint `POST /api/upload-backup`:**
1. Rep el .zip de MoneyWiz via iOS Shortcut
2. Extreu el SQLite
3. Processa transaccions d'inversió → taula `transactions`
4. Processa totes les transaccions → taula `mw_transactions`
5. Actualitza `mw_accounts` amb saldos actuals
6. Detecta categories noves → afegeix a `mw_categories`
7. Calcula i guarda snapshot de net worth del dia
8. Elimina el .zip (dades sensibles no persisteixen en brut)

**Idempotència:** La constraint UNIQUE a `transactions` i `mw_transactions` evita duplicats en reimportació.

---

## 6. Features V2.0 — WealthPilot Full

### F2.1 — Edició completa des de la UI

**Principi:** Cap paràmetre requereix editar codi o BD directament.

**Pantalles d'edició (accessibles des de la UI mòbil):**

#### Gestió d'actius
- Afegir nou actiu: nom, ticker MoneyWiz, ticker Yahoo Finance, tipus, color, pes objectiu
- Editar actiu existent: qualsevol camp
- Desactivar actiu (no s'elimina mai, es manté per a l'historial)
- Reordenar per a la visualització

#### Gestió d'aportacions mensuals
- Modificar import d'una aportació existent
- Afegir nova aportació (seleccionar actiu, import, dia del mes, data inici)
- Suspendre/activar aportació temporalment
- Programar data fi d'una aportació

#### Aportacions extraordinàries
- Crear aportació extraordinària (actiu, data, import)
- Marcar com a executada (amb data real)
- Eliminar si no s'ha executat

#### Escenaris de rendiment
- Modificar els tres rendiments (advers/base/optimista) per a qualsevol actiu
- Crear escenari personalitzat (per a simulador obert)

#### Objectius financers
- Editar objectiu habitatge (import, data)
- Afegir nous objectius (per exemple: "fons d'emergència", "cotxe nou")
- Modificar estalvi mensual previst

#### Paràmetres globals
- Saldo efectiu actual
- Tipus d'interès compte remunerat
- Llindar mínim d'efectiu
- Qualsevol variable de la taula `parameters`

**Totes les edicions:** s'executen via API (PUT/PATCH), es validen al backend, i la UI es refresca automàticament.

---

### F2.2 — Simulador obert (What-If avançat)

**Mode 1 — Escenaris guardats:**

L'usuari pot crear escenaris nomenats amb paràmetres personalitzats:

```
Escenari: "Canvi de feina + 500€/mes"
  - Ingressos mensuals: +500 €
  - Aportació mensual inversió: +200 €
  - Estalvi mensual efectiu: +300 €
  - Data efecte: 01/09/2026
  - Horitzó: 5 anys
```

```
Escenari: "Compra pis 2029"
  - Retirada efectiu: -35.000 €
  - Desapareix objectiu habitatge
  - Nova despesa mensual: +400 € (hipoteca)
  - Data: 01/04/2029
```

Els escenaris es guarden a `simulations` + `simulation_params` i es poden comparar visualment entre ells.

**Mode 2 — Simulador interactiu en temps real:**

Panell de controls on l'usuari pot modificar qualsevol paràmetre i veure l'efecte instantani al gràfic:

| Paràmetre ajustable | Rang |
|---|---|
| Ingressos mensuals | ±5.000 €/mes |
| Aportació mensual total | 0 – 2.000 €/mes |
| Rendiment de qualsevol actiu | -50% – +100% anual |
| Data d'un event (compra pis, etc.) | qualsevol data futura |
| Import d'un event | qualsevol import |

El simulador mai modifica la BD. Opera sobre una còpia en memòria dels paràmetres actuals.

---

### F2.3 — Analítica de finances personals

Tres mòduls d'analítica basats en `mw_transactions`:

#### Mòdul A — Despeses per categoria

**Vista mensual:**
- Top 10 categories per import gastat
- Comparació amb el mes anterior
- Tendència dels últims 6 mesos per categoria
- Gràfic de barres apilades per categoria × mes

**Categories principals identificades en les dades actuals:**
- Casa (lloguer, súper, mobles, farmàcia)
- Oci (bars, restaurants, teatre, cine)
- Vehicles (gasolina, taller, assegurança, peatges)
- Esport (Batec, equipament)
- Regals
- Electrònica (software, hardware)
- Viatges
- Roba i sabates

#### Mòdul B — Net worth total mes a mes

**Evolució temporal:**
- Gràfic de línies: net worth total per mes (de `net_worth_snapshots`)
- Desglos: inversions / efectiu / cripto
- Comparació amb la projecció simulada
- Ràtio estalvi/ingressos per mes

**Fonts:**
- Net worth diari: calculat en cada importació de backup
- Ingressos: transaccions de categoria 'Nòmina'
- Despeses: totes les transaccions negatives no-inversió

#### Mòdul C — Estalvi real vs. planificat

**Comparativa mensual:**
- Estalvi planificat: `monthly_savings_cash` (paràmetre BD)
- Estalvi real: ingressos − despeses − inversions del mes
- Desviació: diferència i % sobre el planificat
- Tendència: últims 12 mesos

**Alertes automàtiques:**
- Si l'estalvi real d'un mes és < 80% del planificat → alerta al dashboard
- Si les despeses d'una categoria superen la mitjana dels últims 3 mesos en > 30% → alerta

---

### F2.4 — Comparació d'escenaris

Pantalla dedicada per comparar fins a 3 escenaris simultàniament:

```
[Escenari actual]  vs.  [Canvi feina]  vs.  [Compra pis 2029]

Horitzó: 5 anys

          Actual    Canvi feina    Compra pis
12 mesos  €32.173   €34.800        €31.500
24 mesos  €43.157   €48.200        €42.000
36 mesos  €55.000   €62.000        €54.000 (−35k pis)
60 mesos  €82.000   €95.000        €78.000

Net worth màxim a 5 anys: Canvi feina +15,9% vs. actual
```

Gràfic de línies amb les tres projeccions superposades, seleccionables/desactivables.

---

## 7. Mockups visuals

> Vegeu fitxer adjunt `WealthPilot_Mockups.html` per als mockups interactius renderitzats de les pantalles V1.0.

Les pantalles V2.0 seguiran el mateix sistema de disseny. A continuació, l'estructura de les pantalles noves:

### Mapa de navegació complet

```
V1.0 — Pestanya inferior principal:
┌─────────────────────────────────────┐
│  🏠 Inici  │ 📊 Cartera │ 📈 Sim  │
│  📋 Historial         │  ⚙️ Config │
└─────────────────────────────────────┘

V2.0 — Afegeix pestanya Analítica:
┌─────────────────────────────────────┐
│  🏠 Inici  │ 📊 Cartera │ 📈 Sim  │
│  📋 Historial │ 📉 Analítica │ ⚙️  │
└─────────────────────────────────────┘

Config expandida amb sub-seccions:
  ├── Actius i pesos
  ├── Aportacions mensuals
  ├── Aportacions extraordinàries
  ├── Escenaris de rendiment
  ├── Objectius financers
  ├── Paràmetres globals
  └── Sincronització
```

---

## 8. Stack tecnològic

### Resum de decisions

| Component | Tecnologia | Versió | Justificació |
|---|---|---|---|
| BD | PostgreSQL | 15 | Robust, escala, JSON natiu, estàndard |
| Backend | FastAPI + Python | 3.11+ | Async, validació automàtica, documentació |
| ORM | SQLAlchemy + Alembic | 2.0 | Migracions de BD versioned |
| Frontend | HTML/CSS/JS vanilla | — | Sense overhead de framework, fàcil mantenir |
| Gràfics | Chart.js | 4.x | Lleuger, suficient per als casos d'ús |
| Servidor web | Nginx | latest | Reverse proxy + static files |
| HTTPS | Let's Encrypt + Certbot | — | Gratuït, renovació automàtica |
| Desplegament | Systemd | — | Process manager natiu d'Ubuntu |
| App mòbil | PWA (V1) + Capacitor (V2) | — | Reutilitza codi web, instal·lació sense App Store |
| Sincronització | iOS Shortcuts | — | Natiu iOS, sense dependències externes |
| Preus mercat | Yahoo Finance API yfinance | 0.2.x | Gratuït, no oficial però estable |

### Sobre Alembic (migracions)

Alembic és el sistema de migracions de BD per a SQLAlchemy. Permet evolucionar l'esquema de la BD amb versions controlades. Quan s'afegeixi una nova taula o columna a futur, es crea una migració que s'aplica sense perdre dades. **Crític per a un projecte que creixerà.**

```bash
# Exemple de workflow
alembic revision --autogenerate -m "afegir columna notes a assets"
alembic upgrade head
```

### Seguretat

- Tot tràfic via HTTPS (Let's Encrypt)
- `POST /api/upload-backup` protegit amb Bearer token (generat en setup inicial)
- El .zip de MoneyWiz s'elimina immediatament després del processament
- PostgreSQL: accés únicament des de localhost (no exposat a internet)
- Variables sensibles en `.env` (mai al repositori)
- SSH accés únicament per clau pública

---

## 9. Estructura del projecte

```
wealthpilot/
│
├── backend/
│   ├── main.py                     # FastAPI app, middleware, CORS
│   ├── config.py                   # Settings (pydantic-settings, .env)
│   ├── database.py                 # Connexió PostgreSQL, session factory
│   ├── requirements.txt
│   │
│   ├── alembic/                    # Migracions de BD
│   │   ├── env.py
│   │   ├── versions/
│   │   │   └── 001_initial_schema.py
│   │   └── alembic.ini
│   │
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── portfolio.py            # Asset, Contribution, Transaction, etc.
│   │   ├── config.py               # Scenario, Objective, Parameter
│   │   ├── personal.py             # MwAccount, MwTransaction, MwCategory
│   │   ├── simulation.py           # Simulation, SimulationParam, SimulationResult
│   │   └── networth.py             # NetWorthSnapshot
│   │
│   ├── schemas/                    # Pydantic schemas (request/response)
│   │   ├── __init__.py
│   │   ├── portfolio.py
│   │   ├── simulation.py
│   │   ├── analytics.py
│   │   └── config.py
│   │
│   ├── api/                        # Routers FastAPI
│   │   ├── __init__.py
│   │   ├── portfolio.py            # GET /portfolio, GET /positions
│   │   ├── simulation.py           # GET /simulation, POST/PUT/DELETE /scenarios
│   │   ├── history.py              # GET /history, GET /fiscal
│   │   ├── analytics.py            # GET /analytics/expenses, /networth, /savings
│   │   ├── config.py               # CRUD /assets, /contributions, /parameters
│   │   └── upload.py               # POST /upload-backup
│   │
│   └── services/
│       ├── __init__.py
│       ├── moneywiz_parser.py      # Processament SQLite MoneyWiz
│       ├── yahoo_finance.py        # Preus en temps real
│       ├── portfolio_calculator.py # Càlculs de posicions, preu mig, rendiment
│       ├── simulation_engine.py    # Motor de simulació (Mode A i B)
│       ├── analytics_engine.py     # Càlculs analítica finances personals
│       └── tax_calculator.py       # Càlcul plusvàlues i impost ESP
│
├── frontend/
│   ├── index.html                  # Punt d'entrada, estructura base
│   ├── manifest.json               # PWA manifest
│   ├── service-worker.js           # Cache offline
│   │
│   ├── css/
│   │   ├── variables.css           # Design tokens (colors, fonts, spacing)
│   │   ├── base.css                # Globals, reset, tipografia
│   │   ├── components.css          # Components reutilitzables
│   │   └── pages.css               # Estils específics per pantalla
│   │
│   └── js/
│       ├── app.js                  # Router, inicialització, state global
│       ├── api.js                  # Client API (fetch wrappers, error handling)
│       │
│       ├── pages/
│       │   ├── dashboard.js
│       │   ├── portfolio.js
│       │   ├── simulation.js       # Inclou simulador obert V2.0
│       │   ├── history.js
│       │   ├── analytics.js        # V2.0: despeses, net worth, estalvi
│       │   └── settings/
│       │       ├── index.js        # Pàgina principal config
│       │       ├── assets.js       # Gestió actius
│       │       ├── contributions.js# Gestió aportacions
│       │       ├── scenarios.js    # Gestió escenaris
│       │       ├── objectives.js   # Gestió objectius
│       │       └── parameters.js   # Paràmetres globals
│       │
│       └── components/
│           ├── nav.js              # Navegació inferior
│           ├── charts.js           # Wrappers Chart.js
│           ├── modal.js            # Modal d'edició genèric
│           ├── form.js             # Components de formulari
│           └── semaphore.js        # Semàfors visual
│
├── deployment/
│   ├── nginx.conf                  # Configuració Nginx (reverse proxy + static)
│   ├── wealthpilot.service         # Systemd service
│   ├── setup.sh                    # Instal·lació inicial servidor (PostgreSQL, deps)
│   └── deploy.sh                   # Deploy d'actualitzacions
│
├── docs/
│   ├── ios-shortcut.md             # Instruccions Shortcut iOS pas a pas
│   └── database-schema.md          # Documentació de l'esquema BD
│
├── .env.example                    # Template variables d'entorn
├── .gitignore                      # Inclou .env, backend/uploads/, etc.
└── README.md
```

### Fitxers mai al repositori (`.gitignore`)

```
.env
backend/uploads/         # Backups temporals de MoneyWiz
backend/data/            # Cache JSON
*.sqlite                 # SQLite temporals
__pycache__/
node_modules/
```

---

## 10. Planning de desenvolupament

### Visió general

```
V1.0 ──────────────────────────────── V2.0
│                                     │
S0   S1   S2   S3   S4              S5   S6   S7   S8
Setup Core Sim  PWA  Polish         Edit Anlyt SimObert Final
│                    │                              │
└── Producte        └── V1.0 live                  └── V2.0 live
    funcional           i desplegat                    complet
```

---

### Sessió 0 — Infraestructura i base de dades (prerequisit)
**Durada estimada:** 2-3 hores

**Prerequisit obligatori:**
- Executar diagnòstic del servidor (Apèndix A) i compartir output
- Verificar que ports 80 i 443 estan oberts al firewall d'Oracle

**Tasques:**
- [ ] Diagnòstic servidor: serveis actuals, ports, recursos
- [ ] Instal·lar PostgreSQL 15 al servidor Oracle
- [ ] Instal·lar Python 3.11+, pip, nginx, certbot, git
- [ ] Crear base de dades `wealthpilot` i usuari dedicat
- [ ] Executar schema SQL complet (Secció 4)
- [ ] Inserir dades inicials: actius, escenaris, paràmetres, objectius
- [ ] Importar historial complet de transaccions del SQLite de MoneyWiz
- [ ] Crear repositori Git privat
- [ ] Configurar estructura de directoris al servidor
- [ ] Generar Bearer token per a l'API
- [ ] Crear fitxer `.env` al servidor

**Resultat:** Servidor preparat amb BD poblada i repositori creat.

---

### Sessió 1 — Backend core + Dashboard
**Durada estimada:** 3 hores

**Tasques:**
- [ ] Estructura FastAPI: main.py, config.py, database.py
- [ ] Models SQLAlchemy per a totes les taules
- [ ] Schemas Pydantic per a respostes API
- [ ] Servei `yahoo_finance.py`: preus actuals per ticker
- [ ] Servei `portfolio_calculator.py`: unitats, preu mig FIFO, rendiment
- [ ] Endpoint `GET /api/portfolio`: posicions completes amb preus reals
- [ ] Endpoint `POST /api/upload-backup`: ingesta MoneyWiz
- [ ] Web app base: estructura HTML, router JS, sistema de components
- [ ] Pantalla Dashboard: tots els camps amb dades reals de la BD
- [ ] Desplegament inicial al servidor + nginx + systemd

**Resultat:** Dashboard funcionant amb dades reals al servidor Oracle.

---

### Sessió 2 — Cartera + Simulació
**Durada estimada:** 3 hores

**Tasques:**
- [ ] Servei `simulation_engine.py`: Mode A (projecció) i Mode B (creixement necessari)
- [ ] Endpoint `GET /api/simulation`: paràmetres d'horitzó i escenari des de BD
- [ ] Pantalla Cartera: llista actius, semàfors, donut interactiu
- [ ] Pantalla Simulació: slider d'horitzó, selector escenaris, gràfic de línies, what-if bàsic
- [ ] Visualització "tu aportes X vs. mercat aporta Y"
- [ ] Tests de la lògica de simulació

**Resultat:** Cartera i simulació totalment funcionals i interactives.

---

### Sessió 3 — Historial + PWA + Polish
**Durada estimada:** 2-3 hores

**Tasques:**
- [ ] Servei `tax_calculator.py`: plusvàlues i impost espanyol per trams
- [ ] Endpoint `GET /api/history`: amb filtres per actiu, any, tipus
- [ ] Pantalla Historial: llista transaccions, filtres, resum per actiu, apartat fiscal
- [ ] Pantalla Configuració V1.0: estat connexions, sincronització
- [ ] HTTPS amb Let's Encrypt (certbot)
- [ ] PWA: manifest.json, service-worker.js, icones
- [ ] Responsive design iPhone + iPad
- [ ] Provar instal·lació PWA a iPhone i iPad
- [ ] iOS Shortcut: crear, documentar, provar flux complet

**Resultat:** V1.0 completa, instal·lable com a PWA, amb HTTPS. **V1.0 LIVE.**

---

### Sessió 4 — Edició completa des de UI (V2.0 inici)
**Durada estimada:** 3 hores

**Tasques:**
- [ ] Endpoints CRUD complets: assets, contributions, extraordinary, scenarios, objectives, parameters
- [ ] Component `modal.js`: modal genèric d'edició reutilitzable
- [ ] Component `form.js`: inputs validats, tipats, amb feedback d'error
- [ ] Pantalla Settings > Actius: llista + afegir + editar + desactivar
- [ ] Pantalla Settings > Aportacions: llista + modificar + afegir + suspendre
- [ ] Pantalla Settings > Aportacions extraordinàries: CRUD complet
- [ ] Pantalla Settings > Escenaris de rendiment: editar els tres tipus per actiu
- [ ] Pantalla Settings > Objectius: editar habitatge + afegir nous
- [ ] Pantalla Settings > Paràmetres globals: tots els camps editables
- [ ] Validació: la suma de target_weight ha de ser 100%

**Resultat:** Qualsevol paràmetre editable des de la UI mòbil.

---

### Sessió 5 — Analítica de finances personals (V2.0)
**Durada estimada:** 3 hores

**Tasques:**
- [ ] Servei `analytics_engine.py`: processament `mw_transactions`
- [ ] Endpoint `GET /api/analytics/expenses`: despeses per categoria × mes
- [ ] Endpoint `GET /api/analytics/networth`: evolució net worth mensual
- [ ] Endpoint `GET /api/analytics/savings`: estalvi real vs. planificat
- [ ] Pantalla Analítica > Despeses: top categories, gràfic barres apilades, filtres
- [ ] Pantalla Analítica > Net Worth: gràfic evolució mensual, desglos per tipus
- [ ] Pantalla Analítica > Estalvi: comparativa real vs. planificat, últims 12 mesos
- [ ] Alertes automàtiques: categoria > +30% de la mitjana → alerta al dashboard

**Resultat:** Analítica completa de finances personals activa.

---

### Sessió 6 — Simulador obert i comparació d'escenaris (V2.0)
**Durada estimada:** 3 hores

**Tasques:**
- [ ] Endpoint CRUD `/api/scenarios/custom`: escenaris guardats amb params
- [ ] Mode 1: pantalla "Nou escenari" amb tots els paràmetres editables
- [ ] Mode 2: simulador interactiu en temps real (sliders múltiples)
- [ ] Pantalla comparació d'escenaris: fins a 3 simultàniament
- [ ] Cache de resultats a `simulation_results` per a rendiment
- [ ] Invalidació de cache quan canvien paràmetres

**Resultat:** Simulador obert complet. **V2.0 LIVE.**

---

### Sessió 7 (opcional) — Capacitor iOS App
**Durada estimada:** 2 hores  
**Prerequisit:** Mac amb Xcode instal·lat

**Tasques:**
- [ ] Instal·lar Capacitor al frontend
- [ ] Configurar projecte iOS amb Xcode
- [ ] Icones natives i splash screen
- [ ] Build i instal·lació al dispositiu via Xcode
- [ ] Verificar comportament vs. PWA

**Resultat:** App instal·lada com a app nativa sense App Store.

---

### Resum de sessions

| Sessió | Focus | Durada | Versió | Resultat |
|---|---|---|---|---|
| 0 | Infraestructura + BD | 2-3h | Pre | Servidor + BD preparats |
| 1 | Backend + Dashboard | 3h | V1.0 | Dades reals al browser |
| 2 | Cartera + Simulació | 3h | V1.0 | Core analítica inversió |
| 3 | Historial + PWA | 2-3h | V1.0 | **V1.0 LIVE** |
| 4 | Edició UI completa | 3h | V2.0 | Tot editable sense codi |
| 5 | Analítica personal | 3h | V2.0 | MoneyWiz analytics |
| 6 | Simulador obert | 3h | V2.0 | **V2.0 LIVE** |
| 7* | Capacitor iOS | 2h | V2.0 | App nativa (opcional) |

**Total estimat:** 21-23 hores de desenvolupament actiu.

---

## 11. Apèndixs

### Apèndix A — Diagnòstic servidor Oracle (ACCIÓ REQUERIDA)

Abans de la Sessió 0, l'usuari ha de connectar-se via SSH i executar:

```bash
# 1. Serveis en funcionament
systemctl list-units --type=service --state=running

# 2. Ports oberts
ss -tlnp

# 3. Logs recents (identificar el "codi recurrent")
sudo journalctl -n 50 --no-pager

# 4. Recursos disponibles
free -h && df -h /

# 5. Python disponible
python3 --version && pip3 --version

# 6. PostgreSQL ja instal·lat?
psql --version 2>/dev/null || echo "PostgreSQL no instal·lat"
```

L'output d'aquestes comandes determina el punt de partida exacte de la Sessió 0.

---

### Apèndix B — Dades de seeding inicial

Valors a inserir a la BD en la Sessió 0:

**Taula `assets`:**

| ticker_mw | ticker_yf | name | type | target_weight |
|---|---|---|---|---|
| EUNL | IWDA.AS | MSCI World | etf | 22.00 |
| PPFB | PHAU.L | Or físic ETC | commodity | 12.00 |
| EUNK | IMAE.MI | MSCI Europe | etf | 10.00 |
| IS3N | IS3N.AS | MSCI EM IMI | etf | 5.00 |
| CSJP | CSJP.AS | MSCI Japan | etf | 6.00 |
| WDEF | WDEF.MI | Europe Defence | etf | 5.00 |
| BTC | BTC-EUR | Bitcoin | crypto | 2.00 |

**Taula `objectives`:**

| key | name | target_amount | target_date |
|---|---|---|---|
| home_purchase | Compra habitatge | 40000.00 | 2029-04-01 |

**Historial de transaccions (de l'Apèndix D del PRD anterior):**
64 transaccions entre abril 2025 i març 2026. Vegeu fitxer `seed_transactions.sql` (generat a la Sessió 0 des del SQLite de MoneyWiz).

---

### Apèndix C — Mapa de tickers

| Actiu | Ticker MoneyWiz | Ticker Yahoo Finance | Borsa |
|---|---|---|---|
| MSCI World | EUNL | IWDA.AS | Euronext Amsterdam |
| Or físic | PPFB | PHAU.L | London Stock Exchange |
| MSCI Europe | EUNK | IMAE.MI | Borsa Italiana |
| MSCI EM IMI | IS3N | IS3N.AS | Euronext Amsterdam |
| Bitcoin | BTC | BTC-EUR | Crypto EUR |
| Japó | CSJP | CSJP.AS | Euronext Amsterdam |
| Defensa Europa | WDEF | WDEF.MI | Borsa Italiana |

---

### Apèndix D — Estructura SQLite de MoneyWiz

Taula principal: `ZSYNCOBJECT`. Camps rellevants per a la ingesta:

| Camp | Tipus | Descripció | Conversió |
|---|---|---|---|
| `ZDATE1` | FLOAT | Timestamp Apple (seg. des de 01/01/2001) | + 978307200 → Unix timestamp |
| `ZDESC2` | VARCHAR | Descripció transacció | Mapejat a asset per ticker |
| `ZAMOUNT1` | FLOAT | Import EUR (negatiu = compra) | Directe |
| `ZNUMBEROFSHARES` | FLOAT | Unitats comprades | Directe |
| `ZPRICEPERSHARE1` | FLOAT | Preu per unitat al moment | Directe |
| `ZSYMBOL1` | VARCHAR | Ticker intern MoneyWiz | Mapejat a `assets.ticker_mw` |

**Query de transaccions d'inversió:**
```sql
SELECT ZDATE1, ZDESC2, ZAMOUNT1, ZNUMBEROFSHARES, ZPRICEPERSHARE1, ZSYMBOL1
FROM ZSYNCOBJECT
WHERE ZNUMBEROFSHARES > 0
ORDER BY ZDATE1 ASC
```

**Query de totes les transaccions personals:**
```sql
SELECT ZDATE1, ZDESC2, ZAMOUNT1, ZNAME_ACCOUNT, ZCATEGORY_PATH
FROM ZSYNCOBJECT
WHERE ZAMOUNT1 IS NOT NULL AND ZNUMBEROFSHARES = 0
ORDER BY ZDATE1 DESC
```

---

### Apèndix E — Variables d'entorn (.env)

```bash
# Base de dades
DATABASE_URL=postgresql://wealthpilot:PASSWORD@localhost:5432/wealthpilot

# Autenticació API
API_BEARER_TOKEN=GENERAR_TOKEN_ALEATORI_32_CHARS

# Configuració FastAPI
DEBUG=false
ALLOWED_ORIGINS=https://DOMINI_O_IP

# Paths
UPLOAD_DIR=/tmp/wealthpilot_uploads
```

---

*Document v2.0 — 23 març 2026. Actualitzar la secció "Arquitectura global" un cop completat el diagnòstic del servidor (Apèndix A).*
