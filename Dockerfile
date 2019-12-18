FROM python:3.7-stretch

RUN pip install --no-cache-dir pipenv

WORKDIR /app
COPY Pipfile* /app/
RUN pipenv install

COPY * /app

EXPOSE 5000

CMD ["pipenv", "run", "start"]