ML-Annotate
===============

You can use ML-Annotate to label text data for machine learning purposes. ML-Annotate supports binary, multi-label and multi-class labeling.

.. image:: http://i.imgur.com/JMVU6Ym.png

Running locally
-----------

ML-Annotate requires Python 3.5 or later.

1. Create neccessary virtualenv for ML-Annotate and install all packages::

    virtualenv --python python3 .virtualenv
    source .virtualenv/bin/activate
    pip install -r requirements.txt

2. Setup .env with all neccessary enviroment variables::

    echo "source .virtualenv/bin/activate" >> .env
    echo "export FLASK_APP=annotator/app.py" >> .env
    echo "export DATABASE_URL=postgres://localhost/annotator" >> .env
    echo "export FLASK_DEBUG=1" >> .env
    source .env

3. Create database. This requires you to have PostgreSQL installed so you should have command line tools such as createdb::

    .virtualenv/bin/flask resetdb
    .virtualenv/bin/flask add-user admin password

4. Normally you would want to import your data at this point. We have included a test script to make up some data for testing purposes::

    .virtualenv/bin/flask import_fake_data

5. Run the app::

    .virtualenv/bin/flask run


Adding data
-----------

ML-Annotate includes iPython shell for inserting data. Start by running::

    flask shell

Then you will have access to the application shell. Here's an example on how to add data from Project Gutenberg::

    import requests
    request = requests.get('https://www.gutenberg.org/files/1342/1342-0.txt')
    text_contents = max(request.text.split('***'), key=lambda x: len(x))
    paragraphs = [
        x.strip() for x in text_contents.replace('\r', '').split('\n\n')
        if x.strip()
    ]
    new_problem = Problem(
        name='Example',
        labels=[ProblemLabel(label='Example', order_index=1)],
        # supported types: binary, multi-label, multi-class
        # add more labels if using other labels.
        classification_type='binary'
    )
    for i, paragraph in enumerate(paragraphs):
        db.session.add(Dataset(
            table_name='gutenberg.pride_and_prejudice_by_jane_austen',
            entity_id='paragraph%i' % i,
            problem=new_problem,
            free_text=paragraph
        ))
    db.session.commit()


Deploying to Heroku
-----------

This guide expects that you are deploying ML-Annotate to Heroku.

1. Create new Heroku application.
2. Set up the Heroku application Git remotes and push the application to production::

    git remote add production git@heroku.com:APP_NAME_HERE.git
    git push production

3. Setup configuration::

    heroku addons:create heroku-postgresql:hobby-dev --app APP_NAME_HERE
    heroku config:set SECRET_KEY=$(python3 -c 'import binascii, os; print(binascii.hexlify(os.urandom(24)).decode())') --app APP_NAME_HERE
    heroku config:set FLASK_APP=annotator/app.py --app APP_NAME_HERE
    heroku buildpacks:add --index 1 heroku/nodejs --app APP_NAME_HERE
    heroku buildpacks:add --index 2 https://github.com/philippkueng/heroku-buildpack-sassc.git --app APP_NAME_HERE
    heroku buildpacks:add --index 3 heroku/python --app APP_NAME_HERE

4. Then create the tables and create the user::

    heroku run "flask createtables" --app APP_NAME_HERE
    heroku run "flask add_user admin password" --app APP_NAME_HERE

5. You should be able to access your instance of ML-Annotate now by going to *YOUR_APP_NAME.herokuapp.com*. Username is *admin* and the password is the one you set previously (yoursupersecretpassword).


Users
-----------

You can add admin users with the command::

    flask add_user username password

If you need to add more specific permissions, you can use **flask shell**::

    flask shell
    u = User(username='username', password='password')
    db.session.add(u)
    db.session.add(UserProblem(user=u, problem=Problem.query.get('PROBLEM_ID')))
    db.session.commit()


Making modifications
-----------

It's very likely that this application does not fit your needs perfectly and you need to make some modifications. If you need to extend any models, you can do so and generate migration with the following command::


    alembic revision --autogenerate -m 'Add column'

Then you can run the migration locally with `alembic upgrade head`. The migration is run automatically on Heroku when you deploy.

