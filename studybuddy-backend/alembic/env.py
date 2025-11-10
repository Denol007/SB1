"""Alembic environment configuration for async SQLAlchemy.

This module configures Alembic to work with async SQLAlchemy engines.
It loads database configuration from environment variables and supports
both online and offline migration modes.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import app config and database base
from app.core.config import settings
from app.infrastructure.database.base import Base

# Import all models so they're registered with Base.metadata
# This is required for autogenerate to detect schema changes
from app.infrastructure.database.models.comment import Comment  # noqa: F401
from app.infrastructure.database.models.community import Community  # noqa: F401
from app.infrastructure.database.models.membership import Membership  # noqa: F401
from app.infrastructure.database.models.post import Post  # noqa: F401
from app.infrastructure.database.models.reaction import Reaction  # noqa: F401
from app.infrastructure.database.models.university import University  # noqa: F401
from app.infrastructure.database.models.user import User  # noqa: F401
from app.infrastructure.database.models.verification import Verification  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the database URL from settings (loaded from .env)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# add your model's MetaData object here for 'autogenerate' support
# This allows Alembic to detect schema changes automatically
target_metadata = Base.metadata

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
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect default value changes
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Execute migrations with the given connection.

    Args:
        connection: Database connection to use for migrations.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect default value changes
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode.

    Creates an async engine and runs migrations within an async context.
    This is required for async SQLAlchemy.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    For async SQLAlchemy, we use asyncio.run to execute
    the async migration function.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
