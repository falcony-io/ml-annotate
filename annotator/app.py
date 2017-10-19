import os
import shutil
import sys

from flask import Flask, render_template
from flask_assets import Bundle, Environment
from flask_debugtoolbar import DebugToolbarExtension
from flask_sslify import SSLify
from raven.contrib.flask import Sentry
from webassets.exceptions import FilterError
from webassets.filter import get_filter, register_filter
from webassets_webpack import Webpack

from .extensions import db, login_manager


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

if not app.debug:
    app.config['ASSETS_DEBUG'] = False

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

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SQLALCHEMY_RECORD_QUERIES'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgres://localhost/annotator'
)
app.config['BABEL_BIN'] = 'node_modules/babel-cli/bin/babel.js'
app.config['BROWSERIFY_BIN'] = 'node_modules/browserify/bin/cmd.js'
app.config['WEBPACK_BIN'] = 'node_modules/.bin/webpack'

app.config['WEBPACK_CONFIG'] = (
    'webpack.config.js' if app.debug else 'webpack.production.js'
)

app.config['WEBPACK_TEMP'] = 'temp.js'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'development')

toolbar = DebugToolbarExtension(app)
app.shell_context_processor(shell_context)
sslify = SSLify(app)
db.init_app(app)
login_manager.init_app(app)
if os.environ.get('SENTRY_DSN'):
    sentry = Sentry(app, dsn=os.environ.get('SENTRY_DSN'))

assert app.debug or os.environ.get('SECRET_KEY'), (
    'Should run in debug mode or should have SECRET_KEY set'
)
assert sys.version_info >= (3, 4), (
    'Should run with Python 3.4 or later.'
)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


@app.before_first_request
def copy_bootstrap_fonts():
    files = [
        'glyphicons-halflings-regular.eot',
        'glyphicons-halflings-regular.ttf',
        'glyphicons-halflings-regular.woff2',
        'glyphicons-halflings-regular.svg',
        'glyphicons-halflings-regular.woff',
    ]
    for file in files:
        shutil.copyfile(
            'node_modules/bootstrap/fonts/%s' % file,
            'annotator/static/fonts/%s' % file
        )


@login_manager.user_loader
def load_user(user_id):
    from annotator.models import User

    return User.query.get(user_id)


if app.debug:
    @app.errorhandler(FilterError)
    def handle_error(error):
        import html

        return '''
        <h1>Error</h1>
        %s
        ''' % (
            html.escape(error.args[0].split('stdout=b\'')[1]).replace("\\n", "<br>")
        )
