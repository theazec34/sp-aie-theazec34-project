# Brasaland Digital — FastAPI API (services/api) with uv + hot reload
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Official uv installer
COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /usr/local/bin/uv

WORKDIR /app/api
COPY api/requirements.txt ./requirements.txt
RUN uv pip install --system -r requirements.txt

COPY api/ ./
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/api

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
