# Brasaland Digital — FastAPI API (services/api) with uv + hot reload
# Build context: monorepo root (see docker-compose.yml) so packages/shared is available.
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /usr/local/bin/uv

# Shared Python package expected at /packages/shared/python
# (app/analyzer.py resolves parents[3]/packages/shared/python from /app/api/app/...)
COPY packages/shared/python /packages/shared/python

WORKDIR /app/api
COPY services/api/requirements.txt ./requirements.txt
RUN uv pip install --system -r requirements.txt

COPY services/api/ ./
COPY services/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/api

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
