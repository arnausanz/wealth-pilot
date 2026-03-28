.PHONY: dev dev-bg down build rebuild logs ps db-shell migrate migration seed test check-prices sanity update-data clean clean-all

# ─── Development ──────────────────────────────────────────────────────────────

dev:
	docker compose up

dev-bg:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

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

# ─── Tests ────────────────────────────────────────────────────────────────────

test:
	@bash tests/run_tests.sh

# ─── Cleanup ──────────────────────────────────────────────────────────────────

clean:
	docker compose down -v --remove-orphans

clean-all:
	docker compose down -v --remove-orphans --rmi local
