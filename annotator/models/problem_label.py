from sqlalchemy_utils import UUIDType

from annotator.extensions import db
from annotator.models import Problem


class ProblemLabel(db.Model):
    __tablename__ = 'problem_label'

    id = db.Column(
        UUIDType(binary=False),
        server_default=db.func.uuid_generate_v4(),
        primary_key=True
    )

    problem_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey(Problem.id),
        nullable=False,
    )

    problem = db.relationship(Problem, backref='labels')

    label = db.Column(
        db.Unicode(255),
        nullable=False,
    )

    order_index = db.Column(
        db.Integer,
        nullable=False,
    )

    def __repr__(self):
        return '<Problemlabel label=%r>' % (self.label,)
