# Library Management System

A full-stack web application for managing a library's book inventory and lending operations. Members can browse the catalogue, check out books, and track their loans, while staff (librarians) have full control over inventory, loans, and user management.

Built as coursework for the Distributed Systems and Cloud Computing (DSCC) module.

---

## Features

**Member (regular user):**
- Browse the book catalogue with availability indicators
- View detailed book information
- Check out available books
- Return checked-out books
- View personal loan history (active and returned)
- Self-service registration

**Staff / Librarian (`is_staff`):**
- Full CRUD management of the book catalogue (add, edit, delete)
- View and filter all loans (all / active / returned)
- Assign loans on behalf of members
- Force-return any active loan
- View all registered members with active loan counts
- Django admin panel access

**Platform:**
- Role-based access control with server-side permission enforcement
- Atomic database operations for checkout/return (prevents race conditions)
- Unique constraint preventing duplicate active loans
- CSRF protection on all forms
- Production-hardened security headers (HSTS, secure cookies, SSL redirect)
- Responsive dark emerald UI theme
- 45 automated tests covering auth, books, loans, forms, staff operations, and permissions

---

## Technologies Used

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Django 6.0.2 |
| Database | PostgreSQL 16 |
| Application Server | Gunicorn |
| Reverse Proxy / TLS | Nginx (Alpine) |
| TLS Certificates | Let's Encrypt via Certbot |
| Containerisation | Docker (multi-stage build), Docker Compose |
| CI/CD | GitHub Actions |
| Testing | pytest, pytest-django |
| Linting | flake8 |

---

## Local Setup Instructions

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed
- Git

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/malikahon/library_checkout.git
   cd library_checkout
   ```

2. **Create a `.env` file** in the project root (or use the provided example):
   ```dotenv
   SECRET_KEY=your-dev-secret-key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1

   DB_NAME=library_db
   DB_USER=library_user
   DB_PASSWORD=library_pass
   DB_HOST=localhost
   DB_PORT=5433
   ```

3. **Start the development stack:**
   ```bash
   docker compose -f docker-compose.dev.yml up --build
   ```
   This starts PostgreSQL and Django's development server with live code reloading.

4. **Access the application** at [http://localhost:8000](http://localhost:8000).

5. **(Optional) Seed sample data:**
   ```bash
   docker compose -f docker-compose.dev.yml exec web python manage.py populate_books
   ```

6. **(Optional) Create a superuser:**
   ```bash
   docker compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
   ```

### Running Tests Locally

```bash
docker compose -f docker-compose.dev.yml exec web pytest -v
```

---

## Deployment Instructions (VPS with Docker Compose)

### Prerequisites

- A VPS (e.g., Ubuntu 22.04+) with Docker installed
- A registered domain with a DNS A record pointing to the server IP
- Ports 80 and 443 open on the firewall

### Steps

1. **SSH into the server and clone the repository:**
   ```bash
   git clone https://github.com/malikahon/library_checkout.git
   cd library_checkout
   ```

2. **Create a production `.env.docker` file:**
   ```dotenv
   SECRET_KEY=<generate-a-strong-random-key>
   DEBUG=False
   ALLOWED_HOSTS=managelibrary.app,www.managelibrary.app,20.24.83.116

   DB_NAME=library_db
   DB_USER=library_user
   DB_PASSWORD=<strong-random-password>
   DB_HOST=db
   DB_PORT=5432

   POSTGRES_DB=library_db
   POSTGRES_USER=library_user
   POSTGRES_PASSWORD=<strong-random-password>
   ```

3. **Update `nginx/nginx.conf`** — replace all occurrences of `managelibrary.app` with your actual domain (already done if using this repo).

4. **Start the production stack:**
   ```bash
   docker compose up -d --build
   ```
   This starts four services: PostgreSQL, Django/Gunicorn, Nginx, and Certbot.

5. **Obtain an SSL certificate (first time):**
   ```bash
   docker compose run --rm certbot certonly \
     --webroot -w /var/www/certbot \
      -d managelibrary.app -d www.managelibrary.app
   docker compose restart nginx
   ```

6. **Run database migrations and create a superuser:**
   ```bash
   docker compose exec web python manage.py migrate --noinput
   docker compose exec web python manage.py createsuperuser
   ```

7. **(Optional) Seed sample data:**
   ```bash
   docker compose exec web python manage.py populate_books
   ```

8. **Verify** — visit `https://managelibrary.app` in a browser.

### Zero-Downtime Redeployment

```bash
docker compose pull
docker compose up -d --build
docker compose exec web python manage.py migrate --noinput
```

---

## Environment Variables

All configuration is managed through environment variables. No secrets are hardcoded.

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | Yes | — | Django cryptographic signing key. The app raises `ImproperlyConfigured` if missing. |
| `DEBUG` | No | `False` | Set to `True` for local development only. |
| `ALLOWED_HOSTS` | No | `localhost` | Comma-separated list of valid hostnames. |
| `DB_NAME` | No | `library_db` | PostgreSQL database name. |
| `DB_USER` | No | `library_user` | PostgreSQL username. |
| `DB_PASSWORD` | No | `library_pass` | PostgreSQL password. Use a strong password in production. |
| `DB_HOST` | No | `localhost` | Database host. Set to `db` when using Docker Compose. |
| `DB_PORT` | No | `5433` | Database port. Use `5432` inside Docker networks. |
| `POSTGRES_DB` | No* | — | PostgreSQL container init: database name (must match `DB_NAME`). |
| `POSTGRES_USER` | No* | — | PostgreSQL container init: username (must match `DB_USER`). |
| `POSTGRES_PASSWORD` | No* | — | PostgreSQL container init: password (must match `DB_PASSWORD`). |

\* Required in `.env.docker` for the PostgreSQL Docker container's first-run initialisation.

---

## Screenshots

<!-- Screenshots will be added after deployment -->

*Screenshots of the running application will be added here after the cloud deployment is complete.*

---

## Project Structure

```
library_checkout/
├── config/              # Django project settings, URLs, WSGI/ASGI
├── library/             # Main app: models, views, forms, admin, management commands
├── templates/           # HTML templates (base, registration, library, staff, error pages)
├── static/              # Static assets (CSS, images, JS)
├── tests/               # pytest-django test suite (45 tests)
├── nginx/               # Nginx reverse proxy configuration
├── Dockerfile           # Multi-stage Docker build (non-root user)
├── docker-compose.yml   # Production: Postgres + Gunicorn + Nginx + Certbot
├── docker-compose.dev.yml  # Development: Postgres + Django dev server
├── entrypoint.sh        # Container entrypoint (collectstatic, migrate, gunicorn)
├── requirements.txt     # Production Python dependencies
└── requirements-dev.txt # Development dependencies (adds pytest)
```
