# Campus Cuisines

Campus Cuisines is planned as a Django web application for campus-food content. This repository currently contains a verified development foundation; production application code, Django settings, routes, models, migrations, and user workflows have not been created.

## Repository map

| Path | Purpose |
| --- | --- |
| `requirements.in`, `requirements.txt`, `pyproject.toml` | Python 3.13 dependency inputs, locked dependencies, and quality-tool configuration |
| `compose.yml`, `Dockerfile` | Local PostgreSQL/MinIO services and the future non-root Django/Gunicorn image |
| `scripts/` | Infrastructure verification and Docker-backed smoke test |
| `tests/infrastructure/` | Configuration-only test harness |
| `.github/workflows/` | Pull-request checks and guarded future Cloud Run release workflow |
| `.agents/skills/` | Repository-specific agent workflows |
| `frontend/`, application package, API, docs | Not created yet |

## Getting started

1. Install [Git](https://git-scm.com/downloads), [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine plus Compose), and a current [web browser](https://www.google.com/chrome/). Verify with `git --version`, `docker version`, and `docker compose version`.
2. Install Python 3.13 only if you intend to run quality tools outside Docker. Use the [official Python installer](https://www.python.org/downloads/) or your platform version manager, then verify `python3.13 --version`.
3. Create local-only configuration: `cp .env.example .env`. Replace the placeholder values in `.env`; never commit it.
4. Install the exact locked toolchain using Python 3.13:

   ```sh
   python3.13 -m venv .venv
   . .venv/bin/activate
   python -m pip install --require-hashes -r requirements.txt
   ```

5. Run non-Docker checks:

   ```sh
   python scripts/verify_infrastructure.py
   ruff format --check .
   ruff check .
   pyright
   pytest tests/infrastructure
   ```

6. Run the local-service smoke test. It starts PostgreSQL and MinIO, verifies readiness, then removes the containers and named volumes:

   ```sh
   ./scripts/smoke.sh
   ```

The Docker image installs all locked dependencies and runs as a non-root user, but it intentionally cannot start until product work adds a Django WSGI module. Django’s WSGI server needs an application callable and settings module, so this foundation does not fabricate one. See the [Django WSGI deployment documentation](https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/).

## Common commands

| Command | Purpose |
| --- | --- |
| `python scripts/verify_infrastructure.py` | Check required infrastructure files and core configuration |
| `ruff format --check . && ruff check .` | Format and lint checks |
| `pyright` | Type-check configured Python files |
| `pytest tests/infrastructure` | Run the configuration-only test harness |
| `./scripts/smoke.sh` | Validate Compose services, then clean them up |
| `docker compose up -d postgres minio` | Start local services during future application work |
| `docker compose down --volumes --remove-orphans` | Stop services and delete local data |

When application code exists, CI will run Django checks, the full pytest suite, 70% coverage enforcement, and Playwright journeys. Static files should use Django `collectstatic` with WhiteNoise; Django documents `STATIC_ROOT` and the static-files workflow in its [staticfiles reference](https://docs.djangoproject.com/en/5.2/ref/contrib/staticfiles/).

## Troubleshooting

- **Docker permission denied:** ensure Docker Desktop/Engine is running and your Linux user can access the Docker socket; then rerun `docker version`.
- **Port 5432, 9000, or 9001 already in use:** stop the conflicting local service or change the corresponding host-port mapping in `compose.yml`.
- **Hash installation fails:** use Python 3.13 and do not edit `requirements.txt` by hand. Regenerate it only with the documented `pip-tools` command below.
- **Local data needs resetting:** run `docker compose down --volumes --remove-orphans`. This deletes only Campus Cuisines’ named local service volumes.

## Updating dependencies

The lock was generated with `pip-tools` on Python 3.13. To deliberately update it, run this controlled command and review the resulting diff:

```sh
docker run --rm -v "$PWD:/workspace" -w /workspace python:3.13-slim \
  sh -c "pip install 'pip<26' pip-tools==7.5.2 && pip-compile --generate-hashes --allow-unsafe -o requirements.txt requirements.in"
```

The `pip<26` bootstrap is required because the selected generator is not compatible with pip 26. GitHub Actions uses `setup-python`’s pip cache, as described in [GitHub’s dependency-caching documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching).

## Future GitHub and cloud prerequisites

Before a real release can run, configure the `production` GitHub environment, its approval rules, `GCP_PROJECT_ID`, `GCP_REGION`, `GCP_WORKLOAD_IDENTITY_PROVIDER`, and `GCP_SERVICE_ACCOUNT` repository variables, GitHub-to-Google workload identity federation, Google Cloud billing/project permissions, and runtime secrets such as `DJANGO_SECRET_KEY`, `DATABASE_URL`, and object-storage credentials. The release workflow intentionally fails before authentication or deployment until the Django project and those prerequisites exist.
