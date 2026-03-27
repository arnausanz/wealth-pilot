# Backend Core — FastAPI + SQLAlchemy Async

> Última actualització: Març 2026

---

## Estructura de Fitxers

```
backend/
├── core/
│   ├── config.py      Pydantic BaseSettings llegint .env
│   ├── db.py          Engine async, AsyncSessionLocal, Base, get_db()
│   ├── errors.py      Handlers globals 404/500 → JSON consistent
│   ├── logging.py     Structured logging a stdout
│   └── security.py    Placeholder per a API key auth
├── modules/
│   └── <mòdul>/
│       ├── __init__.py
│       ├── models.py   Models SQLAlchemy (Mapped / mapped_column)
│       ├── schemas.py  Pydantic v2 schemas (request/response)
│       ├── service.py  Lògica de negoci (async functions)
│       └── router.py   FastAPI router (endpoints)
├── tests/
│   ├── conftest.py       Fixtures compartides (_use_null_pool, db_conn, http_client)
│   ├── test_api.py       Tests dels endpoints FastAPI base
│   ├── test_database.py  Tests d'estructura de la BD
│   ├── test_seed.py      Tests de les dades inicials
│   └── test_market.py    Tests del mòdul de mercat
├── scripts/
│   └── seed.py         Seed idempotent
├── alembic/
│   ├── env.py          Async migrations + importació de tots els models
│   ├── script.py.mako  Template de migracions
│   └── versions/       Fitxers de migració generats
├── alembic.ini
├── main.py             App FastAPI (< 80 línies)
├── pytest.ini
└── requirements.txt
```

---

## `core/config.py` — Settings

```python
class Settings(BaseSettings):
    DATABASE_URL: str           # postgresql+asyncpg://user:pass@host/db
    ENV: str = "development"
    LOG_LEVEL: str = "debug"
    APP_VERSION: str = "0.1.0"
    CORS_ORIGINS: str = "http://localhost:8080"   # str, NO list[str]!
    model_config = {"env_file": ".env", "extra": "ignore"}
```

**Regla important:** `CORS_ORIGINS` ha de ser `str`, no `list[str]`. pydantic-settings v2 intenta `json.loads()` sobre camps `list[str]` i falla amb valors no-JSON. El split es fa manualment a `main.py`.

---

## `core/db.py` — Connexió Async

```python
engine = create_async_engine(settings.DATABASE_URL, echo=(settings.ENV == "development"))
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

`get_db()` és el dependency per a tots els routers: `session: AsyncSession = Depends(get_db)`.

**Nota de tests:** `get_db()` accedeix a `AsyncSessionLocal` via els seus `__globals__` (el namespace del mòdul `core.db`). Per tant, el fixture `_use_null_pool` de conftest.py pot monkey-patchar `core.db.AsyncSessionLocal` i `get_db()` veurà el nou valor automàticament — sense cap canvi al codi de producció.

---

## `main.py` — App FastAPI amb Lifespan

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gap fill automàtic a l'arrencada: descarrega preus que falten a la BD."""
    try:
        async with AsyncSessionLocal() as db:
            result = await market_service.fill_all_gaps(db)
    except Exception as exc:
        logger.error("Startup gap fill failed (non-fatal): %s", exc)
    yield

app = FastAPI(lifespan=lifespan, ...)
```

El servidor arrenca sempre, fins i tot si Yahoo Finance és inaccessible (el `try/except` ho garanteix). En cada reinici, la BD es posa al dia automàticament.

**Afegir nous mòduls (2 línies):**
```python
from modules.nom_modul.router import router as nom_router
app.include_router(nom_router, prefix="/api/v1")
```

---

## Models SQLAlchemy 2.0

Tots els models usen la nova sintaxi amb `Mapped` i `mapped_column`:

```python
class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    target_weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    contributions: Mapped[List["Contribution"]] = relationship("Contribution", back_populates="asset")
```

Avantatges sobre la sintaxi clàssica: type-safe, autocomplete millor, errors en temps de compilació.

---

## Afegir un Nou Mòdul

1. Crear `backend/modules/nom_modul/` amb `__init__.py`
2. Crear `models.py` (models SQLAlchemy)
3. Crear `schemas.py` (Pydantic v2 request/response)
4. Crear `service.py` (lògica de negoci async)
5. Crear `router.py` (FastAPI router)
6. Afegir a `alembic/env.py`: `from modules.nom_modul.models import *`
7. Afegir a `main.py`:
   ```python
   from modules.nom_modul.router import router as nom_router
   app.include_router(nom_router, prefix="/api/v1")
   ```
8. `make migration name="add_nom_modul"` + `make migrate`

**Total de canvis a fitxers existents: 2 línies** (env.py + main.py). Tot el codi nou va a la carpeta nova.

---

## Format d'Errors (API)

Tots els errors segueixen el mateix format JSON:

```json
// 404
{"error": "Not found", "path": "/api/v1/ruta-inexistent"}

// 500
{"error": "Internal server error"}

// 422 (validació Pydantic - automàtic de FastAPI)
{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}
```

---

## Endpoints Actuals

### Sistema
| Mètode | Ruta | Descripció |
|--------|------|-----------|
| `GET` | `/health` | Status, versió i entorn |
| `GET` | `/api/v1` | Llista de mòduls disponibles |
| `GET` | `/api/docs` | Swagger UI (autogenerat) |
| `GET` | `/api/redoc` | ReDoc (autogenerat) |
| `GET` | `/api/openapi.json` | Esquema OpenAPI JSON |

### Mòdul Market (`/api/v1/market`)
| Mètode | Ruta | Descripció |
|--------|------|-----------|
| `GET` | `/api/v1/market/prices` | Preus actuals de tots els assets actius (amb cache 5 min) |
| `GET` | `/api/v1/market/prices/{asset_id}` | Preu actual d'un asset concret |
| `POST` | `/api/v1/market/refresh` | Desencadena un gap fill des de Yahoo Finance |
| `GET` | `/api/v1/market/history/{asset_id}?days=30` | Historial OHLCV (1–3650 dies) |

---

## Seed Script

`backend/scripts/seed.py` és idempotent: comprova si cada registre existeix abans d'inserir-lo. Es pot executar N vegades sense duplicats.

Dades sembrades:
- **8 assets**: MSCI World, Physical Gold, MSCI Europe, MSCI EM IMI, Japan, Europe Defence, Bitcoin, Cash
- **24 escenaris**: 3 (advers/base/optimista) × 8 assets, amb annual_return i volatilitat
- **7 contribucions mensuals**: una per asset (excepte Cash), dia 2 de cada mes
- **18 paràmetres globals**: portfolio (cash, rebalanceig), simulació (horitzó, inflació), fiscalitat (trams IRPF), personal, UI
- **2 objectius**: Compra d'habitatge (80.000€, 2029) + Fons d'Emergència (15.000€)
- **4 índexs de mercat**: S&P 500, MSCI World ETF, Euro Stoxx 50, EURIBOR
- **8 widgets de dashboard**: net worth, on track, donut chart, objectius, rebalanceig, transaccions, alertes, simulació
