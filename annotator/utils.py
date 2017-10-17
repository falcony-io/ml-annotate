from flask import abort
from flask_login import current_user


def assert_rights_to_problem(problem):
    if not problem:
        abort(404)
    if not current_user.can_access_problem(problem):
        abort(403)
