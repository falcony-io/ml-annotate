from sqlalchemy_utils import UUIDType

from annotator.extensions import db
from annotator.models import Problem, User


class UserProblem(db.Model):
    __tablename__ = 'user_problem'

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

    problem = db.relationship(Problem)

    user_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey(User.id),
        nullable=False,
        index=True
    )

    user = db.relationship(User, backref='problems')

    def __repr__(self):
        return '<UserProblem problem=%r user=%r>' % (
            self.problem.label,
            self.user.username
        )
