# Infrastructure Plan

> Planning only. This document describes future infrastructure work. No installations, configuration changes, containers, workflows, deployments, or other implementation files were created by the infrastructure-planning process.

## 1. Project and User Experience

- **Application:** Campus Cuisines (assumed from repository name)
- **Primary users:** Public users with individual accounts.
- **Primary user task:** Browse and interact with campus-food content; confirm the exact feature set before implementation.
- **Selected platform:** Browser-based web application.
- **User-experience rationale:** Users can open a link immediately on desktop and mobile browsers without an installation.
- **Required operating systems, browsers, or devices:** Current desktop and mobile versions of Chrome, Firefox, Safari, and Edge.
- **Offline or native-device requirements:** Cache the application shell and selected recently viewed content so brief connection loss has limited impact; server-backed actions require connectivity.

## 2. Connectivity and Application Shape

- **Connectivity model:** Multi-user web-enabled.
- **Accounts and authentication:** Separate Django-managed user accounts; select the sign-in method and account-recovery policy before implementation.
- **Backend required:** Yes, one Django application and relational database.
- **Cross-device persistence:** Hosted PostgreSQL preserves account data across devices.
- **Interaction between accounts:** Supported through server-authorized Django features; define the precise sharing or interaction rules in product requirements.
- **Primary application components:** Django web UI and backend, PostgreSQL, object storage for uploads, and a cache/service-worker layer for limited offline resilience.

## 3. Selected Technology Stack

| Area | Selected technology | Purpose | Version policy |
|---|---|---|---|
| Primary language | Python | Application and backend code | Python 3.13 |
| Application framework | Django | Server-rendered public web application, accounts, ORM, and admin | Django 5.2 LTS |
| Runtime or SDK | CPython | Run Django and tooling | Supported stable release |
| Package manager | pip with pip-tools | Install reproducible Python dependencies | `requirements.in` inputs and hash-locked `requirements.txt` |
| Build or packaging tool | Docker multi-stage build | Package the application as an OCI image | Supported Docker BuildKit features |
| Web serving | Gunicorn behind a managed HTTPS endpoint | Serve Django in production | Supported stable release |
| Static assets | Django staticfiles with WhiteNoise | Serve versioned static browser assets | WhiteNoise serves collected, versioned assets from the Django image |

## 4. Storage and Persistence

- **Storage model:** Hosted relational data plus hosted object storage.
- **Primary data store:** Managed PostgreSQL.
- **User files or object storage:** A provider-supported object-storage bucket for uploads; store object keys and metadata in PostgreSQL, not file blobs in database rows.
- **Local-development storage:** PostgreSQL container and an S3-compatible object-storage emulator in Compose.
- **Production hosting model:** Managed PostgreSQL and object storage alongside the Cloud Run deployment.
- **Schema and migration approach:** Django migrations, reviewed with application changes and executed as an explicit release step before traffic reaches a migration-dependent version.
- **Backup, export, or recovery approach:** Enable managed PostgreSQL automated backups and point-in-time recovery where available; apply bucket versioning/lifecycle policy and periodically test restoration.
- **Secrets and connection-string approach:** Keep database URLs, bucket credentials, Django secret key, and allowed-host settings in Cloud Run/GitHub secrets or a cloud secret manager; never commit them or bake them into images.
- **Reason this storage fits the access pattern:** PostgreSQL fits shared relational account data, and object storage is durable and scalable for user uploads.

## 5. Testing Tools

| Test layer | Tool or library | Planned scope | Planned execution point |
|---|---|---|---|
| Unit | pytest and pytest-django | Models, forms, permissions, services, and utility code | Local and pull requests |
| Integration | pytest-django with PostgreSQL test service | Views, ORM queries, uploads, authentication, and storage integration | Local and pull requests |
| End-to-end or UI | Playwright for Python | Core public browsing, sign-in, account, and upload journeys | Pull requests when practical; release validation |

## 6. Test Analysis

| Capability | Tool | Planned policy |
|---|---|---|
| Coverage | coverage.py with pytest-cov | Produce terminal and XML reports |
| Coverage threshold or regression rule | pytest-cov configuration | Enforce a modest initial 70% project threshold on pull requests; raise only with team agreement |
| Mutation testing | Not selected initially | Reconsider for small, business-critical modules after the core suite is stable |
| Flaky-test or duration analysis | pytest durations and Playwright traces | Report slow tests locally and retain CI failure evidence |
| Reporting | GitHub Actions artifacts | Upload coverage XML/HTML and relevant test reports on failure |

## 7. Static Analysis and Security

| Check | Tool | Planned enforcement |
|---|---|---|
| Formatting | Ruff formatter | Blocking pull-request check |
| Linting | Ruff | Blocking pull-request check |
| Type checking or compiler warnings | Pyright | Blocking pull-request check for application code |
| Anti-pattern or maintainability analysis | Ruff rules and Django checks | Blocking baseline; keep rules focused and documented |
| Dependency vulnerability scanning | Dependabot and `pip-audit` | Dependabot alerts/updates; `pip-audit` blocks pull requests on actionable known vulnerabilities |
| Secret scanning | Gitleaks | Blocking pull-request and history-aware scheduled scan |
| Static security analysis | Bandit and GitHub CodeQL | Bandit blocks pull requests; CodeQL runs on pull requests and scheduled scans |
| Container scanning | Trivy | Scan Docker image before registry publication; block releases on high/critical findings per agreed exception policy |

## 8. Development Technologies Requiring Manual Installation

These are developer-workstation prerequisites that will not be supplied by the planned Docker environment.

| Technology | Why it is needed | Required on which machines | Version policy | Planned installation or verification method | Why Docker does not provide it |
|---|---|---|---|---|---|
| Git | Source control and GitHub workflow | All developer machines | Supported stable release | Future: install from the OS-supported distribution and verify with `git --version` | Docker cannot manage the host working-copy workflow |
| Docker Desktop or Docker Engine with Compose | Build and run development services and images | All developer machines; Linux may use Docker Engine | Supported stable release | Future: install the platform-supported Docker distribution and verify with `docker version` and `docker compose version` | It is the host container runtime |
| Web browser | Manual local browser use and optional Playwright headed debugging | All developer machines | Current stable browser | Future: keep a supported browser updated | Browser UI is a host application |
| Google Cloud CLI (optional) | Manual diagnostics or emergency operations, if team policy permits | Release maintainers only | Supported stable release | Future: install only after Cloud Run account setup | Deployment credentials and cloud access remain host/account concerns |

### Host tools intentionally not required

- **Not required because Docker supplies them:** Python, pip, Django, PostgreSQL client/server, object-storage emulator, pytest, and application dependencies.
- **Not required for this platform:** Xcode, Android Studio, native desktop SDKs, and mobile-store signing tools.

## 9. Docker Plan

- **Planned Docker role:** Development and production deployment.
- **Future files that would be created during implementation:** `Dockerfile`, `compose.yml`, `.dockerignore`, and an example environment-variable document with no secrets.
- **Planned images and services:** A Django/Gunicorn image; local PostgreSQL; local S3-compatible object-storage emulator; optional reverse proxy only if needed locally.
- **Development container behavior:** Bind-mount source code, run Django with development settings, and use named volumes for database and emulator state.
- **Ports:** Define development-only ports for Django, PostgreSQL, and the storage emulator; expose only the application HTTP port in production.
- **Bind mounts and named volumes:** Bind mount source only in development; named volumes retain local database/object-storage data; production is stateless except for external stores.
- **Environment-variable and secret handling:** Read configuration at runtime; use untracked local environment values for development and Cloud Run secret references in production.
- **Local database or service containers:** Compose runs PostgreSQL and the object-storage emulator; test jobs use service containers when needed.
- **Production image or non-container release path:** Publish a versioned, immutable Docker image to Artifact Registry and deploy it to Cloud Run.
- **Build stages and hardening:** Use multi-stage builds, minimal runtime base, a non-root user, `.dockerignore`, health/readiness endpoint, pinned base-image policy, and no embedded secrets.
- **Planned future development command:** `docker compose up --build` (run only during implementation/development).
- **Planned future production or packaging command:** `docker build --tag <registry>/<project>/campus-cuisines:<version> .` (run only from the future release workflow or approved release process).

## 10. GitHub Actions Plan

### A. Automated pull-request checks

- **Future workflow file:** `.github/workflows/pr-checks.yml`
- **Trigger:** `pull_request` as the primary trigger; optionally `workflow_dispatch` for reruns.
- **Runner or matrix:** `ubuntu-latest`; test against the selected supported Python version, expanding to a small supported-version matrix only when the project declares one.
- **Permissions:** Least privilege: `contents: read`; grant `security-events: write` only to CodeQL jobs and avoid write tokens elsewhere.
- **Planned jobs in order:**
  1. Checkout, set up Python, restore pip cache, and lockfile-enforced dependency installation.
  2. Ruff format verification and linting, Pyright, Django system checks, Bandit, `pip-audit`, and Gitleaks.
  3. pytest/pytest-django unit and integration suite with PostgreSQL service container; collect coverage and enforce 70% threshold.
  4. Build the Docker image and run Trivy image scan.
  5. Run Playwright core browser journeys against the built application when CI time and test data are ready; upload traces/screenshots on failure.
  6. Run CodeQL analysis and upload results.
- **Service containers:** PostgreSQL; include an S3-compatible service only for integration tests that exercise the storage adapter.
- **Caching:** Cache pip downloads keyed by Python version and dependency lockfile hash; cache Playwright browsers keyed by Playwright version.
- **Coverage and analysis reporting:** Publish coverage XML/HTML as artifacts; surface CodeQL findings in GitHub Security; retain lint/test logs on failures.
- **Failure artifacts:** Coverage reports, pytest output, Django logs with secrets redacted, Playwright traces/videos/screenshots, and Trivy report.
- **Checks that should block merging:** Dependency install, format, lint, types, Django checks, Bandit, dependency/secret scans, tests/coverage, Docker build, and high/critical container findings; CodeQL blocks according to repository security policy.
- **Proposed branch-protection settings:** Require pull request review, required passing checks, up-to-date branch before merge, and no force pushes to the protected default branch.

### B. New-release deployment

- **Future workflow file:** `.github/workflows/release.yml`
- **Release trigger:** A protected `v*` tag or `workflow_dispatch` with an explicit version; use a protected GitHub environment before production deployment.
- **Release destination:** Google Artifact Registry and Google Cloud Run.
- **Runner or matrix:** `ubuntu-latest`; use Google’s supported authentication/deployment actions and avoid long-lived cloud keys.
- **Planned jobs in order:**
  1. Validate the tag/version and rerun relevant format, analysis, test, coverage, and Docker build checks.
  2. Authenticate to Google Cloud through GitHub-to-Google workload identity federation, build a versioned image, scan it with Trivy, and publish it to Artifact Registry.
  3. Run reviewed Django migrations as a controlled one-off job against production PostgreSQL, when required.
  4. Deploy the immutable image digest to Cloud Run under the protected production environment.
  5. Run smoke checks against the HTTPS endpoint, create release notes, and record the deployed image digest.
- **Build artifacts:** Image digest, Trivy report, coverage/test summary, release notes, and optional source archive/checksums.
- **Signing, notarization, or store requirements:** No native-app signing; protect Google deployment identity and Artifact Registry permissions.
- **Database migration step:** Required only when migrations are present; use backward-compatible, reviewed migrations and do not deploy incompatible code before migration success.
- **Environment approval:** GitHub `production` environment approval before cloud deployment.
- **Post-deployment verification:** Health/readiness endpoint and a small anonymous browser/API smoke workflow against the deployed service.
- **Failed-release or rollback approach:** Stop rollout, redeploy the prior known-good Cloud Run revision/image digest, then assess database compatibility before any database recovery action.

### GitHub configuration required later

| Name | Type | Purpose |
|---|---|---|
| `GCP_PROJECT_ID` | Repository variable | Target Google Cloud project identifier |
| `GCP_REGION` | Repository variable | Cloud Run and Artifact Registry region |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Repository variable | GitHub Actions workload-identity provider resource name |
| `GCP_SERVICE_ACCOUNT` | Repository variable | Least-privilege deployer service-account email |
| `production` | GitHub environment | Approval gate and production-scoped configuration |
| `DJANGO_SECRET_KEY` | Cloud secret | Django cryptographic signing key injected at runtime |
| `DATABASE_URL` | Cloud secret | Production PostgreSQL connection string injected at runtime |
| `OBJECT_STORAGE_*` | Cloud secrets | Bucket endpoint/name as applicable and access credentials, preferably workload identity |
| `GITLEAKS_LICENSE` | Repository or organization secret | Required by the Gitleaks Action when this repository belongs to a GitHub organization; never commit the license value |
| Google Cloud project and billing account | Provider account | Enable Cloud Run, Artifact Registry, managed PostgreSQL, object storage, and secret management |
| GitHub Advanced Security availability | GitHub account/entitlement | Enable CodeQL code-scanning results where required by repository policy |

## 11. Planned Repository Artifacts - Not Created by This Skill

List only the files that a later implementation task is expected to create. This section is documentation, not authorization to create them now.

- [ ] Application manifest or project file: `requirements.in`/`requirements.txt` or equivalent pinned dependency specification
- [ ] Lockfile: a reproducible Python dependency lock file
- [ ] Test configuration: `pyproject.toml` and Playwright configuration as appropriate
- [ ] Static-analysis configuration: `pyproject.toml`, Gitleaks/CodeQL settings if needed
- [ ] Docker or Compose files: `Dockerfile`, `compose.yml`, `.dockerignore`
- [ ] `.github/workflows/pr-checks.yml`
- [ ] `.github/workflows/release.yml`
- [ ] Deployment or store configuration: Cloud Run service configuration and infrastructure definitions, selected later

## 12. Assumptions and Open Items

- **Assumptions:** Campus Cuisines has account-based public interaction and users may upload images or files; its browser UI can tolerate server-backed actions waiting for reconnection.
- **Decisions still requiring an external account, credential, certificate, or organizational approval:** Google Cloud project/billing ownership; production domain and DNS; Google workload-identity setup; managed PostgreSQL and bucket selection; Cloud Run/Artifact Registry permissions; Django authentication and email provider; GitHub environment approvers.
- **Confirmed implementation choices:** Python 3.13; Django 5.2 LTS; `pip-tools` for hash-locked dependencies; and WhiteNoise for static asset delivery.
- **Items to confirm before product implementation begins:** Exact primary user workflows; acceptable offline-cached content and privacy rules; upload type/size limits and moderation; data retention and backup policy; production region; and coverage baseline appropriateness.
