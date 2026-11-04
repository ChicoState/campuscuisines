# ADR-0002: Use Google-only authentication for Chico accounts

## Status

Accepted — 2026-10-16.

## Context

Campus Cuisines needs accounts for user actions while keeping campus-food content
publicly browseable. The project already has a custom Django user model, but no
account journey. The selected identity population is active Chico users with
`@csuchico.edu` Google accounts.

## Decision

Use Google OAuth through `django-allauth` as the only normal account creation and
sign-in method. The server accepts a callback only when Google supplies a verified
email in the `csuchico.edu` allowlist. Store that email as the immutable, unique
account identity; initialize `username` from its local part without collision
fallback. The allauth Google subject remains the provider-account link.

Public reads are explicitly classified `public`; user actions/private data are
`authenticated`; administration is `staff/admin`. Unclassified future features are
treated as authenticated. Normal staff sessions originate through Google; a
password superuser is a documented break-glass operational mechanism, not a normal
web account flow.

## Alternatives considered

### Django username/password accounts

- Pros: no external identity configuration.
- Cons: adds password storage, reset, recovery, abuse, and eligibility burden.
- Rejected: Google Workspace already provides the intended campus identity.

### Client-side Google domain restriction only

- Pros: very small UI configuration.
- Cons: a UI/domain hint is not authorization and can be bypassed.
- Rejected: the backend must decide who can create a session or account.

### Make all pages login-required

- Pros: uniform route protection.
- Cons: removes the intended public browsing experience.
- Rejected: the product needs public read-only access, with explicit server-side
  protection for every action.

## Consequences

- Production requires a Google OAuth web client and runtime client-secret delivery.
- The app does not offer password recovery, multi-provider linking, or real-time
  Google Workspace deprovisioning in this release.
- Existing anonymous review/image submission behavior must be changed to require an
  eligible session.
- Every future feature specification and tests must declare an access level.

See [the Google accounts specification and implementation plan](../google-accounts-plan.md).
