# WealthPilot — Roadmap

> Actualitzat: Març 2026 | Stack: FastAPI + React + PostgreSQL + Docker (dev) / Systemd + Nginx (prod)

---

## Completat ✅

| Fase | Contingut |
|------|-----------|
| 0 | Infraestructura: Docker Compose, PostgreSQL, FastAPI, Vite/React, 64 taules |
| 1 | Sync MoneyWiz, market prices (Yahoo Finance), net worth snapshots |
| 2 | Dashboard, Portfolio, rebalanceig, asset snapshots |
| 3 | Simulació (motor FV), historial de transaccions |
| 4 | Config UI: assets, aportacions, escenaris, objectius, paràmetres, reset defaults |
| 5 | Analytics (despeses, flux caixa, evolució net worth, alertes) + Simulador Obert |
| PWA | manifest.json, service-worker, icones, meta tags iOS |

---

## FASE 6 — Deploy Oracle Cloud 🔄 En curs

**VM:** Ubuntu 22.04 ARM (4 CPUs, 24GB RAM) · IP: 79.76.110.205 · Domini: `79-76-110-205.sslip.io`

- [ ] Obrir ports 80/443 a Oracle Security List + iptables
- [ ] Instal·lar: nginx, certbot, python3.12, node 20, postgresql
- [ ] Crear BD + usuari PostgreSQL (`wealthpilot_db`)
- [ ] Clonar repo + crear `/opt/wealthpilot/venv` + `pip install`
- [ ] Build frontend: `npm ci && npm run build` → `/opt/wealthpilot/dist`
- [ ] Crear `/opt/wealthpilot/.env.prod` (a partir de `deployment/.env.prod.template`)
- [ ] Copiar nginx.conf (substituir `DOMAIN_PLACEHOLDER`) + habilitar site
- [ ] Instal·lar i arrencar `wealthpilot.service` (systemd)
- [ ] Let's Encrypt: `certbot --nginx -d 79-76-110-205.sslip.io`
- [ ] Migracions + seed: `alembic upgrade head` + `python scripts/seed.py`
- [ ] Importar backup MoneyWiz (via `/api/v1/sync/upload`)
- [ ] **✓ MILESTONE: App live a HTTPS**

**Scripts preparats:** `deployment/setup.sh` (first-time) · `deployment/deploy.sh` (actualitzar) · `deployment/nginx.conf`

---

## FASE 7 — Test mòbil PWA

- [ ] Instal·lar com a PWA al Safari iOS: obrir URL → Compartir → Afegir a pantalla d'inici
- [ ] Verificar mode standalone (sense barra d'adreça)
- [ ] Revisar totes les pantalles a 390px (iPhone)
- [ ] Anotar problemes UX/visual per a Fase 8
- [ ] **✓ MILESTONE: PWA instal·lada i funcional al mòbil**

---

## FASE 8 — Polish UX/UI (post-test mòbil)

Prioritats identificades durant el test mòbil:

### 8.1 Gràfics
- [ ] Redissenyar `ProjectionChart` (simulació): més llegible, labels millors, grids subtils
- [ ] Charts d'analytics (despeses, flux caixa): millorar estètica, llegibilitat en pantalla petita
- [ ] Net worth evolution: anotacions d'events importants sobre la línia
- [ ] Consistència visual entre tots els gràfics (paleta, tipografia, espais)
- [ ] **Tooltip al gràfic de la home**: mantenir premut → quadre flotant amb net worth i rendiment a aquella data (estil Trade Republic). Implementar amb `onTouchStart`/`onTouchMove` sobre el SVG, calculant la posició X relativa i interpolant el snapshot més proper.

### 8.2 Simulació
- [ ] Simplificar el flow: slider + resultats en un sol scroll, sense tabs
- [ ] Simulador Obert: UX més intuïtiva per crear i afegir events
- [ ] Previsualització en temps real mentre s'afegeix un event (sense botó "Comparar")
- [ ] Cards de resum de simulació més llegibles (valors finals destacats)

### 8.3 Configuració
- [ ] Redisseny complet de `SettingsScreen`: UI d'app real, no formulari web
- [ ] Edició inline amb feedback visual millor (no tap-to-edit ocult)
- [ ] Grups visuals clars entre seccions
- [ ] Indicador de "canvis pendents de guardar" si aplica

### 8.4 Historial de transaccions
- [ ] Mostrar nom del payee (taula `mw_payees`) a cada transacció
- [ ] Mostrar categoria (taula `mw_categories`) amb color + icona
- [ ] Cerca per text (descripció, payee, categoria)
- [ ] Agrupació per dia/setmana amb subtotals
- [ ] Millor badge visual per tipus de transacció (compra, venda, ingrés, despesa)

### 8.5 Net Worth — visibilitat de comptes
- [ ] Desglossar `cash_and_bank_value` per compte (taula `mw_accounts`)
- [ ] Mostrar saldo de cada compte a la pantalla principal (o expandible)
- [ ] Indicar quin compte té la liquiditat (compte corrent vs. estalvi)
- [ ] Distingir visualment entre efectiu, inversions, altres actius

---

## FASE 9 — iOS Natiu amb Capacitor (Opcional)

- [ ] `@capacitor/core` + `@capacitor/ios`
- [ ] iOS Shortcut: backup MoneyWiz → auto-push a `/api/v1/sync/upload`
- [ ] Notificació push post-sync
- [ ] Distribució TestFlight (requereix Apple Developer Account, €99/any)

---

## Backlog (futur)

- Immobles al net worth (valor, hipoteca, rendibilitat)
- Jubilació: simulació "quan puc jubilar-me amb X€/mes?"
- Monte Carlo simulation per a la projecció
- Exportació PDF d'informes fiscals
- Inflació com a paràmetre explícit (valor real vs. nominal)
- Múltiples monedes
- Open Banking / importació automàtica de broker
