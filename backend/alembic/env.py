import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# Afegir el directori arrel del backend al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.config import settings  # noqa: E402
from core.db import Base  # noqa: E402

# Importar tots els models aquí perquè Alembic els detecti en autogenerate
from modules.portfolio.models import *  # noqa: F401, E402
from modules.config.models import *  # noqa: F401, E402
from modules.sync.models import *  # noqa: F401, E402
from modules.simulation.models import *  # noqa: F401, E402
from modules.networth.models import *  # noqa: F401, E402
from modules.analytics.models import *  # noqa: F401, E402
from modules.market.models import *  # noqa: F401, E402
from modules.history.models import *  # noqa: F401, E402
from modules.realestate.models import *  # noqa: F401, E402
from modules.pensions.models import *  # noqa: F401, E402
from modules.credit.models import *  # noqa: F401, E402
from modules.alerts.models import *  # noqa: F401, E402
from modules.system.models import *  # noqa: F401, E402
from modules.preferences.models import *  # noqa: F401, E402
from modules.tags.models import *  # noqa: F401, E402

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(settings.DATABASE_URL)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
