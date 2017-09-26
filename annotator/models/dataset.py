from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_utils import (
    UUIDType
)

from annotator.models.problem import Problem
from annotator.extensions import db


class Dataset(db.Model):
    __tablename__ = 'dataset'

    id = db.Column(
        UUIDType(binary=False),
        server_default=db.func.uuid_generate_v4(),
        primary_key=True
    )

    entity_id = db.Column(
        db.Unicode(255),
        index=True
    )

    problem_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey(Problem.id, ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    problem = db.relationship(Problem, backref='dataset')

    table_name = db.Column(
        db.Unicode(255),
        nullable=False,
    )

    free_text = db.Column(
        db.Text(),
        nullable=False
    )

    meta = db.Column(JSONB)

    probability = db.Column(
        db.Float(),
        nullable=True
    )

    sort_value = db.Column(
        db.Float(),
        nullable=True
    )

    __table_args__ = (
        db.UniqueConstraint(
            'table_name',
            'entity_id',
            name='uq_dataset_table_name_entity_id'
        ),
        db.CheckConstraint(
            (0 <= probability) & (probability <= 1),
            name='chk_dataset_probability'
        ),
    )

    def __repr__(self):
        return '<Dataset table_name=%r>' % self.table_name
