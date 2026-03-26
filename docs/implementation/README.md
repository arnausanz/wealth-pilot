# Implementation Docs

Documentació tècnica del projecte WealthPilot. Un fitxer per àrea, actualitzats a mesura que avança el projecte.

| Fitxer | Contingut |
|--------|----------|
| [01-stack-i-arquitectura.md](01-stack-i-arquitectura.md) | Stack tecnològic, estructura de directoris, principi core-immutable, estratègia de desplegament |
| [02-base-de-dades.md](02-base-de-dades.md) | 64 taules, tots els mòduls documentats, decisions de disseny (FIFO, JSONB, idempotència) |
| [03-backend-core.md](03-backend-core.md) | FastAPI, SQLAlchemy 2.0, configuració, endpoints actuals, com afegir un nou mòdul |
| [04-frontend-core.md](04-frontend-core.md) | SPA vanilla JS, PWA, router, API client, event bus, sistema de disseny, com afegir una pantalla |
| [05-tests.md](05-tests.md) | Pytest, fixtures, cobertura, filosofia integració vs. mocking |
| [06-desplegament.md](06-desplegament.md) | Docker Compose local, Systemd Oracle Cloud, variables d'entorn, Nginx, HTTPS |
