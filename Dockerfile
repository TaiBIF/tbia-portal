FROM python:3.8-slim-buster

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    # dependencies for building Python packages
    && apt-get install -y build-essential \
    # tools
    && apt-get install -y curl \
    # psycopg2 dependencies
    # && apt-get install -y libpq-dev \
    # Translations dependencies
    #&& apt-get install -y gettext \
    # cleaning up unused files
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*


# timezone to Asia/Taipei
RUN ln -sf /usr/share/zoneinfo/Asia/Taipei /etc/localtime
RUN echo "Asia/Taipei" > /etc/timezone
ENV TZ=Asia/Taipei


# install python package
#RUN pip install --upgrade pip
#RUN pip install --no-cache-dir pipenv
#COPY Pipfile Pipfile.lock ./
#RUN pipenv install --dev --ignore-pipfile --system

WORKDIR /code

# Install Poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy using poetry.lock* in case it doesn't exist yet
COPY ./pyproject.toml ./poetry.lock* /code/

RUN poetry install --no-root --no-dev


COPY ./scripts/entrypoint /srv/entrypoint
RUN sed -i 's/\r$//g' /srv/entrypoint
RUN chmod +x /srv/entrypoint

COPY ./scripts/start /srv/start
RUN sed -i 's/\r$//g' /srv/start
RUN chmod +x /srv/start

COPY ./scripts/wait-for-it.sh /srv/wait-for-it.sh
RUN sed -i 's/\r$//g' /srv/wait-for-it.sh
RUN chmod +x /srv/wait-for-it.sh

COPY ./scripts/docker-web-entry.sh /srv/docker-web-entry.sh
RUN sed -i 's/\r$//g' /srv/docker-web-entry.sh
RUN chmod +x /srv/docker-web-entry.sh

ENTRYPOINT ["/srv/entrypoint"]
