# Campus Cuisines

Campus Cuisines is a Django web application foundation for campus-food content. It includes a public home page, initial application settings, and a deliberately minimal custom user model. Food-content workflows and account experiences have not been designed or implemented yet.

## Repository map

| Path | Purpose |
| --- | --- |
| `requirements.in`, `requirements.txt`, `requirements-dev.in`, `requirements-dev.txt`, `pyproject.toml` | Python 3.13 runtime/development dependency inputs, hash-locked dependencies, and quality-tool configuration |
| `compose.yml`, `Dockerfile` | Local PostgreSQL/MinIO services and the future non-root Django/Gunicorn image |
| `scripts/` | Infrastructure verification and Docker-backed smoke test |
| `tests/infrastructure/` | Configuration-only test harness |
| `.github/workflows/` | Pull-request checks and guarded future Cloud Run release workflow |
| `.agents/skills/` | Repository-specific agent workflows |
| `config/` | Django settings, routes, and WSGI/ASGI entry points |
| `accounts/` | Initial custom Django user model and migration |
| `core/`, `templates/`, `static/` | Public homepage and browser assets |
| `docs/` | Living implementation specifications and plans |

## Getting started

1. Install [Git](https://git-scm.com/downloads), [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine plus Compose), and a current [web browser](https://www.google.com/chrome/). Verify with `git --version`, `docker version`, and `docker compose version`.
2. Install Python 3.13 only if you intend to run quality tools outside Docker. Use the [official Python installer](https://www.python.org/downloads/) or your platform version manager, then verify `python3.13 --version`.
3. Create local-only configuration: `cp .env.example .env`. Replace the placeholder values in `.env`; never commit it.
4. Install the exact locked toolchain using Python 3.13:

   ```sh
   python3.13 -m venv .venv
   . .venv/bin/activate
   python -m pip install --require-hashes -r requirements-dev.txt
   ```

5. Start the local application. Compose runs the application, PostgreSQL, and MinIO; it applies local migrations before starting Django:

   ```sh
   docker compose up --build web
   ```

   Open <http://localhost:8000/> in a browser. Stop the services and remove their disposable local data with `docker compose down --volumes --remove-orphans`.

6. Run non-Docker checks:

   ```sh
   python scripts/verify_infrastructure.py
   ruff format --check .
   ruff check .
   pyright
   pytest
   ```

7. Run the local-service smoke test. It starts PostgreSQL and MinIO, verifies readiness, then removes the containers and named volumes:

   ```sh
   ./scripts/smoke.sh
   ```

The Docker image installs only the runtime lock file and runs as a non-root user. Compose overrides its production Gunicorn command with Django’s development server and bind-mounts the source code for local edits. See the [Django WSGI deployment documentation](https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/).

## Common commands

| Command | Purpose |
| --- | --- |
| `python scripts/verify_infrastructure.py` | Check required infrastructure files and core configuration |
| `ruff format --check . && ruff check .` | Format and lint checks |
| `pyright` | Type-check configured Python files |
| `pytest` | Run infrastructure and application tests |
| `./scripts/smoke.sh` | Validate Compose services, then clean them up |
| `docker compose up --build web` | Start the local application, PostgreSQL, and MinIO at `http://localhost:8000/` |
| `docker compose down --volumes --remove-orphans` | Stop services and delete local data |

When application code exists, CI will run Django checks, the full pytest suite, 70% coverage enforcement, and Playwright journeys. Static files should use Django `collectstatic` with WhiteNoise; Django documents `STATIC_ROOT` and the static-files workflow in its [staticfiles reference](https://docs.djangoproject.com/en/5.2/ref/contrib/staticfiles/).

## Troubleshooting

- **Docker permission denied:** ensure Docker Desktop/Engine is running and your Linux user can access the Docker socket; then rerun `docker version`.
- **Port 5432, 9000, or 9001 already in use:** stop the conflicting local service or change the corresponding host-port mapping in `compose.yml`.
- **Hash installation fails:** use Python 3.13 and do not edit `requirements.txt` by hand. Regenerate it only with the documented `pip-tools` command below.
- **Local data needs resetting:** run `docker compose down --volumes --remove-orphans`. This deletes only Campus Cuisines’ named local service volumes.

## Updating dependencies

The locks are generated with `pip-tools==7.6.1` on Python 3.13. To deliberately update them, run this controlled command and review the resulting diff:

```sh
docker run --rm -v "$PWD:/workspace" -w /workspace python:3.13-slim \
  sh -c "pip install 'pip<26' pip-tools==7.6.1 && pip-compile --generate-hashes --allow-unsafe -o requirements.txt requirements.in && pip-compile --generate-hashes --allow-unsafe -o requirements-dev.txt requirements-dev.in"
```

The `pip<26` bootstrap is required because the selected generator is not compatible with pip 26. GitHub Actions uses `setup-python`’s pip cache, as described in [GitHub’s dependency-caching documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching).

## Future GitHub and cloud prerequisites

Before a real release can run, configure the `production` GitHub environment, its approval rules, `GCP_PROJECT_ID`, `GCP_REGION`, `GCP_WORKLOAD_IDENTITY_PROVIDER`, and `GCP_SERVICE_ACCOUNT` repository variables, GitHub-to-Google workload identity federation, Google Cloud billing/project permissions, and runtime secrets such as `DJANGO_SECRET_KEY`, `DATABASE_URL`, and object-storage credentials. The release workflow intentionally fails before authentication or deployment until the Django project and those prerequisites exist.

The pull-request secret scan uses Gitleaks v3. If this repository is owned by a GitHub organization, obtain a Gitleaks license and save it in **Settings → Secrets and variables → Actions** as the repository or organization secret `GITLEAKS_LICENSE`; do not place the license in this repository. Personal-account repositories do not require that secret.
