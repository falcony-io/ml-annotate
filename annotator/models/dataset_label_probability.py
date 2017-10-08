from sqlalchemy_utils import UUIDType

from annotator.extensions import db
from annotator.models import Dataset


class DatasetLabelProbability(db.Model):
    __tablename__ = 'dataset_label_probability'

    id = db.Column(
        UUIDType(binary=False),
        server_default=db.func.uuid_generate_v4(),
        primary_key=True
    )

    data_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey(Dataset.id, ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    data = db.relationship(Dataset, backref='probabilities')

    label_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey('problem_label.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    label = db.relationship(
        'ProblemLabel'
    )

    probability = db.Column(
        db.Float(),
        nullable=True
    )

    __table_args__ = (
        db.CheckConstraint(
            (0 <= probability) & (probability <= 1),
            name='chk_dataset_probability'
        ),
        db.UniqueConstraint(
            'data_id', 'label_id', name='uq_dataset_label_probability_data_id_label_id'
        ),
    )

    def __repr__(self):
        return '<Problemlabel label=%r>' % (self.label,)
