FROM python:3.10-slim-buster

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get -y upgrade \
    # dependencies for building Python packages
    && apt-get install -y build-essential \
    # tools
    && apt-get install -y csvkit \
    && apt-get install -y curl \
    && apt-get install -y zip \
    && apt-get install -y unzip \
    # django i18n
    && apt-get install -y gettext \
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

# Python packages
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Package
COPY requirements requirements
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements/base.txt


# # Install Poetry
# RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
#     cd /usr/local/bin && \
#     ln -s /opt/poetry/bin/poetry && \
#     poetry config virtualenvs.create false

# # Copy using poetry.lock* in case it doesn't exist yet
# COPY ./pyproject.toml ./poetry.lock* /code/

# RUN poetry install --no-root --no-dev

COPY ./scripts/entrypoint /srv/entrypoint
RUN sed -i 's/\r$//g' /srv/entrypoint
RUN chmod +x /srv/entrypoint

COPY ./scripts/start /srv/start
RUN sed -i 's/\r$//g' /srv/start
RUN chmod +x /srv/start

ENTRYPOINT ["/srv/entrypoint"]
