# Modular Navigation and Home-Page Content Plan

## Summary

Reorganize Campus Cuisines into four bookmarkable, modular pages with shared top
navigation:

1. Home
2. Reviews
3. Menu
4. About Us

The Menu tab will include campus dining menus, schedules, and pricing.

Each tab should be independently extendable. Adding a new tab or adding
features to one tab should require minimal changes to unrelated tabs.

## Modular navigation design

- Use a shared accessible navigation component in `templates/base.html` with
  semantic `<nav aria-label="Primary navigation">` markup.
- Define navigation entries centrally with a display label, URL name, ordering,
  and active-route matching rules.
- Render tabs from that shared definition rather than duplicating links across
  templates.
- Mark the current page with `aria-current="page"`.
- Treat nested routes as belonging to their parent tab: future nested review
  routes keep Reviews active. Image upload/detail routes remain direct routes
  without a current top-navigation tab.
- Keep each tab's implementation isolated with a dedicated route, view or view
  module, template, and tests.
- Adding a new tab should involve adding its route, page implementation,
  navigation definition, and tests without modifying existing tab behavior.
- Adding features to one tab should not require changes to other tab templates
  or views except where shared components are intentionally extended.
- Keep shared concerns limited to the base layout, navigation styling,
  accessibility behavior, and common design tokens.

## Key changes

- Add routes:
  - `/` → Home
  - `/reviews/` → Reviews
  - `/images/` → Images gallery
  - `/map/` → Menu placeholder
  - `/about/` → About Us
  - `/account/` → Account placeholder
- Move the full review form/feed to `/reviews/`.
- Preserve legacy Home review POST behavior and redirect successful submissions
  to `/reviews/`.
- Add an Images gallery for published, non-deleted assets while preserving
  existing upload/detail routes.
- Add a Menu page with a placeholder message and no menu integration
  integration yet.
- Add static About Us and Account pages.
- Keep Home as a landing page with welcome content and a concise Reviews
  preview.
- Preserve the existing skip-to-content link, visible keyboard focus states,
  and responsive behavior.
- Ensure navigation remains usable at narrow widths through wrapping or
  horizontal scrolling without hiding tabs.

## Ordered tasks

- [x] Establish the modular navigation structure.
  - Add centralized tab metadata.
  - Render navigation from that metadata.
  - Implement active-route matching and `aria-current`.
  - Verify adding a hypothetical tab requires no changes to unrelated page
    templates.

- [x] Add named routes and isolated page implementations for Reviews, Images,
  Menu, About Us, and Account.
  - Verify each route returns the correct page and status code.

- [x] Extract review behavior into the Reviews page while preserving legacy Home
  POST compatibility.
  - Verify submission, validation, ordering, timestamps, escaped content, and
    review-image behavior.

- [x] Add the published Images gallery (direct route only; not a current top-nav tab).
  - Verify published, unpublished, deleted, and empty-gallery behavior.
  - Verify image routes remain directly available without adding an Images tab.

- [x] Add the Menu placeholder page.
  - Verify it renders the Menu heading and placeholder message without external
    integration.

- [x] Add shared responsive navigation styling.
  - Verify the order is Home, Reviews, Menu, About Us.
  - Verify keyboard focus, skip-link behavior, active state, mobile layout, and
    screen-reader semantics.

- [x] Convert Home into the landing page.
  - Preserve welcome content.
  - Keep the homepage focused on welcome content and the Reviews preview.
  - Add a concise Reviews preview.
  - Remove the full review form/feed from Home.

- [x] Update README documentation and run:
  `git diff --check`, `python manage.py check`, `pytest`,
  `ruff format --check .`, `ruff check .`, `pyright`, and browser tests when
  Chromium is available.

## Interfaces and data

- New URL names: `reviews`, `images`, `map`, `about`, and `account`.
- Existing URL names remain available: `home`, `image-upload`, and
  `image-detail`.
- The navigation metadata is the extension point for future tabs.
- No database models, migrations, dependencies, authentication flows, map
  integrations, or external APIs are required.
- Menu content will cover campus dining menus, schedules, and pricing.
- Existing image privacy, publication, and signed-URL rules remain unchanged.

## Test scenarios

- Navigation renders all four tabs in the required order and omits Images and Account.
- Current pages and nested routes receive the correct active state.
- `aria-current="page"` appears only on the active tab.
- Keyboard users can reach and activate every tab.
- The skip link continues to move focus to the main content.
- Navigation remains usable at 320px and desktop widths.
- A new navigation definition can be added without modifying unrelated page
  templates.
- Menu and Account render their placeholder content.
- Home renders the welcome content and Reviews preview without a visit-planning
  section or Recent Images preview.
- Reviews, Images, About Us, image upload, and image detail regression tests
  pass.
- Legacy review POST behavior still creates a review and redirects to
  `/reviews/`.

## Assumptions

- The navigation is server-rendered and does not require JavaScript.
- Each tab is a separate page rather than an in-page section.
- Menu is intentionally empty except for a user-facing placeholder.
- Account is intentionally empty except for a user-facing placeholder.
