# Announcement Modal Specification and Plan

## Objective

Add an Announcements button to the green site header. Activating it opens an
in-page modal containing one test announcement from Admin without changing the
current URL or navigating away from the page.

## Scope and decisions

- The button is available in the shared green header on every page.
- A native HTML `dialog` provides modal semantics, focus containment, and Escape
  handling without a new dependency.
- The first release contains exactly one static placeholder announcement:
  "Test announcement," attributed to Admin, with the body "This is a test
  announcement."
- This slice does not add an announcement database model, Django admin editing,
  authentication, an API, read/unread state, or notification counts.
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

- `templates/base.html`: shared header button and announcement dialog markup.
- `static/core/announcements.js`: dependency-free dialog interaction.
- `static/core/site.css`: responsive styles using the existing design tokens.
- `tests/test_core.py`: server-rendered structure and single-announcement checks.
- `tests/test_browser.py`: URL-preserving open/close interaction coverage.

Use native semantic elements and the existing BEM-like class naming convention.
Keep user-facing copy in the template so Django auto-escaping remains the default.

## Testing strategy

- Render test: the homepage includes the header button, dialog, one announcement,
  Admin attribution, and the JavaScript asset.
- Browser test: opening the modal keeps the URL unchanged; the announcement is
  visible; closing it hides the modal and restores focus to the trigger.
- Full regression suite: all existing Django tests continue to pass.

## Boundaries

- Always: preserve semantic keyboard behavior, visible focus, responsive layout,
  the existing header brand, and the current URL.
- Ask first: persistence, Django admin management, audience targeting, scheduling,
  or more than one announcement.
- Never: add a dependency for this interaction, redirect to an announcement page,
  or weaken existing security/configuration defaults.

## Ordered tasks

### Task 1: Specify and test the announcement contract

- Acceptance: focused tests describe the shared button, single announcement, and
  modal interaction before implementation.
- Verify: the focused tests fail against the pre-feature code.
- Files: this plan, `tests/test_core.py`, and `tests/test_browser.py`.

### Task 2: Implement the accessible modal slice

- Acceptance: the button opens the one-announcement dialog without navigation;
  all three close paths work; focus returns to the button; styling fits the
  existing visual system at mobile and desktop widths.
- Verify: focused Django and browser tests pass with no console errors.
- Files: `templates/base.html`, `static/core/announcements.js`, and
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
