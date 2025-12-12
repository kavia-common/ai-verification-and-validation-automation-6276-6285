import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Interpret the config file for Python logging.
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Build Flask app to extract SQLAlchemy metadata and DB URL
from app import create_app  # noqa
from app.extensions import db  # noqa

flask_app = create_app()
with flask_app.app_context():
    target_metadata = db.metadata
    # Set URL from Flask config, preferring env DATABASE_URL if present
    url = os.getenv("DATABASE_URL") or flask_app.config.get("SQLALCHEMY_DATABASE_URI")

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=False,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        {"sqlalchemy.url": url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, include_schemas=False)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
