# Agent guidance

## Status and source of truth

This repository has an infrastructure-only foundation for the planned Campus Cuisines Django application. Read `infrastructure_plan.md` before changes; it records selected Python 3.13, Django 5.2 LTS, pip-tools lock files, WhiteNoise static delivery, local PostgreSQL/MinIO, and Cloud Run as the future release target. Do not change those decisions without using the applicable planning skill and updating the plan.

## Repository map

- Application package, Django settings, front end, API, models, migrations, and product docs: not created yet.
- `requirements.in` / `requirements.txt` / `pyproject.toml`: reproducible Python toolchain and quality configuration.
- `compose.yml`, `Dockerfile`, `.dockerignore`, `.env.example`: local services and future application container infrastructure.
- `scripts/`: configuration verifier and Compose smoke test.
- `tests/infrastructure/`: infrastructure-only tests.
- `.github/workflows/`: PR quality checks and guarded future release workflow.
- `.agents/skills/`: local skill instructions.

## Required workflow

1. Read this file, `infrastructure_plan.md`, and the applicable local `SKILL.md` before changing files.
2. Use `spec-driven-development` and `planning-and-task-breakdown` for product scope; `infra-builder` for planned infrastructure; `incremental-implementation` and `test-driven-development` for application behavior; `frontend-ui-engineering` for UI; `api-and-interface-design` for public APIs; `security-and-hardening` for auth, storage, uploads, or external integrations; `test-in-browser` or `browser-testing-with-devtools` for browser verification; `ci-cd-and-automation` for workflows; `documentation-and-adrs` for durable decisions; `code-review-and-quality` before merge; and `git-workflow-and-versioning` for every change/commit.
3. Do not implement product behavior as part of infrastructure work. Do not add secrets, generated reports, local volumes, production data, or remote credentials to Git.
4. Update the README and this file when a command, service lifecycle, repository path, or developer prerequisite changes.

## Verification

Use Python 3.13 with the hash-locked requirements file. Run:

```sh
python scripts/verify_infrastructure.py
ruff format --check .
ruff check .
pyright
pytest tests/infrastructure
./scripts/smoke.sh
```

CI runs the same infrastructure checks plus Bandit, pip-audit, Gitleaks, CodeQL, Docker image build/Trivy scanning, and—after application code is added—Django checks, full test coverage, and browser tests.

`./scripts/smoke.sh` always cleans up with `docker compose down --volumes --remove-orphans`. For manual development, start only `postgres` and `minio`; stop them with the same cleanup command when finished. Named volumes hold disposable local data.

## Change checklist

- Keep the change in the plan’s scope and avoid product code in infrastructure tasks.
- Regenerate and review `requirements.txt` whenever `requirements.in` changes; never hand-edit the lock file.
- Run the relevant local checks and state any unavailable prerequisite exactly.
- Inspect `git diff --check` and ensure no secrets are in the diff.
- Update documentation for changed commands, configuration, or prerequisites.
