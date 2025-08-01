FROM ghcr.io/astral-sh/uv:latest AS uv
FROM alpine AS builder
ENV PATH="/app/.venv/bin:$PATH"

ARG UID=10001
RUN adduser -D -H -h /app -u "${UID}" appuser

USER appuser
WORKDIR /app

# Install dependencies
COPY --chown=${UID} pyproject.toml uv.lock ./
COPY --from=uv /uv /usr/local/bin/uv

RUN uv sync --no-dev --frozen

# Copy application
COPY sorti/ .

CMD ["uv", "run", "main.py"]
