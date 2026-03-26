# Base de Dades — Esquema Complet

> Última actualització: Març 2026 | 64 taules | 1 migració aplicada

---

## Filosofia del Schema

**"Millor 150 taules i n'esborro 100 que crear-ne 10 i afegir-ne 100 més."**

L'esquema és deliberadament complet des del dia 1. Les taules que no s'usin ara no costen res en PostgreSQL (zero overhead si estan buides). Evita haver d'afegir taules a mig projecte, que forçaria migracions complicades i potencialment canvis a l'ORM.

---

## Mòduls i Taules (64 total)

### `modules/portfolio` — Core d'inversions
| Taula | Descripció |
|-------|-----------|
| `assets` | ETFs, crypto, commodities, cash. Inclou ticker MW, ticker YF, ISIN, target_weight, color_hex |
| `contributions` | Contribucions mensuals recurrents per asset (import, dia del mes, dates d'inici/fi) |
| `extraordinary_contributions` | Aportacions puntuals planificades (data, import, executada?) |
| `transactions` | Transaccions d'inversió importades de MoneyWiz. **Immutables.** UNIQUE(data, asset, import, shares) |
| `tax_lots` | Lots de compra FIFO per a càlcul de cost basis i fiscalitat espanyola |
| `price_history` | Preus de tancament diaris (Yahoo Finance). UNIQUE(asset, data) |
| `dividends` | Dividends i interessos rebuts per asset |
| `corporate_actions` | Splits, mergers, spinoffs (afecten al càlcul de cost basis) |

### `modules/config` — Configuració editable des de la UI
| Taula | Descripció |
|-------|-----------|
| `scenarios` | Retorn anual esperat per asset × escenari (advers/base/optimista). Inclou volatilitat per a Monte Carlo |
| `objectives` | Objectius financers (compra de pis, fons d'emergència, etc.) amb target_amount i target_date |
| `parameters` | Paràmetres globals key-value (cash_balance, trams IRPF, horitzó simulació, etc.) |
| `parameter_history` | Audit trail immutable de tots els canvis de paràmetres |

### `modules/sync` — Integració MoneyWiz
| Taula | Descripció |
|-------|-----------|
| `import_batches` | Registre de cada upload de backup MoneyWiz (status, counts, errors) |
| `mw_accounts` | Comptes de MoneyWiz (banc, inversió, crèdit, efectiu) |
| `mw_categories` | Jerarquia de categories de despeses/ingressos (self-referencial) |
| `mw_payees` | Comerciants i contraparts (Mercadona, Netflix, etc.) |
| `mw_transactions` | Transaccions financeres (despeses, ingressos, transferències). **No confondre amb `transactions`** |
| `recurring_expenses` | Despeses recurrents detectades o definides manualment (subscripcions, lloguer, etc.) |

### `modules/simulation` — Motor de projecció
| Taula | Descripció |
|-------|-----------|
| `simulations` | Escenari de simulació guardat (nom, tipus, horitzó, escenari base) |
| `simulation_params` | Overrides per a una simulació (key-value: contribució mensual, rendiment, etc.) |
| `simulation_events` | Events puntuals: canvi de feina (+500€/mes), compra de pis (−80k), etc. |
| `simulation_results` | Resultats mensuals pre-calculats (portfolio_value, total_contributed, total_returns) |
| `monte_carlo_runs` | Resultats de simulació Monte Carlo: percentils P10, P25, P50, P75, P90 |

### `modules/networth` — Evolució del patrimoni
| Taula | Descripció |
|-------|-----------|
| `net_worth_snapshots` | Snapshot diari del patrimoni net total, desglossat per classe d'actiu |
| `asset_snapshots` | Detall per asset dins d'un snapshot (shares, preu, valor, cost basis, P&L) |
| `net_worth_milestones` | Fites de patrimoni (100k, 200k, etc.) — automàtiques o manuals |

### `modules/analytics` — Analítica personal
| Taula | Descripció |
|-------|-----------|
| `budgets` | Pressupost mensual per categoria (planificat vs. real) |
| `monthly_summaries` | Resum mensual pre-calculat (ingressos, despeses, inversions, estalvi, savings rate) |
| `income_sources` | Fonts d'ingressos (salari, freelance, lloguers, dividends) |
| `income_records` | Ingrés real rebut per data i font (amb brut/net/retenció) |
| `spending_patterns` | Patrons de despesa per categoria (mitjana, desviació estàndard) per a detecció d'anomalies |

### `modules/market` — Dades de mercat
| Taula | Descripció |
|-------|-----------|
| `market_indices` | Índexs de referència (S&P 500, MSCI World, Eurostoxx 50, EURIBOR) |
| `market_index_data` | Dades diàries dels índexs (OHLCV + daily_return_pct) |
| `exchange_rates` | Tipus de canvi diaris (base EUR). Necessari per a assets en USD, GBP, JPY |
| `price_fetch_logs` | Log de cada fetch de Yahoo Finance (status, temps de resposta, errors) |

### `modules/history` — Historial fiscal
| Taula | Descripció |
|-------|-----------|
| `tax_reports` | Informe fiscal anual (guanys realitzats, base imposable, IRPF estimat, dividends) |
| `realized_gains` | Guany/pèrdua per cada venda (FIFO, amb lot d'adquisició, data, cost basis) |

### `modules/realestate` — Immobiliàri
| Taula | Descripció |
|-------|-----------|
| `properties` | Propietats (residència principal, inversió, vacacional). Inclou referència cadastral |
| `property_valuations` | Valoracions històriques (manual, Idealista, taxació notarial) |
| `mortgages` | Hipoteques: import, tipus d'interès (fix/variable), spread Euribor, quota mensual |
| `mortgage_payments` | Pagaments mensuals de la hipoteca (principal + interessos) |
| `rental_income` | Ingressos per lloguer d'immobles d'inversió |
| `property_expenses` | Despeses de la propietat: IBI, comunitat, assegurança, manteniment |

### `modules/pensions` — Pensions
| Taula | Descripció |
|-------|-----------|
| `pension_plans` | Plans de pensions privats (individual, empresa, EPSV, PIAS) |
| `pension_contributions` | Aportacions al pla (deduïbles d'IRPF) |
| `pension_valuations` | Valoració periòdica del pla (unitats × valor liquidatiu) |
| `social_security_estimates` | Estimació de pensió pública (Seguretat Social) a les 65/67/70 anys |

### `modules/credit` — Crèdit
| Taula | Descripció |
|-------|-----------|
| `credit_accounts` | Targetes de crèdit i línies de crèdit (límit, saldo, interès) |
| `credit_statements` | Extractes mensuals (saldo tancament, data de venciment, estat del pagament) |
| `credit_payments` | Pagaments de targeta (complet, mínim, parcial) |

### `modules/alerts` — Alertes automàtiques
| Taula | Descripció |
|-------|-----------|
| `alert_rules` | Regles configurables: desviació de portfolio, pic de despesa, objectiu en risc, etc. |
| `alert_history` | Registre de cada alerta disparada (missatge, valor disparador, estat: nova/llegida/resolta) |

### `modules/system` — Sistema
| Taula | Descripció |
|-------|-----------|
| `audit_log` | Audit trail immutable de totes les operacions d'escriptura via API |
| `api_keys` | API keys per a autenticació M2M (iOS Shortcut, scripts). Hash SHA-256, mai en clar |
| `app_versions` | Registre de versions desplegades |
| `scheduled_tasks` | Tracking de tasques programades (fetch de preus, snapshots, etc.) |

### `modules/preferences` — Preferències
| Taula | Descripció |
|-------|-----------|
| `user_preferences` | Preferències de la UI (moneda, format de dates, animacions, notificacions) |
| `dashboard_widgets` | Configuració dels widgets del dashboard (visibilitat, ordre, config específica) |
| `report_templates` | Templates de reports guardats (fiscal anual, resum de cartera, etc.) |

### `modules/tags` — Etiquetes i notes
| Taula | Descripció |
|-------|-----------|
| `tags` | Etiquetes definides per l'usuari (nom, color) |
| `transaction_tags` | Many-to-many: tags en transaccions d'inversió |
| `mw_transaction_tags` | Many-to-many: tags en transaccions de MoneyWiz |
| `notes` | Notes de text lliure associables a qualsevol entitat del sistema |
| `note_tags` | Many-to-many: tags en notes |

---

## Decisions de Disseny

### FIFO per a fiscalitat espanyola
`tax_lots` implementa el mètode FIFO obligatori a Espanya (Art. 37.2 LIRPF). Cada compra crea un lot; cada venda consumeix lots en ordre cronològic i genera un registre a `realized_gains`.

### JSONB per a dades semi-estructurades
`simulation_results.asset_breakdown`, `alert_rules.condition_config`, `audit_log.old_values/new_values` usen JSONB. Permet flexibilitat sense afegir columnes, i PostgreSQL suporta índexs JSONB si cal.

### Separació `transactions` vs `mw_transactions`
- `transactions`: transaccions d'**inversió** (compres/vendes/dividends d'ETFs). Immutables, importades de MW.
- `mw_transactions`: transaccions **financeres generals** (despeses, ingressos, transferències). Raw data de MoneyWiz.

### Import batch per a idempotència
`import_batches` + `UNIQUE` constraints a `transactions` i `mw_transactions` garanteixen que pujar el mateix backup de MoneyWiz N vegades és idempotent (zero duplicats).

---

## Migracions

```bash
make migration name="descripcio"   # Genera nova migració (autogenerate des dels models)
make migrate                        # Aplica migracions pendents a la BD
```

`alembic/env.py` importa TOTS els models via `from modules.X.models import *` per garantir que autogenerate els detecti. Quan s'afegeixi un nou mòdul amb models, cal afegir la seva importació aquí.
