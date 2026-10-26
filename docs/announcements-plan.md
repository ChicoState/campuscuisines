# Announcement Stage 3 Specification and Plan

## Objective

Replace the initial static announcement modal with a database-backed announcement
panel. Users can dismiss announcements, see the current count in the header, and
review all announcements on a separate history page.

## Scope and decisions

- The button is available in the shared green header on every page.
- A native HTML `dialog` provides modal semantics, focus containment, and Escape
  handling without a new dependency.
- The seed data contains one test announcement:
  "Test announcement," attributed to Admin, with the body "This is a test
  announcement."
- Announcement content is stored in Django's database and can be managed in Django
  admin. Dismissals are stored per authenticated user or anonymous session.
- Each announcement can be dismissed from the X button in its heading.
- The history page lists active and archived announcements.
- Staff can reannounce any history entry. Reannouncing activates the existing
  announcement and clears its prior user/session dismissals so it appears as new
  to everyone again.
- The modal closes from its visible Close button, the Escape key, or a click on
  the backdrop. Focus returns to the Announcements button when it closes.

## Commands

```sh
export DJANGO_DEBUG=true
python -m pytest tests/test_core.py
RUN_BROWSER_TESTS=true python -m pytest tests/test_browser.py -k announcement
ruff format --check .
ruff check .
pyright
python manage.py check
python -m pytest
```

## Project structure and style

- `announcements/`: models, dismissal/history views, admin, URLs, and migration.
- `templates/base.html`: shared header button, count badge, and announcement dialog markup.
- `templates/announcements/history.html`: announcement history page.
- `static/core/announcements.js`: dependency-free dialog interaction.
- `static/core/site.css`: responsive styles using the existing design tokens.
- `tests/test_announcements.py`: model-backed rendering, dismissal persistence, history, and safe redirects.
- `tests/test_browser.py`: modal, heading dismissal, count, and history coverage.

Use native semantic elements and the existing BEM-like class naming convention.
Keep user-facing copy in the template so Django auto-escaping remains the default.

## Testing strategy

- Render and model tests cover the seeded announcement, count, per-user/session
  dismissal, history, staff-only reannouncement, dismissal reset, and external
  redirect rejection.
- Browser tests cover opening/closing, heading dismissal, count update, and
  navigation to history.
- Full regression suite: all existing Django tests continue to pass.

## Boundaries

- Always: preserve semantic keyboard behavior, visible focus, responsive layout,
  the existing header brand, and the current URL.
- Ask first: audience targeting, scheduling, or more advanced saved-announcement
  behavior.
- Never: add a dependency for this interaction, redirect to an announcement page,
  or weaken existing security/configuration defaults.

## Ordered tasks

### Task 1: Add the announcement data model

- Acceptance: migrations create the test announcement and dismissal records can be
  associated with a user or session.
- Verify: `pytest tests/test_announcements.py`.
- Files: `announcements/`, `config/settings.py`, and `tests/test_announcements.py`.

### Task 2: Implement the accessible modal slice

- Acceptance: the header shows the active count; the panel lists active records;
  dismissal clears the list and history lists all records.
- Verify: focused Django and browser tests pass with no console errors.
- Files: `announcements/`, `templates/`, `static/core/announcements.js`, and
  `static/core/site.css`.

### Task 3: Complete regression and quality verification

- Acceptance: application checks, lint, types, the full test suite, diff hygiene,
  and browser verification pass or any unavailable prerequisite is reported.
- Verify: run the commands above and inspect the final diff for secrets and
  unrelated changes.

## Success criteria

- The green banner visibly contains an Announcements button.
- Activating the button opens an accessible modal containing exactly one test
  announcement attributed to Admin.
- Opening and closing the modal never changes the page URL.
- Mouse and keyboard users can close the modal and continue from the trigger.
- Existing application behavior remains unchanged.
