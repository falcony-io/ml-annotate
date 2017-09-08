from sqlalchemy_utils import (
    UUIDType
)

from annotator.extensions import db
from annotator.models import Dataset


class LabelEvent(db.Model):
    __tablename__ = 'label_event'

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

    data = db.relationship(Dataset, backref='label_events')

    label = db.Column(
        db.Unicode(255),
        nullable=False
    )

    label_matches = db.Column(
        db.Boolean(),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        nullable=False
    )

    def __repr__(self):
        return '<LabelEvent label=%r>' % self.label
