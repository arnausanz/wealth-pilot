.PHONY: dev dev-bg down build rebuild build-frontend logs logs-fe ps db-shell migrate migration seed test test-fe check-fe shell-fe check-prices sanity update-data net-worth clean clean-all

# ─── Development ──────────────────────────────────────────────────────────────
# Frontend runs at http://localhost:8080 (Vite dev server with hot reload)
# Backend API at http://localhost:8000

dev:
	docker compose up

dev-bg:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

build-frontend:
	docker compose build frontend

rebuild:
	docker compose build --no-cache

logs:
	docker compose logs -f

ps:
	docker compose ps

# ─── Database ─────────────────────────────────────────────────────────────────

db-shell:
	docker compose exec db sh -c 'psql -U $$POSTGRES_USER -d $$POSTGRES_DB'

migrate:
	docker compose exec backend alembic upgrade head

migration:
	@[ "$(name)" ] || (echo "Usage: make migration name=<description>" && exit 1)
	docker compose exec backend alembic revision --autogenerate -m "$(name)"

seed:
	docker compose exec backend python scripts/seed.py

check-prices:
	docker compose exec db sh -c 'psql -U $$POSTGRES_USER -d $$POSTGRES_DB -c "\
SELECT a.display_name, a.ticker_yf, a.asset_type, \
       ph.price_close, ph.currency, ph.price_date, \
       (CURRENT_DATE - ph.price_date) AS days_old \
FROM assets a \
LEFT JOIN LATERAL ( \
    SELECT price_close, currency, price_date \
    FROM price_history \
    WHERE asset_id = a.id \
    ORDER BY price_date DESC LIMIT 1 \
) ph ON TRUE \
WHERE a.is_active = TRUE \
ORDER BY a.sort_order;"'

# ─── Dades ────────────────────────────────────────────────────────────────────

sanity:
	docker compose exec backend python scripts/sanity_check.py

update-data:
	docker compose exec backend python scripts/update_data.py

net-worth:
	docker compose exec backend python scripts/net_worth.py

# ─── Tests ────────────────────────────────────────────────────────────────────

test:
	@bash tests/run_tests.sh

test-fe:
	docker compose exec frontend npm test

check-fe:
	docker compose exec frontend npm run typecheck

# ─── Frontend ─────────────────────────────────────────────────────────────────

logs-fe:
	docker compose logs -f frontend

shell-fe:
	docker compose exec frontend sh

# ─── Cleanup ──────────────────────────────────────────────────────────────────

clean:
	docker compose down -v --remove-orphans

clean-all:
	docker compose down -v --remove-orphans --rmi local
