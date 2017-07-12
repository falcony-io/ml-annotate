import os
import sys
import warnings
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.exc import SAWarning

ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
sys.path.append(ROOT)

from annotator import app
from annotator.models import *
from annotator.extensions import db

# Don't raise exception on `SAWarning`s. For example, if Alembic does
# not recognize some column types when autogenerating migrations,
# Alembic would otherwise crash with SAWarning.
warnings.simplefilter('ignore', SAWarning)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)


def get_target_metadata():
    # load_models()
    return db.metadata

target_metadata = get_target_metadata()


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = app.config['SQLALCHEMY_DATABASE_URI']
    context.configure(url=url)

    with context.begin_transaction():
        context.run_migrations()


def include_symbol(tablename, schema):
    return not (tablename in ['activity', 'transaction'] and schema == 'audit')


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    url = app.config['SQLALCHEMY_DATABASE_URI']
    engine = create_engine(url, poolclass=pool.NullPool)

    connection = engine.connect()
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_symbol=include_symbol
    )

    try:
        with context.begin_transaction():
            connection.execute('SELECT pg_advisory_lock(1)')
            context.run_migrations()
    finally:
        connection.close()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
