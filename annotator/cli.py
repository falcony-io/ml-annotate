import click
import requests
from sh import createdb, dropdb, psql
from .app import app
from .extensions import db
from .models import User, Problem, ProblemLabel, Dataset


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
    new_problem = Problem(
        name='Example',
        labels=[ProblemLabel(label='Example', order_index=1)]
    )
    for i, paragraph in enumerate(paragraphs):
        db.session.add(Dataset(
            table_name='gutenberg.pride_and_prejudice_by_jane_austen',
            entity_id='paragraph%i' % i,
            problem=new_problem,
            free_text=paragraph
        ))
    db.session.commit()
    print('Inserted %i rows' % len(paragraphs))


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
