# 09 — Mòdul Net Worth (Snapshots)

## Visió general

El mòdul `networth` genera i manté instantànies diàries del patrimoni net. Actua com a agregador de dues fonts:

- **Total**: `mw_accounts.current_balance` (font de veritat — el que MoneyWiz mostra)
- **Desglossat per asset**: `shares acumulades × preu de Yahoo Finance` (informatiu — pot diferir si hi ha actius no mapejats com NUKL)

### Fitxers

```
backend/
  modules/networth/
    __init__.py
    models.py      ← 3 taules ORM: NetWorthSnapshot, AssetSnapshot, NetWorthMilestone
    schemas.py     ← Pydantic: AssetSnapshotOut, NetWorthSnapshotOut, NetWorthHistoryResponse, GenerateSnapshotResponse
    service.py     ← generate_snapshot(), get_history()
    router.py      ← 2 endpoints REST
  scripts/
    net_worth.py   ← script CLI: make net-worth
  tests/
    test_networth.py ← suite de tests (schema + API + servei)
```

---

## Estratègia de càlcul

```
total_net_worth = cash_value + inv_value - liab_value

  cash_value  = SUM(current_balance) WHERE account_type IN (checking, savings, cash, forex)
  inv_value   = SUM(current_balance) WHERE account_type IN (investment)
  liab_value  = SUM(current_balance) WHERE account_type IN (credit, loan)

  Filtre: is_active = TRUE AND include_in_networth = TRUE
```

Per al desglossat per asset:

```
value_eur = total_shares × last_price_eur

  total_shares = SUM(shares) per investment_buy − SUM(shares) per investment_sell
  last_price   = última entrada a price_history per asset, ON O BEFORE snapshot_date
  cost_basis   = SUM(amount_eur) per investment_buy
  pnl_eur      = value_eur − cost_basis
```

El join que connecta les dues fonts:

```sql
JOIN assets a ON a.ticker_mw = mt.mw_symbol
```

On `ticker_mw` és el símbol intern de MoneyWiz (e.g. `EUNL`, `PHAU`, `BTC`) i `mw_symbol` és el camp extret de `ZSYMBOL1` al parser.

---

## Idempotència

El snapshot és **idempotent per data**:

- `net_worth_snapshots`: `ON CONFLICT (snapshot_date) DO UPDATE` (constraint `uq_networth_date`)
- `asset_snapshots`: `DELETE WHERE snapshot_id = :sid` + `INSERT` (re-insert net, no duplicats)

Cridar `POST /api/v1/networth/snapshot?snapshot_date=2025-01-01` N vegades produeix exactament el mateix resultat.

---

## Flux post-sync

Quan `sync.service.process_upload()` completa amb èxit, crida automàticament:

```python
await networth_service.generate_snapshot(db, trigger_source="sync")
```

L'error del snapshot és **non-fatal**: si falla, el sync continua i l'error s'enregistra al log.

---

## API

### `POST /api/v1/networth/snapshot`

Genera (o actualitza) el snapshot per a una data.

| Paràmetre | Tipus | Default | Descripció |
|-----------|-------|---------|------------|
| `snapshot_date` | `date` (query) | avui | Data del snapshot |

**Resposta 201:**
```json
{
  "snapshot_date": "2025-03-28",
  "total_net_worth": "125430.50",
  "investment_portfolio_value": "89200.00",
  "cash_and_bank_value": "36230.50",
  "assets_tracked": 7,
  "created": true
}
```

### `GET /api/v1/networth/history`

Retorna els snapshots per al període indicat.

| Paràmetre | Tipus | Default | Opcions |
|-----------|-------|---------|---------|
| `period` | `str` (query) | `1y` | `1m`, `3m`, `6m`, `1y`, `2y`, `5y`, `all` |

**Resposta 200:**
```json
{
  "period": "1y",
  "snapshots": [...],
  "current_net_worth": "125430.50",
  "change_eur_period": "+12430.50",
  "change_pct_period": "+11.00"
}
```

---

## Scripts de manteniment

```bash
# Resum complet del net worth amb posicions per asset
make net-worth

# Equivalent Docker directe:
docker compose exec backend python scripts/net_worth.py
```

Output exemple:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  WealthPilot — Net Worth
  2025-03-28 14:30 UTC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

─────────────────── Comptes MoneyWiz ────────────────────────
  ➕ Compte Corrent              checking      EUR     1.500,00 €
  ➕ Trade Republic              investment    EUR    89.200,00 €

  Efectiu i comptes                             1.500,00 €
  Cartera d'inversió                           89.200,00 €

─────────────────── Posicions d'inversió ────────────────────
  Asset                        Accions       Preu        Valor €     P&L €   P&L%
  ────────────────────────────────────────────────────────────────────────
  🟢 IWDA                        12,5000    85,3200    1.066,50   +66,50  +6.66%
     ticker: IWDA.AS             cost:      1.000,00 €   preu: 2025-03-27
  ...
```

---

## Decisions de disseny

### Dues fonts per al total vs. el desglossat

El total del net worth llegeix `mw_accounts.current_balance` perquè:
1. MoneyWiz fa els seus propis ajustos interns (revaluació de criptos, etc.)
2. Alguns assets no estan mapejats a `assets.ticker_mw` (e.g. NUKL)
3. El balanç d'inversió de MW és el que l'usuari veu a l'app real

El desglossat per asset usa `shares × preu YF` perquè és l'única manera d'obtenir:
- Cost basis per asset
- P&L realitzat/no realitzat per asset
- Pes de cada asset a la cartera

Pot haver-hi una petita divergència entre els dos valors. Això és **esperat i documentat**.

### change_eur vs. el snapshot anterior

`change_eur` i `change_pct` es calculen respecte l'snapshot **immediatament anterior** (`snapshot_date < :d`), no respecte el dia anterior del calendari. Això garanteix coherència fins i tot si hi ha dies sense snapshot.

---

## Tests

`tests/test_networth.py` — cobreix:

- **Schema**: existència de taules `net_worth_snapshots` i `asset_snapshots`, columnes requerides, constraint `uq_networth_date`, columnes `shares`/`mw_symbol` a `mw_transactions`
- **API POST /snapshot**: 201, shape de resposta, data específica, idempotència, data invàlida → 422
- **API GET /history**: 200, shape, tots els períodes vàlids, període invàlid → 422, ordre ascendent, periode reflectit
- **Servei**: cash_and_bank_value llegit de mw_accounts, aritmètica (cash + inv - liab), comptes exclosos no comptats, change_eur calculat correctament
