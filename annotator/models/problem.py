from sqlalchemy_utils import (
    UUIDType
)

from annotator.extensions import db


class Problem(db.Model):
    __tablename__ = 'problem'

    id = db.Column(
        UUIDType(binary=False),
        server_default=db.func.uuid_generate_v4(),
        primary_key=True
    )

    label = db.Column(
        db.Unicode(255),
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        nullable=False
    )
