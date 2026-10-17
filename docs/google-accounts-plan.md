# Google Accounts Specification and Implementation Plan

## Status

Approved for implementation on 2026-10-16. This document is the source of truth
for the first account feature and its Google OAuth setup.

## Objective

Campus Cuisines remains publicly browseable, while only active `@csuchico.edu`
Google-account holders may perform actions. Google is the only normal way to
create or sign in to an account. This gives campus users a low-friction account
without collecting passwords or supporting password recovery.

## Confirmed product decisions

- Allowed identity: a Google-authenticated, verified email ending in
  `@csuchico.edu`. Compare domains case-insensitively on the server; do not rely
  only on Google UI hints or a client-provided email value.
- The verified email is the immutable account identity. A new account's username
  is the email local part. Do not add a collision suffix: an unexpected username
  collision safely denies account creation and instructs the user to contact an
  administrator.
- Username editing and profile UI are out of scope, but `username` remains a
  future-facing field for product features.
- Anonymous visitors may browse public pages and published reviews. Creating,
  editing, uploading, deleting, or viewing private user-owned data requires an
  authenticated eligible account.
- Eligibility is evaluated at Google sign-in. This release does not synchronize
  Google Workspace suspension/deletion status during an existing session.
- Google is the normal staff-admin login path. A password superuser is an
  operational break-glass mechanism only; it must not be presented as a normal
  user login or account-creation path.
- Do not request Google API access or refresh tokens. Request identity data only
  (`openid`, `email`, and `profile`) and use PKCE.

## Access-level contract

Every new page, view, endpoint, command that acts for a user, and product feature
must declare one access level in its specification and tests:

| Level | Meaning | Default treatment |
| --- | --- | --- |
| `public` | Anyone may read the feature; it cannot reveal private data or mutate state. | Must be explicitly chosen. |
| `authenticated` | An eligible signed-in user may use it. | Required for all user actions and private data. |
| `staff/admin` | An eligible signed-in user with Django staff permission may use it. | Required for administration/moderation. |

Treat an unclassified feature as `authenticated` until its product specification
explicitly justifies `public`. The implementation must enforce the chosen level on
the server and test anonymous, eligible, and (where applicable) non-staff cases.
Client UI visibility is never the authorization boundary.

## Technical design

Use `django-allauth[socialaccount]` and its Google provider, configured from
environment variables rather than a `SocialApp` database row so the OAuth client
secret is not stored in PostgreSQL. Add allauth's required applications, middleware,
authentication backend, routes, and migrations while retaining Django's model
backend only for the break-glass administrative procedure.

Create an accounts-owned social-account adapter that, before a social login is
completed:

1. accepts only the Google provider;
2. requires a provider-verified email and the configured allowed domain;
3. assigns the new user's immutable email and initial username from that email;
4. denies a duplicate username safely instead of generating a substitute; and
5. returns a generic access-denied response without creating a usable account when
   the identity is not eligible.

The Google provider's subject identifier, maintained by allauth's `SocialAccount`,
is the stable provider link. Do not treat a display name as identity. Add a database
migration that makes the account email required and unique after a migration
preflight confirms there are no conflicting persisted users.

Expose a sign-in page with a POST-based "Continue with Google" control and a
logout action. Do not expose local signup, password login, password reset, account
connection, or provider-disconnection journeys. Redirect unauthenticated protected
requests to that sign-in page and preserve a safe local `next` destination.

The current homepage review form and `/images/upload/` are authenticated actions.
Their anonymous/debug-mode exceptions must be removed; their tests and templates
must reflect the access contract. Public review rendering stays public. Existing
image ownership and signed-URL authorization remain authoritative.

For `/admin/`, replace the normal login entry with Google sign-in and rely on
`is_staff` for permission after that session is established. Document a
console/management-command-only break-glass procedure; never leave a public
password login route enabled merely for convenience.

## Configuration contract

Add placeholders only to `.env.example`; real values belong in untracked `.env`
locally and Secret Manager/Cloud Run secret injection in production.

| Variable | Purpose |
| --- | --- |
| `GOOGLE_OAUTH_CLIENT_ID` | OAuth web-client ID. |
| `GOOGLE_OAUTH_CLIENT_SECRET` | OAuth web-client secret. |
| `GOOGLE_OAUTH_ALLOWED_EMAIL_DOMAINS` | Comma-separated allowed domains; initially `csuchico.edu`. |

No OAuth token storage is required. Do not log authorization codes, access tokens,
client secrets, or full identity-token contents.

## Local Google OAuth setup and test guide

Google Cloud configuration is required to test the real flow locally; Cloud Run
deployment is not. Complete these steps in a Google Cloud project:

1. In **Google Auth Platform**, configure app branding (application name, support
   email, developer contact) and select the appropriate audience. If the project
   belongs to Chico's Google Workspace organization, an Internal audience can add
   Google-side restriction. Otherwise use External and rely on this application's
   server-side `@csuchico.edu` check. In Testing status, add each developer as a
   test user; publish to Production when the campus audience should use it.
2. Create an OAuth 2.0 **Web application** client. Add exactly this local redirect
   URI:

   ```text
   http://127.0.0.1:8000/accounts/google/login/callback/
   ```

   Use `127.0.0.1` consistently: `localhost` is a different registered URI. Do
   not add broad, unused origins or redirect URIs.
3. Put the generated client ID and secret in untracked `.env`, along with
   `GOOGLE_OAUTH_ALLOWED_EMAIL_DOMAINS=csuchico.edu`. Start the application with
   `docker compose up --build web`, then use the local sign-in page in a browser.
4. Manually prove: eligible first sign-in creates the account; repeat sign-in uses
   the same account; logout works; an ineligible Google account is denied and does
   not create a user; anonymous review/image POSTs redirect or reject; and a
   signed-in user can complete those actions.

For production, create a separate OAuth client (recommended) and register only the
final HTTPS Cloud Run/custom-domain callback:

```text
https://<production-domain>/accounts/google/login/callback/
```

Add that production domain to the consent-screen authorized domains and verify its
ownership as required by Google. Inject the production client secret through Secret
Manager at runtime. Do not reuse a local secret in deployment configuration. The
homepage must remain publicly readable because it is the consent-screen homepage.

## Commands

After implementation, run:

```sh
export DJANGO_DEBUG=true
python scripts/verify_infrastructure.py
ruff format --check .
ruff check .
pyright
python manage.py check
pytest
RUN_BROWSER_TESTS=true pytest -m browser
./scripts/smoke.sh
```

The real Google consent flow is a manual local-browser acceptance test; automated
tests must mock/provider-fixture the external identity response and never use real
OAuth credentials.

## Testing strategy

- Model/migration: email is required/unique; the migration has a safe data-audit
  path; existing image ownership remains valid.
- Adapter/service: accept a verified Chico Google identity; deny an unverified,
  wrong-domain, missing-email, wrong-provider, and duplicate-username identity
  without persisting a usable account.
- View/integration: only the Google sign-in start/callback paths are available;
  protected routes preserve safe return paths; local password/account routes are
  absent or inaccessible; logout clears the session.
- Authorization regression: public pages render anonymously; review submission and
  image upload require an eligible account in both debug and non-debug settings;
  non-staff users cannot enter staff administration.
- Browser: verify public navigation, sign-in entry visibility, logout, and
  authenticated form availability using a test-authenticated session. Complete the
  real Google flow manually using the local guide above.

## Ordered implementation tasks

### Task 1: Add the dependency and configuration foundation

- Acceptance: the lock files contain a reviewed allauth social-account dependency;
  settings read only the documented environment variables; no secret is committed.
- Verify: regenerate hashes with the documented pip-tools process, run settings
  tests and `python manage.py check`.
- Likely files: `requirements.in`, lock files, `config/settings.py`,
  `.env.example`, `tests/test_settings.py`.
- Dependencies: none.

### Task 2: Establish identity persistence and eligibility enforcement

- Acceptance: email is immutable, required, and unique; Google subject links are
  persisted by allauth; only verified `@csuchico.edu` Google identities can create
  or complete an account; initial usernames have no collision fallback.
- Verify: migration, adapter, and persistence tests for every accept/deny case.
- Likely files: `accounts/models.py`, `accounts/adapters.py`, `accounts/migrations/`,
  `accounts/tests/`.
- Dependencies: Task 1.

### Checkpoint: identity safety

- [ ] Migration applies to a clean database and passes the preflight on any retained data.
- [ ] No ineligible callback can create a usable user or session.
- [ ] Focused account tests pass.

### Task 3: Deliver the Google-only account journey

- Acceptance: a user can start a POST-only Google login, receive an accessible
  allowed/denied result, return safely to a protected page, and log out; local
  consumer signup/password flows are unavailable.
- Verify: route/template/view tests plus manual local OAuth test.
- Likely files: `config/urls.py`, `accounts/urls.py`, `accounts/views.py`,
  templates, static CSS, and account tests.
- Dependencies: Task 2.

### Task 4: Enforce and document feature access levels

- Acceptance: public browsing is explicit; reviews and image uploads require an
  eligible account in all environments; future features have a reusable access
  classification/enforcement pattern; staff administration uses Google sessions.
- Verify: anonymous, authenticated, and staff authorization tests; Django admin
  access test.
- Likely files: `core/views.py`, `reviews/`, `accounts/`, templates, tests,
  `AGENTS.md`, and README.
- Dependencies: Task 3.

### Checkpoint: working application behavior

- [ ] Anonymous visitors can browse but cannot mutate data.
- [ ] An eligible local Google sign-in can submit a review and upload an image.
- [ ] Browser and full application checks pass.

### Task 5: Complete operational documentation and review

- Acceptance: the README contains local setup/testing and the production OAuth
  handoff; the break-glass procedure is restricted to operators; this plan and the
  access-level rules match the implementation.
- Verify: documentation review, `git diff --check`, secret scan, and the complete
  command list above.
- Likely files: `README.md`, `docs/decisions/`, `docs/`, and `AGENTS.md`.
- Dependencies: Tasks 1-4.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Client-side/domain-hint bypass | Validate provider, verified email, and allowlist in the social adapter before account/session creation. |
| OAuth secret exposure | Use environment/Secret Manager configuration; never use a database `SocialApp` or commit credentials. |
| Existing account-email conflicts | Audit data before making email unique; halt migration on unresolved conflicts. |
| Anonymous write regression | Add route-level tests for every current mutation and require future features to state an access level. |
| OAuth redirect mismatch | Register exact local and production callback URIs separately and keep them documented. |
| Google outage or lost administrator access | Maintain an audited, operator-only break-glass runbook outside normal public routes. |

## Sources

- django-allauth installation and URL/configuration: https://docs.allauth.org/en/latest/installation/quickstart.html
- django-allauth Google provider and callback configuration: https://docs.allauth.org/en/latest/socialaccount/providers/google.html
- django-allauth adapter hooks and verified-email configuration: https://docs.allauth.org/en/latest/socialaccount/adapter.html
- django-allauth provider credential configuration and its database-secret warning: https://docs.allauth.org/en/latest/socialaccount/provider_configuration.html
- Google OAuth redirect URI matching: https://developers.google.com/identity/protocols/oauth2/web-server
- Google OAuth audience, testing users, and publication state: https://support.google.com/cloud/answer/15549945
- Google authorized-domain verification: https://support.google.com/cloud/answer/13804266
