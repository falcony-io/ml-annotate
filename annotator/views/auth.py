from annotator import app
from flask_login import current_user, login_required, login_user, logout_user
from wtforms.fields import PasswordField, TextField
from flask import (
    render_template,
    url_for,
    redirect,
    request,
    flash
)
from annotator.models import Problem, User
from flask_wtf import Form


class LoginForm(Form):
    username = TextField('Username')
    password = PasswordField('Password')


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
