# Mòdul Market — Yahoo Finance i Historial de Preus

> Última actualització: Març 2026

---

## Responsabilitat del Mòdul

El mòdul `market` és responsable de:

1. **Descarregar preus** des de Yahoo Finance i guardar-los a la BD (font de veritat)
2. **Servir preus actuals** a la resta de l'app (amb cache en memòria, 5 min TTL)
3. **Detectar preus obsolets** (stale) i informar-ne a la UI
4. **Historial OHLCV** per a gràfics i càlculs de rendiment

**Principi fonamental: la BD és la font de veritat. Yahoo Finance és només el proveïdor.**
Un cop descarregats, els preus no es tornen a tocar fins que n'hi hagi de nous. Si Yahoo cau, la app continua funcionant amb l'últim preu guardat i el flag `is_stale = True`.

---

## Estructura de Fitxers

```
backend/modules/market/
├── __init__.py
├── models.py    4 taules: MarketIndex, MarketIndexData, ExchangeRate, PriceFetchLog
├── schemas.py   5 schemas Pydantic: AssetPriceOut, MarketPricesResponse,
│                GapFillResponse, PriceHistoryPoint, AssetPriceHistoryResponse
├── service.py   Tota la lògica: gap fill, cache, window function query
└── router.py    4 endpoints REST
```

Els preus dels assets es guarden a `price_history` (mòdul `portfolio`). El mòdul `market` escriu i llegeix aquesta taula però no en posseeix el model.

---

## Taules de BD

### `price_history` (mòdul portfolio, escrita pel market)
| Columna | Tipus | Notes |
|---------|-------|-------|
| `asset_id` | FK → assets | |
| `price_date` | DATE | Constraint únic amb asset_id |
| `price_close` | NUMERIC(12,4) | Obligatori |
| `price_open/high/low` | NUMERIC(12,4) | Opcional |
| `volume` | NUMERIC(20,0) | Opcional |
| `currency` | VARCHAR(5) | Llegit de l'asset |

Constraint: `UNIQUE(asset_id, price_date)` → permet `ON CONFLICT DO NOTHING` (idempotència).

### `price_fetch_logs` (mòdul market)
Registra cada operació de descàrrega: ticker, status (success/failed/rate_limited), preu retornat, missatge d'error, temps de resposta. Útil per a depuració i monitoratge de rate limits.

---

## Gap Fill — Estratègia

El gap fill es llança en dos moments:
1. **Arrencada del servidor** (lifespan de FastAPI) — posa la BD al dia automàticament
2. **`POST /api/v1/market/refresh`** — trucada manual des de la UI o scripts

### Algoritme (`fill_all_gaps`)

```
1. Assets actius amb ticker_yf → llista de tickers
2. SELECT MAX(price_date) per asset en UNA sola query
3. inception_date des de parameters.key='portfolio_inception_date' (default: 2020-01-01)
4. Per cada asset:
   - Si MAX(price_date) = NULL → start = inception_date
   - Sinó              → start = MAX(price_date) + 1 dia
   - Si start > avui   → skip (ja tenim tot)
5. Agrupar tickers per start_date → batches
6. Per cada batch: yf.download(tickers, start, end) via asyncio.to_thread()
7. Si batch falla → reintent individual amb exponential backoff (max 3 intents)
8. INSERT INTO price_history ... ON CONFLICT (asset_id, price_date) DO NOTHING
9. Commit per ticker (fallo d'un asset no perd els altres)
10. Log a price_fetch_logs
11. Invalidar cache en memòria
```

### Recuperació d'Outages

Si Yahoo cau durant X dies, quan torna:
- Un sol `fill_all_gaps` descarrega TOT el rang que falta per a cada asset en un batch
- Ràpid gràcies al batch download (una sola crida HTTP per grup de tickers)
- Idempotent: si es crida múltiples cops, no hi ha duplicats

---

## Cache en Memòria

`get_current_prices` usa una cache a nivell de mòdul (variable global + `asyncio.Lock`):

```python
@dataclass
class _PriceCache:
    prices: list[AssetPriceOut]
    fetched_at: float   # time.monotonic()
    ttl_seconds: int = 300  # 5 minuts
```

- La primera crida (o quan la cache caduca) fa la query a la BD
- Les crides següents retornen la cache → `cached: True` a la resposta
- El gap fill invalida la cache (`fetched_at = 0`) perquè la propera crida agafi preus nous

**Per què 5 minuts?** Els preus de Yahoo Finance s'actualitzen cada 15 min en mercat obert. 5 minuts és un bon compromís entre frescor i reducció de queries a la BD.

---

## Detecció de Preus Obsolets (Stale)

| Tipus d'asset | Threshold |
|---------------|-----------|
| ETF, acció, commodity | 3 dies calendari |
| Crypto | 1 dia calendari |

El crypto opera 24/7, per tant 1 dia és suficient. Per ETFs, el threshold de 3 dies cobreix cap de setmana (Dis+Diu) + 1 dia de festiu.

`is_stale: true` no impedeix servir el preu — sempre es retorna l'últim preu conegut. La UI pot mostrar un indicador visual (badge groc/taronja) i el nombre de dies (`stale_days`).

---

## Query de Preus Actuals (Window Function)

Per obtenir l'últim preu i el canvi diari en una sola query SQL:

```sql
WITH ranked AS (
    SELECT ph.*, a.display_name, a.ticker_yf, a.asset_type, a.currency,
           ROW_NUMBER() OVER (PARTITION BY ph.asset_id ORDER BY ph.price_date DESC) AS rn
    FROM price_history ph JOIN assets a ON a.id = ph.asset_id
    WHERE a.is_active = TRUE
),
latest AS (SELECT * FROM ranked WHERE rn = 1),
prev   AS (SELECT asset_id, price_close AS prev_close FROM ranked WHERE rn = 2)
SELECT l.*, p.prev_close
FROM latest l LEFT JOIN prev p ON p.asset_id = l.asset_id
```

Això retorna les 2 darreres files per asset (per calcular el `change_pct_1d`) sense subconsultes ni múltiples queries.

---

## Descàrrega via yfinance

S'usa la llibreria `yfinance==1.2.0` (sync), cridada via `asyncio.to_thread()` per no bloquejar l'event loop.

> **Nota de versió:** yfinance >= 1.0 **sempre** retorna MultiIndex columns `(Price, Ticker)` fins i tot per descàrregues d'un sol ticker. `_extract_ohlcv_single` detecta MultiIndex primer i delega a `_extract_ohlcv_multi`.

### Batch vs Single

```python
# Batch (preferit): una crida HTTP per a N tickers amb el mateix start_date
df = yf.download(["IWDA.AS", "BTC-EUR"], start="2020-01-01", end="2026-03-28",
                 auto_adjust=True, progress=False, threads=True)
# → DataFrame amb MultiIndex columns: ('Close', 'IWDA.AS'), ('Open', 'IWDA.AS'), ...

# Single (fallback si batch falla): amb retry exponential
df = yf.download("IWDA.AS", start="...", end="...", auto_adjust=True, progress=False)
# → yfinance 1.x: MultiIndex columns: ('Close', 'IWDA.AS'), ('Open', 'IWDA.AS'), ...
```

`auto_adjust=True` ajusta els preus per splits i dividends automàticament.

### Gestió del MultiIndex

yfinance >= 1.0 retorna **sempre** MultiIndex `(Price, Ticker)` per a tots els casos. El servei gestiona tant el format nou (`_extract_ohlcv_single` → `_extract_ohlcv_multi`) com el format pla legacy (versió < 1.0).

---

## Insert Idempotent (Bulk)

Per inserir milers de files de manera eficient i segura:

```python
INSERT INTO price_history (asset_id, price_date, price_close, ...)
VALUES (:ai0,:pd0,:pc0,...), (:ai1,:pd1,:pc1,...), ...   -- fins 500 files per batch
ON CONFLICT (asset_id, price_date) DO NOTHING
```

- Màxim 500 files per VALUES clause (evita el límit de paràmetres de PostgreSQL)
- `ON CONFLICT DO NOTHING` → idempotent: pujar el mateix rang 2 vegades = 0 duplicats
- Commit per ticker → si falla un asset, els anteriors queden guardats

---

## Schemas Pydantic

| Schema | Ús |
|--------|----|
| `AssetPriceOut` | Un preu actual + metadades (stale, canvi 1d) |
| `MarketPricesResponse` | Llista de tots els preus + estadístiques (fresh/stale/no_data) |
| `GapFillResponse` | Resultat del gap fill: files inserides, assets actualitzats/fallats, durada |
| `PriceHistoryPoint` | Una fila de l'historial OHLCV |
| `AssetPriceHistoryResponse` | Historial complet d'un asset (envolcall de la llista) |

---

## Endpoints

| Mètode | Ruta | Descripció |
|--------|------|-----------|
| `GET` | `/api/v1/market/prices` | Preus actuals (tots els assets actius, amb cache) |
| `GET` | `/api/v1/market/prices/{asset_id}` | Preu actual d'un asset concret |
| `POST` | `/api/v1/market/refresh` | Gap fill manual (descarrega tot el que falta) |
| `GET` | `/api/v1/market/history/{asset_id}?days=30` | Historial OHLCV (1–3650 dies) |

Exemple de resposta `GET /api/v1/market/prices`:
```json
{
  "prices": [
    {
      "asset_id": 1,
      "display_name": "MSCI World",
      "ticker_yf": "IWDA.AS",
      "asset_type": "etf",
      "price_close": "107.4200",
      "price_date": "2026-03-26",
      "currency": "EUR",
      "is_stale": false,
      "stale_days": 1,
      "change_pct_1d": "0.3200",
      "change_eur_1d": "0.3400"
    }
  ],
  "total_assets": 8,
  "fresh_count": 7,
  "stale_count": 0,
  "no_data_count": 1,
  "cached": true,
  "cache_age_seconds": 42
}
```

---

## Decisions de Disseny

**Per què no cridar Yahoo directament des de la UI?**
La UI mai accedeix directament a Yahoo. Tota la lògica va a la BD primer. Avantatges:
- Sense rate limits al frontend
- Dades consistents: tota l'app veu els mateixos preus
- Historial persistent: fins i tot si Yahoo canvia l'API o tanca, tenim les dades
- Càlculs (P&L, rebalanceig) sempre basats en dades locals

**Per què asyncio.to_thread?**
`yfinance` és una llibreria síncrona (usa `requests` internament). Cridar-la directament bloquejarien el thread de FastAPI. `asyncio.to_thread()` la mou a un thread pool, mantenint l'app responsive.

**Per què NullPool als tests?**
pytest-asyncio crea un event loop nou per cada test. Les connexions asyncpg queden lligades al loop del test anterior. NullPool desactiva la reutilització de connexions, eliminant el problema sense tocar cap codi de producció.
