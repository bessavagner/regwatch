# Dockerfile
# --- Stage 1: build the SPA ---
FROM node:22-slim AS web
RUN corepack enable
WORKDIR /web
COPY web/package.json web/pnpm-lock.yaml web/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY web/ ./
RUN pnpm run build

# Fail the build if the SPA bundle contains an api/ path that WhiteNoise would
# serve unauthenticated, shadowing the DRF API (WhiteNoise resolves before URL routing).
RUN test ! -e dist/api || (echo "ERROR: SPA build produced dist/api — would shadow the authenticated /api" && exit 1)

# --- Stage 2: the Python app (unchanged runtime; now also carries web-dist) ---
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    DJANGO_SETTINGS_MODULE=config.settings

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY manage.py ./
COPY src/ ./src/
COPY --from=web /web/dist ./web-dist

RUN useradd --create-home app && chown -R app /app
USER app

ENTRYPOINT ["/app/.venv/bin/python", "manage.py"]
CMD ["run_daily"]
