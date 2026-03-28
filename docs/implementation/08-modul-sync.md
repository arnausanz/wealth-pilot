# 08 — Mòdul Sync (MoneyWiz Parser)

## Visió general

El mòdul `sync` importa backups de MoneyWiz a PostgreSQL seguint una estratègia de **mirror complet**: la BD és una còpia fidel del darrer backup. Cada upload aplica upserts de tot el contingut del ZIP i esborra el que ja no hi sigui. Pujar el mateix ZIP N vegades produeix exactament el mateix estat a la BD.

### Fitxers

```
backend/
  modules/sync/
    __init__.py
    models.py      ← 6 taules ORM (ImportBatch, MWAccount, MWCategory, MWPayee, MWTransaction, RecurringExpense)
    service.py     ← parser + upsert logic
    schemas.py     ← Pydantic (ImportBatchOut, SyncStatusOut)
    router.py      ← 3 endpoints REST
  tests/
    test_sync.py   ← 34 tests (taules, parser pur, endpoints)
```

---

## Format intern de MoneyWiz

MoneyWiz usa **Apple Core Data** amb una sola taula `ZSYNCOBJECT` (~300 columnes) per a totes les entitats. El camp `Z_ENT` identifica el tipus d'entitat (mapat via `Z_PRIMARYKEY`).

### Entitats que importem

| Z_ENT | Nom MoneyWiz | → Taula nostra | Comentari |
|-------|-------------|----------------|-----------|
| 10 | BankChequeAccount | `mw_accounts` | `account_type = "checking"` |
| 11 | BankSavingAccount | `mw_accounts` | `account_type = "savings"` |
| 12 | CashAccount | `mw_accounts` | `account_type = "cash"` |
| 13 | CreditCardAccount | `mw_accounts` | `account_type = "credit"` |
| 14 | LoanAccount | `mw_accounts` | `account_type = "loan"` |
| 15 | InvestmentAccount | `mw_accounts` | `account_type = "investment"` |
| 16 | ForexAccount | `mw_accounts` | `account_type = "forex"` |
| 19 | Category | `mw_categories` | Jeràrquiques, pares primer |
| 47 | WithdrawTransaction | `mw_transactions` | `tx_type = "expense"` |
| 37 | DepositTransaction | `mw_transactions` | `tx_type = "income"` |
| 45 | TransferDepositTransaction | `mw_transactions` | `tx_type = "transfer_in"` |
| 46 | TransferWithdrawTransaction | `mw_transactions` | `tx_type = "transfer_out"` |
| 40 | InvestmentBuyTransaction | `mw_transactions` | `tx_type = "investment_buy"` |
| 41 | InvestmentSellTransaction | `mw_transactions` | `tx_type = "investment_sell"` |

### Timestamps

MoneyWiz guarda timestamps com a **segons des de 2001-01-01 00:00:00 UTC** (Apple Core Data epoch):

```python
_APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)

def _apple_ts_to_date(ts: float) -> date:
    return (_APPLE_EPOCH + timedelta(seconds=ts)).date()
```

### Categories (jeràrquia)

Les categories poden tenir pare (`ZPARENTCATEGORY` → FK a `ZSYNCOBJECT.Z_PK`). S'extreuen ordenades amb pares primer (`ORDER BY ZPARENTCATEGORY NULLS FIRST`) i s'importen en dos passos:

1. **Pas 1**: Insert/update de totes les categories amb `parent_id = NULL`.
2. **Pas 2**: UPDATE per resoldre les relacions pare-fill via `self-join` per `mw_internal_id`.

Això evita errors de FK ordering independentment de l'ordre d'arribada.

### Assignació de categories (split transactions)

MoneyWiz permet assignar múltiples categories a una sola transacció (*split*). La taula `ZCATEGORYASSIGMENT` conté N files per transacció. Nosaltres prenem la **categoria principal** (MIN Z_PK per transacció) per simplicitat:

```sql
LEFT JOIN (
    SELECT ZTRANSACTION, MIN(ZCATEGORY) AS ZCATEGORY
    FROM ZCATEGORYASSIGMENT
    GROUP BY ZTRANSACTION
) agg ON agg.ZTRANSACTION = s.Z_PK
```

---

## Flux del servei

```
POST /api/v1/sync/upload
         │
         ▼
1. Validació: .zip, < 100 MB, no buit
         │
         ▼
2. Crear ImportBatch (status="processing") → COMMIT immediat
         │
         ▼
3. asyncio.to_thread(_parse_zip_sync)
   ├── Extreure ZIP a tempdir (inclou -wal i -shm)
   ├── sqlite3.connect()   ← WAL s'aplica automàticament
   ├── _read_accounts()    ← SELECT Z_ENT IN (10,11,12,13,14,15,16)
   ├── _read_categories()  ← SELECT Z_ENT = 19
   └── _read_transactions()← SELECT Z_ENT IN (47,37,45,46,40,41) + JOIN categories
         │
         ▼
4. _upsert_accounts()
   └── INSERT ... ON CONFLICT (mw_internal_id) DO UPDATE (balanç, flags)
         │
         ▼
5. _upsert_categories()
   ├── Pas 1: INSERT ... ON CONFLICT DO UPDATE (sense parent_id)
   └── Pas 2: UPDATE parent_id via self-join
         │
         ▼
6. _upsert_transactions() [chunks de 500]
   └── INSERT ... ON CONFLICT (uq_mw_transactions_mw_id) DO UPDATE
       (reflecteix edicions de data, import, notes, categoria fetes a MoneyWiz)
         │
         ▼
6b. _prune_removed(acc_ids, cat_ids, tx_ids)
   ├── DELETE mw_transactions WHERE mw_internal_id NOT IN (tx_ids del ZIP)
   ├── DELETE mw_categories WHERE mw_internal_id NOT IN (cat_ids del ZIP)
   └── DELETE mw_accounts  WHERE mw_internal_id NOT IN (acc_ids del ZIP)
   Ordre respecta FK constraints (tx → cat → acc).
   Guard: si alguna llista és buida, no s'elimina res d'aquella taula.
         │
         ▼
7. Actualitzar ImportBatch (status="completed", estadístiques) → COMMIT
         │
         ▼
Retorna ImportBatchOut
```

**En cas d'error:**
- `db.rollback()` desfà tots els upserts del pas 4-6.
- El `ImportBatch` del pas 2 (ja committed) s'actualitza a `status="failed"` via raw SQL.
- L'audit trail es conserva sempre.

---

## Estratègia Mirror

Cada upload garanteix que la BD és una còpia exacta del ZIP importat:

| Operació | Entitat | Detall |
|----------|---------|--------|
| **UPSERT** | `mw_accounts` | `ON CONFLICT DO UPDATE` — balanç i flags |
| **UPSERT** | `mw_categories` | `ON CONFLICT DO UPDATE` — nom i tipus |
| **UPSERT** | `mw_transactions` | `ON CONFLICT DO UPDATE` — data, import, notes, categoria |
| **DELETE** | tots | Registres de la BD no presents al ZIP (esborrats a MoneyWiz) |

El camp `mw_internal_id` = `str(Z_PK)` del SQLite de MoneyWiz. Com que `Z_PK` és immutable a MoneyWiz, garanteix unicitat cross-uploads.

**Implicació clau**: si l'usuari esborra una transacció a MoneyWiz i puja un nou backup, desapareixerà de la BD al proper upload. Si n'edita una (import, data, categoria), es reflectirà.

---

## Endpoints

### `POST /api/v1/sync/upload`

Puja un ZIP de backup de MoneyWiz i l'importa.

**Request:** `multipart/form-data`, camp `file` amb el fitxer `.zip`.

**Validacions:**
- Extensió ha de ser `.zip`
- Tamany màxim: 100 MB
- Ha de contenir almenys un fitxer `.sqlite`
- El ZIP ha de tenir format vàlid (ZipFile)

**Response 200:**
```json
{
  "id": 3,
  "filename": "iMoneyWiz-iCloud-Backup-2026_03_26.zip",
  "file_size_bytes": 38622464,
  "status": "completed",
  "records_found": 1524,
  "records_imported": 1524,
  "records_skipped": 0,
  "records_failed": 0,
  "mw_date_from": "2021-09-01",
  "mw_date_to": "2026-03-26",
  "error_log": null,
  "trigger_source": "api",
  "started_at": "2026-03-27T10:15:00Z",
  "completed_at": "2026-03-27T10:15:02Z",
  "created_at": "2026-03-27T10:15:00Z"
}
```

**Response 422:** ZIP invàlid, extensió incorrecta, fitxer buit, sense SQLite.

---

### `GET /api/v1/sync/status`

Estat actual de la sincronització.

**Response 200:**
```json
{
  "last_import": { "id": 3, "status": "completed", ... },
  "total_accounts": 9,
  "total_categories": 51,
  "total_transactions": 1397,
  "oldest_transaction": "2021-09-01",
  "newest_transaction": "2026-03-26"
}
```

---

### `GET /api/v1/sync/batches`

Historial de les darreres 20 importacions.

**Response 200:** `array` d'`ImportBatchOut`, del més recent al més antic.

---

## Taules de la BD

### `import_batches`
Registre de cada importació. Sempre es crea, fins i tot si falla.

| Columna | Tipus | Notes |
|---------|-------|-------|
| `id` | int PK | |
| `filename` | varchar(255) | Nom del fitxer original |
| `file_size_bytes` | int | |
| `status` | varchar(20) | `pending`, `processing`, `completed`, `failed`, `partial` |
| `records_found` | int | Total al ZIP (acc + cat + tx) |
| `records_imported` | int | Registres upserted (nous o actualitzats) |
| `records_skipped` | int | Registres eliminats del mirror (prune) |
| `mw_date_from` | date | Primera data de transacció al backup |
| `mw_date_to` | date | Última data de transacció al backup |
| `error_log` | text | Detall de l'error (si status=failed) |
| `trigger_source` | varchar(30) | `api`, `script`, `scheduled` |

### `mw_accounts`
Comptes de MoneyWiz.

| Columna | Tipus | Notes |
|---------|-------|-------|
| `mw_internal_id` | varchar(100) UNIQUE | `str(Z_PK)` de MoneyWiz |
| `name` | varchar(200) | |
| `account_type` | varchar(30) | `checking`, `savings`, `investment`, ... |
| `currency` | varchar(5) | |
| `current_balance` | numeric(14,4) | Balanç actual (actualitzat a cada sync) |
| `is_active` | bool | `NOT ZARCHIVED` |
| `include_in_networth` | bool | `ZINCLUDEINNETWORTH` |
| `last_synced_at` | timestamptz | Moment del darrer sync |

### `mw_categories`
Categories jeràrquiques de MoneyWiz (despeses/ingressos).

| Columna | Tipus | Notes |
|---------|-------|-------|
| `mw_internal_id` | varchar(100) UNIQUE | |
| `name` | varchar(200) | |
| `parent_id` | int FK self | NULL per a categories arrel |
| `category_type` | varchar(20) | `expense` (ZTYPE2=1), `income` (ZTYPE2=2) |

### `mw_transactions`
Totes les transaccions financeres. Actualitzables via upload (mirror).

| Columna | Tipus | Notes |
|---------|-------|-------|
| `mw_internal_id` | varchar(100) | Unique constraint `uq_mw_transactions_mw_id` |
| `account_id` | int FK | → `mw_accounts.id` |
| `category_id` | int FK | → `mw_categories.id` (pot ser NULL) |
| `tx_type` | varchar(20) | `expense`, `income`, `transfer_in/out`, `investment_buy/sell` |
| `tx_date` | date | Convertit des de Apple timestamp |
| `amount` | numeric(14,4) | Sempre positiu; `tx_type` encoda la direcció |
| `amount_eur` | numeric(14,4) | Ara = amount (gestió multi-divisa: tasca futura) |
| `notes` | text | `ZNOTES1` de MoneyWiz |
| `is_reconciled` | bool | `ZSTATUS1` |
| `import_batch_id` | int FK | Traçabilitat per import |

---

## Seguretat i privacitat

- **El ZIP de MoneyWiz mai va al repositori.** `.gitignore` exclou:
  - `/data/moneywiz/*.zip`
  - `/data/moneywiz/*.sqlite`
  - `/data/moneywiz/*.db`
- El ZIP es processa en un `TemporaryDirectory` que es neteja automàticament.
- Cap dada personal s'emmagatzema fora de la BD local (PostgreSQL en Docker).
- Els tests no usen dades reals: creen un SQLite sintètic en memòria.

---

## Tests (`test_sync.py` — 34 tests)

### `TestSyncTables` (6 tests, síncrons via `db_conn`)
- Existència de les taules `import_batches`, `mw_accounts`, `mw_categories`, `mw_transactions`
- Constraint `uq_mw_transactions_mw_id`
- Índex `idx_mw_tx_date`

### `TestMoneyWizParser` (13 tests, síncrons sense BD)
- Parser retorna claus correctes
- Comptes: count, camps, tipus d'inversió
- Categories: count, pares, fills
- Transaccions: count, tipus, imports positius, dates com a `date`, transfers

### `TestSyncEndpoints` (15 tests, asíncrons via `http_client`)
- `GET /status` i `GET /batches` retornen 200
- `POST /upload` rebutja: extensió incorrecta, fitxer buit, ZIP invàlid
- Upload amb ZIP sintètic: 200, batch creat, comptes/categories/transaccions importats
- **Idempotència**: dos uploads del mateix ZIP → mateixa quantitat de transaccions
- Segon upload del mateix ZIP reporta `records_skipped = 0` (res a eliminar)
- Batch apareix a la llista de `/batches`

---

## Decisió de disseny: mirror vs append-only

L'estratègia inicial era *append-only*: `ON CONFLICT DO NOTHING` per a transaccions, sense esborrats. Rebutjada perquè:
- Si l'usuari esborra una transacció a MoneyWiz, la BD quedaria desfasada per sempre.
- Si edita (import, categoria, data), els canvis no es propagarien.

L'estratègia **mirror complet** garanteix que la BD = darrer backup. El cost és una operació `DELETE ... NOT IN (...)` per taula en cada import, acceptable per al volum típic de MoneyWiz (~1.500–5.000 transaccions).

---

## Decisió de disseny: per què `asyncio.to_thread`

El parsing del SQLite (sqlite3) és **síncron**. Per no bloquejar el loop d'asyncio de FastAPI durant l'extracció i lectura (que pot trigar 1-3 s en backups grans), es crida via `asyncio.to_thread`. El resultat és un dict Python pur que el servei asíncron consumeix normalment per fer els upserts.

## Decisió de disseny: imports positius

Els imports a `mw_transactions.amount` sempre s'emmagatzemen positius. La direcció del flux de diners és implícita en `tx_type` (`expense`, `income`, etc.). Això simplifica les agregacions i evita errors de signe en els dashboards.

## Scripts de manteniment

| Script | Comanda | Descripció |
|--------|---------|------------|
| `scripts/update_data.py` | `make update-data` | Refresh de preus (Yahoo Finance) + mirror del ZIP més recent de `data/moneywiz/` |
| `scripts/sanity_check.py` | `make sanity` | Informe de salut: darrer sync, transaccions, preus per asset |

`make update-data` detecta automàticament el ZIP més recent per data de modificació a `data/moneywiz/`. Útil per a updates manuals fins que l'iOS Shortcut estigui implementat.

---

## Tasques futures

- **Multi-divisa**: si `ZCURRENCYNAME2 != EUR`, calcular `amount_eur` via taula `exchange_rates`.
- **Split transactions**: suportar múltiples categories per transacció (ara es pren MIN(Z_PK)).
- **Payees**: importar Z_ENT 28 si MoneyWiz en té (ara 0 en aquest export).
- **iOS Shortcut**: automatitzar upload via `POST /api/v1/sync/upload` amb API key.
- **Reconciliació**: creuar `investment_buy/sell` de `mw_transactions` amb `portfolio.transactions`.
