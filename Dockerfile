# stage 1 — builder
# install Python dependencies into an isolated prefix so the runtime stage
# can copy only the installed packages, leaving build tools behind.
FROM python:3.12-slim AS builder

WORKDIR /build

# install build-time system deps (gcc + libpq headers for psycopg2-binary).
# cleaned up in the same layer to avoid bloating this stage's cache.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# copy requirements BEFORE source code to maximise layer-cache hits.
# only re-runs pip install when requirements.txt changes.
COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# stage 2 — Runtime
# lean image: only the app, its installed deps, and the PostgreSQL client lib
FROM python:3.12-slim AS runtime

WORKDIR /app

# runtime-only system dep: PostgreSQL client library (needed by psycopg2-binary)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# create a non-root system user and group before copying application code
RUN addgroup --system app && adduser --system --ingroup app --no-create-home app

# copy application source (filtered by .dockerignore)
COPY . .

# run collectstatic at build time so the image contains static assets
# the entrypoint also runs collectstatic to populate the shared named volume
RUN SECRET_KEY=build-placeholder python manage.py collectstatic --noinput

# hand ownership of the app directory to the non-root user
RUN chown -R app:app /app

# make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# drop to non-root user for all subsequent commands and at container runtime.
USER app

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
