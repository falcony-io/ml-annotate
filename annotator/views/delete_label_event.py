from flask import flash, redirect, request, url_for
from flask_login import login_required

from annotator import app
from annotator.extensions import db
from annotator.models import Dataset, LabelEvent, ProblemLabel
from annotator.utils import assert_rights_to_problem


@app.route(
    '/<uuid:problem_id>/multi_class_delete_label_event/<uuid:data_id>',
    methods=['POST']
)
@login_required
def multi_class_delete_label_event(problem_id, data_id):
    data = Dataset.query.get(data_id)
    assert_rights_to_problem(data.problem)
    problem_labels = data.problem.labels
    label_id = request.form.get('label_id')
    selected_label = ProblemLabel.query.get(label_id) if label_id else None

    for x in data.label_events:
        db.session.delete(x)

    for label in problem_labels:
        db.session.add(LabelEvent(
            data=data,
            label=label,
            label_matches=True if label == selected_label else None
        ))
    db.session.commit()

    if selected_label:
        flash('Label event replaced with %s' % selected_label.label)
    else:
        flash('Label events removed')

    return redirect(url_for('train', problem_id=problem_id))


@app.route('/<uuid:problem_id>/delete_label_event/<uuid:id>', methods=['POST'])
@login_required
def delete_label_event(problem_id, id):
    problem = Problem.query.get(problem_id)
    assert_rights_to_problem(problem)

    label_event = LabelEvent.query.get(id)
    value = request.form.get('value')
    if label_event:
        if value:
            db.session.add(LabelEvent(
                data=label_event.data,
                label=label_event.label,
                label_matches={
                    'true': True,
                    'false': False,
                    'skip': None
                }[value]
            ))
        db.session.delete(label_event)
        db.session.commit()
        if value:
            flash('Label event replaced with %s' % value)
        else:
            flash('Label event removed.')
    return redirect(url_for('train', problem_id=problem_id))
