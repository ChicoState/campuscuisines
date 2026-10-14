# Django Foundation Specification

## Objective

Provide a small, browser-visible Django application foundation that the team can
extend feature by feature. Visiting `/` locally must return an accessible Campus
Cuisines welcome page.

## Technical decisions

- Python 3.13 and Django 5.2 LTS, consistent with `infrastructure_plan.md`.
- Django templates and static files for the initial server-rendered UI.
- PostgreSQL when the application is run with Docker Compose; SQLite is used only
  by isolated tests that do not need PostgreSQL.
- `accounts.User` subclasses `AbstractUser` without Campus Cuisines-specific
  fields. `AUTH_USER_MODEL` is set before the first migration so account design
  can evolve without changing Django's user-model setting later.
- Local Compose starts the `web`, `postgres`, and `minio` services. MinIO now backs
  private reusable image assets; the `minio-init` service creates the bucket and
  removes anonymous access before the web service accepts uploads.
- Django reaches MinIO through the Compose-only `OBJECT_STORAGE_ENDPOINT`, while
  browser-consumed signed URLs use `OBJECT_STORAGE_PUBLIC_ENDPOINT`. The committed
  local defaults are `http://minio:9000` and `http://localhost:9000`, respectively.

## Commands

```sh
cp .env.example .env
docker compose up --build web
```

The example environment file explicitly sets `DJANGO_DEBUG=true` for local Compose
development. Django defaults to non-debug mode when the variable is absent.

Run automated checks with:

```sh
export DJANGO_DEBUG=true
.venv/bin/python manage.py check
.venv/bin/pytest
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/pyright
```

## Structure

```text
config/       Django settings, URL routing, and WSGI/ASGI entry points
accounts/     Custom user model and its migration
core/         Public homepage, reusable image assets, and retention command
templates/    Shared and page templates
static/       Project CSS and future browser assets
tests/        Django application tests alongside infrastructure tests
```

## Boundaries

- Always: keep secrets in environment variables, add tests for behavior, and run
  checks before committing.
- Ask first: add authentication flows, domain models, external services, or new
  dependencies beyond the approved image-asset workflow.
- Never: commit `.env` values or make product decisions about reviews or other food
  content beyond the approved image-asset workflow.

## Success criteria

- `http://localhost:8000/` renders the public homepage via the Compose `web`
  service.
- Django recognizes the configured custom user model and its initial migration.
- The homepage has a route-level test and renders without browser console errors.
- Existing infrastructure checks continue to pass.

## Implementation plan

1. Create the settings and custom-user-model foundation; verify Django can load it.
2. Write a failing homepage test, then add the route, template, and CSS.
3. Add the Compose `web` service and verify database migration plus browser startup.
4. Update the README with the now-real local application commands and run all
   project checks.
