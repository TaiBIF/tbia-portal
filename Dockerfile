FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

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
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

RUN curl -o /usr/local/bin/aws_signing_helper https://rolesanywhere.amazonaws.com/releases/1.1.1/X86_64/Linux/aws_signing_helper \
    && chmod +x /usr/local/bin/aws_signing_helper

# timezone to Asia/Taipei
RUN ln -sf /usr/share/zoneinfo/Asia/Taipei /etc/localtime
RUN echo "Asia/Taipei" > /etc/timezone
ENV TZ=Asia/Taipei

WORKDIR /code

# Python packages
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Package
COPY requirements requirements
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements/base.txt

COPY ./scripts/entrypoint /srv/entrypoint
RUN sed -i 's/\r$//g' /srv/entrypoint
RUN chmod +x /srv/entrypoint

COPY ./scripts/start /srv/start
RUN sed -i 's/\r$//g' /srv/start
RUN chmod +x /srv/start

ENTRYPOINT ["/srv/entrypoint"]
