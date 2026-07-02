# Dockerfile
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

RUN useradd --create-home app && chown -R app /app
USER app

ENTRYPOINT ["uv", "run", "python", "manage.py"]
CMD ["run_daily"]
