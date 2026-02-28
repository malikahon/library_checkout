# =============================================================================
# Stage 1 — Builder
# Install Python dependencies into an isolated prefix so the runtime stage
# can copy only the installed packages, leaving build tools behind.
# =============================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build-time system deps (gcc + libpq headers for psycopg2-binary).
# Cleaned up in the same layer to avoid bloating this stage's cache.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements BEFORE source code to maximise layer-cache hits.
# Only re-runs pip install when requirements.txt changes.
COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# =============================================================================
# Stage 2 — Runtime
# Lean image: only the app, its installed deps, and the PostgreSQL client lib.
# =============================================================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime-only system dep: PostgreSQL client library (needed by psycopg2-binary).
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage.
COPY --from=builder /install /usr/local

# Create a non-root system user and group before copying application code.
RUN addgroup --system app && adduser --system --ingroup app --no-create-home app

# Copy application source (filtered by .dockerignore).
COPY . .

# Run collectstatic at build time so the image contains static assets.
# The entrypoint also runs collectstatic to populate the shared named volume.
RUN SECRET_KEY=build-placeholder python manage.py collectstatic --noinput

# Hand ownership of the app directory to the non-root user.
RUN chown -R app:app /app

# Make entrypoint executable.
RUN chmod +x /app/entrypoint.sh

# Drop to non-root user for all subsequent commands and at container runtime.
USER app

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
