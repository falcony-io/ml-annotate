from annotator.app import app
from annotator.utils import assert_rights_to_problem
from flask_login import login_required
from annotator.models import Dataset, Problem, ProblemLabel, LabelEvent
from annotator.extensions import db
from flask import flash, request, render_template
from itertools import groupby


def get_event_log(problem):
    event_groups = db.session.query(
        LabelEvent.data_id,
        db.func.max(LabelEvent.created_at)
    ).join(
        Dataset
    ).filter(
        Dataset.problem_id == problem.id
    ).order_by(
        db.func.max(LabelEvent.created_at).desc()
    ).group_by(LabelEvent.data_id).limit(10)
    event_groups_ids = [x[0] for x in event_groups.all()]

    if not event_groups_ids:
        return []

    data = groupby(
        LabelEvent.query.join(
            Dataset
        ).filter(
            Dataset.problem_id == problem.id,
            LabelEvent.data_id.in_(event_groups_ids)
        ).order_by(
            db.case(
                {uuid: i for i, uuid in enumerate(event_groups_ids)},
                value=LabelEvent.data_id,
                else_=len(event_groups_ids)+1
            )
        ),
        key=lambda x: x.data
    )
    return [
        (a, list(b)) for a, b in data
    ]


@app.route('/<uuid:problem_id>/train_log', methods=['GET', 'POST'])
@login_required
def train_log(problem_id):
    problem = Problem.query.get(problem_id)
    assert_rights_to_problem(problem)
    labeled_data_count = Dataset.query.filter(
        Dataset.label_events.any(),
        Dataset.problem_id == problem.id
    ).group_by(Dataset.id).count()
    progress = (
        labeled_data_count /
        Dataset.query.filter(Dataset.problem_id == problem.id).count()
    )

    return render_template(
        'train_log.html',
        event_log=get_event_log(problem),
        progress=progress,
        labeled_data_count=labeled_data_count,
        problem=problem,
        problem_labels_arr=[
            dict(id=x.id, name=x.label, order_index=x.order_index)
            for x in sorted(problem.labels, key=lambda x: x.order_index)
        ]
    )


@app.route('/<uuid:problem_id>/train', methods=['GET', 'POST'])
@login_required
def train(problem_id):
    problem = Problem.query.get(problem_id)
    assert_rights_to_problem(problem)

    if not Dataset.query.filter(Dataset.problem_id == problem.id).count():
        return render_template('train_no_data.html', problem=problem)

    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('label_'):
                label_id = key.split('label_')[1]
                label = ProblemLabel.query.get(label_id)

                if LabelEvent.query.filter_by(
                    label=label,
                    data=Dataset.query.get(request.form['data_id'])
                ).count():
                    flash('This item has already been labeled...skipping?')
                else:
                    label_event = LabelEvent(
                        label=label,
                        label_matches={
                            'yes': True,
                            'no': False,
                            'skip': None
                        }[value],
                        data=Dataset.query.get(request.form['data_id'])
                    )
                    db.session.add(label_event)
                    db.session.commit()

    sample = Dataset.query.filter(
        ~Dataset.label_events.any(),
        Dataset.problem_id == problem.id
    ).order_by(Dataset.sort_value, db.func.RANDOM()).first()

    return render_template(
        'train.html',
        sample=sample,
        problem=problem,
        problem_labels_arr=[
            dict(id=x.id, name=x.label, order_index=x.order_index)
            for x in sorted(problem.labels, key=lambda x: x.order_index)
        ]
    )
