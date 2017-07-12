import sqlalchemy as sa
from .dataset import *  # noqa
from .label_event import *  # noqa
from .problem import *  # noqa
from .training_job import *  # noqa

sa.orm.configure_mappers()
