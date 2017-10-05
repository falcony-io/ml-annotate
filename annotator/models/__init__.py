import sqlalchemy as sa
from .dataset import *  # noqa
from .dataset_label_probability import *  # noqa
from .label_event import *  # noqa
from .problem import *  # noqa
from .problem_label import *  # noqa
from .training_job import *  # noqa
from .user import *  # noqa
from .user_problem import *  # noqa

sa.orm.configure_mappers()
