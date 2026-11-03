FROM python:3.14-slim@sha256:44dd04494ee8f3b538294360e7c4b3acb87c8268e4d0a4828a6500b1eff50061 AS dependencies

# Keep OS security fixes reproducible. Advance the snapshot with an audited rebuild.
RUN sed -i 's|http://deb.debian.org/debian-security|https://snapshot.debian.org/archive/debian-security/20261028T000000Z|;s|http://deb.debian.org/debian|https://snapshot.debian.org/archive/debian/20261028T000000Z|' /etc/apt/sources.list.d/debian.sources \
    && apt-get -o APT::Update::Error-Mode=any -o Acquire::Check-Valid-Until=false -o Acquire::Retries=3 update \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace/backend

WORKDIR /workspace

COPY backend/requirements.lock backend/requirements.lock
RUN pip install --no-cache-dir --upgrade pip==26.2.1 && pip install --no-cache-dir --require-hashes -r backend/requirements.lock

RUN useradd --uid 10001 --create-home appuser

FROM dependencies AS application

COPY alembic.ini alembic.ini
COPY pyproject.toml pyproject.toml
COPY backend/app backend/app
COPY backend/alembic backend/alembic
COPY backend/scripts backend/scripts
COPY scripts scripts

USER appuser

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000"]

FROM application AS test

USER root
COPY backend/requirements-test.lock backend/requirements-test.lock
RUN pip install --no-cache-dir --require-hashes -r backend/requirements-test.lock
COPY backend/tests backend/tests
USER appuser

FROM test AS tools

USER root
# Repository/recovery checks need Git and shasum, not application runtime code.
RUN apt-get -o APT::Update::Error-Mode=any -o Acquire::Check-Valid-Until=false update \
    && apt-get install -y --no-install-recommends git perl \
    && rm -rf /var/lib/apt/lists/*
USER appuser

# Keep the default build free of pytest and backend test fixtures.
FROM application AS runtime
