from sqlalchemy_utils import (
    UUIDType
)

from annotator.models.problem import Problem
from annotator.extensions import db


class TrainingJob(db.Model):
    __tablename__ = 'training_job'

    id = db.Column(
        UUIDType(binary=False),
        server_default=db.func.uuid_generate_v4(),
        primary_key=True
    )

    accuracy = db.Column(
        db.Float(),
        nullable=False
    )

    problem_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey(Problem.id, ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    problem = db.relationship(Problem, backref='training_jobs')

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        nullable=False
    )

    def __repr__(self):
        return '<TrainingJob problem=%r>' % self.problem.id
