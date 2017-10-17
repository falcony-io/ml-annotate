import psycopg2
import sqlalchemy as sa
from flask_login import LoginManager, current_user
from flask_sqlalchemy import BaseQuery, SQLAlchemy
from sqlalchemy_utils import force_auto_coercion
from sqlalchemy_utils.types.pg_composite import (register_psycopg2_composite,
                                                 registered_composites)

db = SQLAlchemy(session_options={'query_cls': BaseQuery})

# Assign automatic data type coercion. For example str representations of UUIDs
# are automatically coerced into UUID objects.
force_auto_coercion()


@sa.event.listens_for(sa.pool.Pool, 'connect', named=True)
def register_composites(dbapi_connection, **kw):
    for name, composite in registered_composites.items():
        try:
            register_psycopg2_composite(
                dbapi_connection,
                composite
            )
        except psycopg2.ProgrammingError as e:
            if str(e) != "PostgreSQL type '{}' not found".format(name):
                raise


def fetch_current_user_id():
    return current_user.id


login_manager = LoginManager()
login_manager.login_view = "login"
