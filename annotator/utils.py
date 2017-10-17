from flask import abort
from flask_login import current_user


def assert_rights_to_problem(problem):
    assert problem
    if not current_user.can_access_problem(problem):
        abort(403)
