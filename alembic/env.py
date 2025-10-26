from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# --- Alembic autogenerate support ---
import os
from dotenv import load_dotenv
import sys

# Add the project root to the Python path.
# This ensures that 'my_app' can be imported correctly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

# Import Base and dynamically load all models for autogenerate support.
# This is a more robust method than manually importing each model,
# especially when dealing with complex import dependencies or when, as the
# traceback suggests, a models/__init__.py file is also importing models.
from my_app.database import Base  # noqa
import pkgutil
import importlib

# Discover and import all models from the my_app.models package.
models_package_path = os.path.join(os.path.dirname(__file__), "..", "my_app", "models")
for _, name, _ in pkgutil.iter_modules([models_package_path]):
    if not name.startswith("_"):
        importlib.import_module(f"my_app.models.{name}")

target_metadata = Base.metadata

# Set sqlalchemy.url from environment variable, making it sync for Alembic
db_url = os.getenv("DATABASE_URL")
if db_url:
    # Alembic runs synchronously, so we need a synchronous DBAPI driver.
    # If the URL is for asyncpg, replace it with a standard one.
    sync_db_url = db_url.replace("postgresql+asyncpg", "postgresql")
    config.set_main_option("sqlalchemy.url", sync_db_url)

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
