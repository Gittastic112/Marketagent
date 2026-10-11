FROM python:3.14-slim AS dependencies

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace/backend

WORKDIR /workspace

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip==26.2.1 && pip install --no-cache-dir -r backend/requirements.txt

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
COPY backend/requirements-test.txt backend/requirements-test.txt
RUN pip install --no-cache-dir -r backend/requirements-test.txt
COPY backend/tests backend/tests
USER appuser

FROM test AS tools

USER root
# Repository/recovery checks need Git and shasum, not application runtime code.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git perl \
    && rm -rf /var/lib/apt/lists/*
USER appuser

# Keep the default build free of pytest and backend test fixtures.
FROM application AS runtime
