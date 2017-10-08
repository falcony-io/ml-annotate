import os

import click
import requests
import sys
from flask import (
    flash,
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
    abort
)
from flask_assets import Environment, Bundle
from flask_login import current_user, login_required, login_user, logout_user
from flask_sslify import SSLify
from sh import createdb, dropdb, psql
from wtforms.fields import PasswordField, TextField
from flask_wtf import Form
from webassets.filter import get_filter, register_filter
from webassets_webpack import Webpack

from .extensions import db, login_manager
from .models import Dataset, DatasetLabelProbability, LabelEvent, Problem, ProblemLabel, TrainingJob, User


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
assets = Environment(app)
assets.init_app(app)
css = Bundle('styles/styles.scss', filters='libsass', output='gen/all.css')
assets.register('css_all', css)

register_filter(Webpack)
react = get_filter('babel', presets='react-es2015')
js = Bundle(
    'js/index.js',
    filters='webpack',
    output='bundle.js',
    depends='js/**.js'
)
assets.register('js_all', js)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgres://localhost/annotator'
)
app.config['BABEL_BIN'] = '/Users/bansku/Documents/ai-trainer/node_modules/babel-cli/bin/babel.js'
app.config['BROWSERIFY_BIN'] = 'node_modules/browserify/bin/cmd.js'
app.config['WEBPACK_BIN'] = 'node_modules/.bin/webpack'
app.config['WEBPACK_CONFIG'] = 'webpack.config.js'
app.config['WEBPACK_TEMP'] = 'temp.js'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'development')
app.shell_context_processor(shell_context)
sslify = SSLify(app)
db.init_app(app)
login_manager.init_app(app)


class LoginForm(Form):
    username = TextField('Username')
    password = PasswordField('Password')


assert app.debug or os.environ.get('SECRET_KEY'), (
    'Should run in debug mode or should have SECRET_KEY set'
)
assert sys.version_info >= (3, 4), (
    'Should run with Python 3.4 or later.'
)


def assert_rights_to_problem(problem):
    print(current_user, problem, current_user.can_access_problem(problem))
    if not current_user.can_access_problem(problem):
        print(current_user, problem, current_user.can_access_problem(problem))
        abort(403)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/')
@login_required
def index():
    print(current_user)
    return render_template(
        'select_problem.html',
        problems=Problem.query.for_user(current_user).order_by(
            Problem.created_at
        ).all(),
        are_there_problems=Problem.query.count() > 0,
        users=User.query
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        user = User.query.filter(User.username == form.username.data).first()
        if (
            user and
            user.password == form.password.data
        ):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Username or password wrong')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/<uuid:problem_id>/batch_label', methods=['POST'])
def batch_label(problem_id):
    problem = Problem.query.get(problem_id)
    assert_rights_to_problem(problem)
    data = request.get_json()
    ids = [str(x) for x in data['selectedIds']]
    if not ids:
        return jsonify(error='No ids selected');

    labels = (
        db.session.query(LabelEvent.id)
        .outerjoin(LabelEvent.data).filter(
            Dataset.id.in_(ids),
            Dataset.problem_id == problem.id,
            LabelEvent.label_id == data['label']
        )
        .all()
    )
    if labels:
        LabelEvent.query.filter(
            LabelEvent.id.in_([x[0] for x in labels])
        ).delete(synchronize_session='fetch')

    if data['value'] != 'undo':
        for dataset_id in ids:
            db.session.add(LabelEvent(
                label_id=data['label'],
                label_matches=data['value'],
                data_id=dataset_id
            ))

    db.session.commit()
    return jsonify(status='ok', labels_removed=len(labels));


@app.route('/<uuid:problem_id>/dataset')
@login_required
def dataset(problem_id):
    problem = Problem.query.get(problem_id)
    assert_rights_to_problem(problem)

    probabilities = db.select(
        [db.func.json_object_agg(
            DatasetLabelProbability.label_id,
            DatasetLabelProbability.probability
        )],
        from_obj=DatasetLabelProbability
    ).where(DatasetLabelProbability.data_id == Dataset.id).correlate(Dataset.__table__).label('dataset_probabilities')

    label_created_at = (
        db.select(
            [db.func.to_char(LabelEvent.created_at, db.text("'YYYY-MM-DD HH24:MI:SS'"))],
            from_obj=LabelEvent
        ).where(LabelEvent.data_id == Dataset.id)
        .order_by(LabelEvent.created_at.desc())
        .limit(1)
        .correlate(Dataset.__table__)
        .label('label_created_at')
    )

    label_matches = db.select(
        [db.func.json_agg(db.func.json_build_array(LabelEvent.label_id, LabelEvent.label_matches))],
        from_obj=LabelEvent
    ).where(LabelEvent.data_id == Dataset.id).correlate(Dataset.__table__).label('label_matches')

    data = (
        db.session.query(
            Dataset.id,
            Dataset.free_text,
            Dataset.entity_id,
            Dataset.table_name,
            Dataset.meta,
            probabilities,
            Dataset.sort_value,
            label_matches,
            label_created_at
        )
        .filter(Dataset.problem_id == problem.id)
        .order_by(Dataset.id.asc())
        .all()
    )
    problem_labels = db.session.query(
        ProblemLabel.id,
        ProblemLabel.label
    ).filter(ProblemLabel.problem == problem).all()


    return render_template(
        'dataset.html',
        data=data,
        problem=problem,
        problem_labels=problem_labels
    )


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
            db.func.to_char(TrainingJob.created_at, db.text("'YYYY-MM-DD HH24:MI:SS'")),
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
        problem=problem,
        problem_labels_arr=[
            dict(id=x.id, name=x.label)
            for x in problem.labels
        ]
    )


@app.route('/<uuid:problem_id>/delete_label_event/<uuid:id>', methods=['POST'])
@login_required
def delete_label_event(problem_id, id):
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
@click.argument('username')
@click.argument('password')
def add_user(username, password):
    db.session.add(User(
        username=username,
        password=password,
        is_superuser=True
    ))
    db.session.commit()
    click.echo('User %s added' % username)


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
            free_text=paragraph
        ))
    db.session.commit()
    print('Inserted %i rows' % len(paragraphs))
