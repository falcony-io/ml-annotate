from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy_utils import PasswordType, UUIDType

from annotator.extensions import db


class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(
        UUIDType(binary=False),
        server_default=db.func.uuid_generate_v4(),
        primary_key=True
    )

    username = db.Column(
        db.Unicode(255),
        nullable=False,
        unique=True,
        index=True
    )

    password = db.Column(
        PasswordType(
            schemes=['pbkdf2_sha512']
        ),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        nullable=False
    )

    is_superuser = db.Column(
        db.Boolean(),
        nullable=False,
        default=False,
        server_default='FALSE'
    )

    @hybrid_method
    def can_access_problem(self, problem):
        from annotator.models import UserProblem

        return self.is_superuser or db.session.query(UserProblem.id).filter(
            UserProblem.user_id == self.id,
            UserProblem.problem_id == problem.id
        ).count() > 0

    @can_access_problem.expression
    def can_access_problem(cls, problem):
        from annotator.models import Problem, UserProblem

        return cls.is_superuser | Problem.id.in_(
            db.session.query(UserProblem.problem_id).filter(
                UserProblem.user_id == cls.id
            )
        )

    def __repr__(self):
        return '<User username=%r>' % self.username
