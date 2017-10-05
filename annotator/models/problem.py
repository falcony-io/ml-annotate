from flask_login import current_user
from flask_sqlalchemy import BaseQuery
from sqlalchemy import select, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import object_session
from sqlalchemy_utils import (
    UUIDType
)

from annotator.extensions import db


class ProblemQuery(BaseQuery):
    def for_user(self, user):
        from annotator.models import User
        return self.filter(User.can_access_problem(self), User.id == current_user.id)


class Problem(db.Model):
    __tablename__ = 'problem'
    query_class = ProblemQuery

    id = db.Column(
        UUIDType(binary=False),
        server_default=db.func.uuid_generate_v4(),
        primary_key=True
    )

    name = db.Column(
        db.Unicode(255),
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        nullable=False
    )

    @hybrid_property
    def dataset_count(self):
        from annotator.models import Dataset

        return object_session(self).query(Dataset).filter(Dataset.problem == self).count()

    @dataset_count.expression
    def dataset_count(cls):
        from annotator.models import Dataset

        return select([func.count(Dataset.id)]).where(Dataset.problem_id == cls.id).label('dataset_count')

    def __repr__(self):
        return '<Problem name=%r>' % self.name
