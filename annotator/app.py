import os

import click
import requests
from flask import (
    flash,
    Flask,
    redirect,
    render_template,
    request,
    url_for,
    Response,
)
from functools import wraps
from flask_sslify import SSLify
from sh import createdb, dropdb, psql

from .extensions import db
from .models import Dataset, LabelEvent, Problem, TrainingJob


def shell_context():
    import annotator.models
    vars = {
        'db': db
    }
    for key in dir(annotator.models):
        if key[0].isupper():
            vars[key] = getattr(annotator.models, key)
    return vars


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgres://localhost/annotator'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'development')
app.shell_context_processor(shell_context)
sslify = SSLify(app)
db.init_app(app)
app.config['PASSWORD'] = os.environ.get('PASSWORD', '')


assert app.debug or len(app.config['PASSWORD']) >= 5, (
    'Should run in debug mode or should have PASSWORD set'
)
assert app.debug or os.environ.get('SECRET_KEY'), (
    'Should run in debug mode or should have SECRET_KEY set'
)


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == app.config['PASSWORD']


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if app.config['PASSWORD']:
            auth = request.authorization
            if not auth or not check_auth(auth.username, auth.password):
                return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route('/')
@requires_auth
def index():
    return render_template(
        'select_problem.html',
        problems=Problem.query.order_by(Problem.created_at).all()
    )


@app.route('/<uuid:problem_id>/label_event')
@requires_auth
def label_event(problem_id):
    problem = Problem.query.get(problem_id)
    data = (
        db.session.query(
            LabelEvent.id,
            LabelEvent.label_matches,
            Dataset.free_text,
            Dataset.probability,
        )
        .outerjoin(LabelEvent.data)
        .filter(Dataset.problem_id == problem.id)
        .order_by(LabelEvent.created_at.desc())
        .all()
    )
    return render_template(
        'label_event.html',
        data=data,
        problem=problem
    )


@app.route('/<uuid:problem_id>/dataset')
@requires_auth
def dataset(problem_id):
    problem = Problem.query.get(problem_id)
    data = (
        db.session.query(
            Dataset.id,
            Dataset.free_text,
            Dataset.entity_id,
            Dataset.table_name,
            Dataset.probability,
            Dataset.sort_value,
        )
        .filter(Dataset.problem_id == problem.id)
        .order_by(Dataset.id.asc())
        .all()
    )
    return render_template(
        'dataset.html',
        data=data,
        problem=problem
    )


@app.route('/<uuid:problem_id>/training_job')
@requires_auth
def training_job(problem_id):
    problem = Problem.query.get(problem_id)
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
    return render_template(
        'training_job.html',
        data=data,
        problem=problem
    )


@app.route('/<uuid:problem_id>/train', methods=['GET', 'POST'])
@requires_auth
def train(problem_id):
    problem = Problem.query.get(problem_id)

    if not Dataset.query.filter(Dataset.problem_id == problem.id).count():
        return render_template('train_no_data.html', problem=problem)

    if request.method == 'POST':
        if LabelEvent.query.filter_by(
            label=request.form['label'],
            data=Dataset.query.get(request.form['data_id'])
        ).count():
            flash('This item has already been labeled...skipping?')
        else:
            label_event = LabelEvent(
                label=request.form['label'],
                label_matches={
                    'yes': True,
                    'no': False,
                    'skip': None
                }[request.form['label_matches']],
                data=Dataset.query.get(request.form['data_id'])
            )
            db.session.add(label_event)
            db.session.commit()

    sample = Dataset.query.filter(
        ~Dataset.label_events.any(),
        Dataset.problem_id == problem.id
    ).order_by(Dataset.sort_value, db.func.RANDOM()).first()
    labeled_data_count = Dataset.query.filter(
        Dataset.label_events.any(),
        Dataset.problem_id == problem.id
    ).count()
    progress = (
        labeled_data_count /
        Dataset.query.filter(Dataset.problem_id == problem.id).count()
    )
    return render_template(
        'train.html',
        sample=sample,
        label=problem.label,
        event_log=LabelEvent.query.join(
            Dataset
        ).filter(
            Dataset.problem_id == problem.id
        ).order_by(
            LabelEvent.created_at.desc()
        ).limit(10),
        progress=progress,
        labeled_data_count=labeled_data_count,
        training_job_count=TrainingJob.query.count(),
        training_jobs=TrainingJob.query.filter(
            TrainingJob.problem_id == problem.id
        ).order_by(
            TrainingJob.created_at.desc()
        ).limit(5),
        problem=problem
    )


@app.route('/<uuid:problem_id>/delete_label_event/<uuid:id>', methods=['POST'])
@requires_auth
def delete_label_event(problem_id, id):
    label_event = LabelEvent.query.get(id)
    if label_event:
        db.session.delete(label_event)
        db.session.commit()
        flash('Label event removed.')
    return redirect(url_for('train', problem_id=problem_id))


@app.cli.command()
def resetdb():
    """Create the tables."""
    import annotator.models  # noqa

    click.echo('Resetting database...')

    query = '''
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = '{}'
    '''.format(db.engine.url.database)
    psql('--command', query)
    dropdb('--if-exists', db.engine.url.database)
    createdb(db.engine.url.database)
    _createtables()


@app.cli.command()
def createtables():
    _createtables()


def _createtables():
    db.init_app(app)

    db.engine.execute('''CREATE EXTENSION IF NOT EXISTS "uuid-ossp";''')
    db.create_all()
    db.session.commit()

    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config('alembic.ini')
    command.stamp(alembic_cfg, 'head')


@app.cli.command()
def import_fake_data():
    request = requests.get('https://www.gutenberg.org/files/1342/1342-0.txt')
    text_contents = max(request.text.split('***'), key=lambda x: len(x))
    paragraphs = [
        x.strip() for x in text_contents.replace('\r', '').split('\n\n')
        if x.strip()
    ]
    new_problem = Problem(label='Example')
    for i, paragraph in enumerate(paragraphs):
        db.session.add(Dataset(
            table_name='gutenberg.pride_and_prejudice_by_jane_austen',
            entity_id='paragraph%i' % i,
            problem=new_problem,
            free_text=paragraph,
            organization_id=None
        ))
    db.session.commit()
    print('Inserted %i rows' % len(paragraphs))
