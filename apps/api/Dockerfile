# Insight2Listing API container (self-hosted, plan section 19.1).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_NO_CACHE=1 \
    UV_COMPILE_BYTECODE=0 \
    PYTHONPATH=/app/src

WORKDIR /app

# Install uv then resolve dependencies from the lockfile only.
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev

COPY . .

EXPOSE 8100

# Migrations run at startup so a fresh database is provisioned automatically.
# Use the venv binaries directly: `uv run` would re-sync dev dependencies.
CMD ["sh", "-c", ".venv/bin/python -m alembic upgrade head && .venv/bin/python run.py"]