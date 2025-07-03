FROM python:3.13-alpine AS builder

WORKDIR /app

# Install dependencies
COPY pyproject.toml uv.lock ./
COPY --from=uv /uv /uv

RUN /uv sync --no-dev


# Final image
FROM python:3.13-alpine

WORKDIR /app

# Copy virtual environment
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application
COPY sorti/ .

CMD ["python", "main.py"]
