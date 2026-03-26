.PHONY: dev dev-bg down build rebuild logs ps db-shell migrate migration seed test clean clean-all

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

# ─── Tests ────────────────────────────────────────────────────────────────────

test:
	@bash tests/run_tests.sh

# ─── Cleanup ──────────────────────────────────────────────────────────────────

clean:
	docker compose down -v --remove-orphans

clean-all:
	docker compose down -v --remove-orphans --rmi local
