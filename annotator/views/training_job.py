from flask import render_template
from flask_login import login_required

from annotator import app
from annotator.extensions import db
from annotator.models import Problem, TrainingJob
from annotator.utils import assert_rights_to_problem


@app.route('/<uuid:problem_id>/training_job')
@login_required
def training_job(problem_id):
    problem = Problem.query.get(problem_id)
    assert_rights_to_problem(problem)

    data = (
        db.session.query(
            TrainingJob.id,
            TrainingJob.accuracy,
            TrainingJob.created_at
        )
        .filter(TrainingJob.problem_id == problem.id)
        .order_by(TrainingJob.created_at.desc())
        .all()
    )
    plot_data = (
        db.session.query(
            db.func.to_char(
                TrainingJob.created_at,
                db.text("'YYYY-MM-DD HH24:MI:SS'")
            ),
            TrainingJob.accuracy,
        )
        .filter(TrainingJob.problem_id == problem.id)
        .order_by(TrainingJob.created_at.asc())
        .all()
    )
    return render_template(
        'training_job.html',
        data=data,
        plot_data=plot_data,
        problem=problem
    )
