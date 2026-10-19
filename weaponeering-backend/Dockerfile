FROM python:3.12-slim

RUN sed -i \
    -e 's|http://deb.debian.org/debian-security|http://security.debian.org/debian-security|g' \
    -e 's|http://deb.debian.org/debian|http://mirror.ku.ac.th/debian|g' \
    /etc/apt/sources.list.d/debian.sources

ARG APP_VERSION=dev-local
ARG GIT_COMMIT=unknown
ARG GIT_BRANCH=unknown
ARG BUILD_DATE=unknown
ARG BUILD_NUMBER=0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    APP_HOME=/app \
    PYTHONPATH=/app/src \
    APP_VERSION=${APP_VERSION} \
    GIT_COMMIT=${GIT_COMMIT} \
    GIT_BRANCH=${GIT_BRANCH} \
    BUILD_DATE=${BUILD_DATE} \
    BUILD_NUMBER=${BUILD_NUMBER}

WORKDIR $APP_HOME

RUN apt-get update -o Acquire::Retries=3 \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-api.txt $APP_HOME/requirements-api.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements-api.txt

COPY alembic.ini $APP_HOME/alembic.ini
COPY alembic $APP_HOME/alembic
COPY src $APP_HOME/src
COPY entrypoint.sh $APP_HOME/entrypoint.sh
RUN chmod +x $APP_HOME/entrypoint.sh

EXPOSE 8000

CMD ["./entrypoint.sh"]
