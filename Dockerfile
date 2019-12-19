FROM python:3.7-stretch

RUN curl -sL https://deb.nodesource.com/setup_12.x | bash - && \
    curl -sL https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - && \
    echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    nodejs \
    yarn \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pipenv

WORKDIR /app
COPY Pipfile* /app/
RUN pipenv install

COPY . /app/

RUN yarn install --frozen-lockfile

EXPOSE 5000

CMD ["pipenv", "run", "start"]
