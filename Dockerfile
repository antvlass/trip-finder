# Stage 1: Builder
FROM python:3.14-slim AS builder

ARG POETRY_VERSION=2.1.4

WORKDIR /app

# Install Poetry and upgrade pip
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry==${POETRY_VERSION}

# Configure Poetry to not create virtual environments
RUN poetry config virtualenvs.create false

# Copy dependency files first for better layer caching
COPY poetry.lock pyproject.toml ./

# Install dependencies (production only)
RUN poetry install --no-interaction --no-ansi --no-root --only main

# Stage 2: Runtime
FROM python:3.14-slim

# Create non-root user
RUN groupadd -r django && useradd -r -g django django

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=django:django . .

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media && \
    chown -R django:django /app

# Switch to non-root user
USER django

# Collect static files
RUN python manage.py collectstatic --noinput || echo "No static files to collect"

# Expose port
EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
