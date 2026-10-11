# Dish Reviews MVP Implementation Plan

## Summary

Keep the current informational Campus Cuisines homepage introduction. Add a
public review-submission section and newest-first review feed below it. Anyone
can submit a dish name, reviewer name, a whole 1–5 star rating, and up-to-500-
character review; valid submissions publish immediately.

No account, dish catalog, filtering, station data, moderation, favorites,
uploads, or rate limiting is included.

## Key changes

- Add a feature-owned `reviews` Django app and register it in Django settings.
- Add a `Review` model with:
  - `dish_name`: required, maximum 100 characters.
  - `reviewer_name`: required, maximum 50 characters.
- `rating`: integer whole-star values `1`–`5`; enforce this range in validation
  and with a database constraint. The rating picker describes each selection:
  1 = Bad, 2 = Mediocre, 3 = Fine, 4 = Good, and 5 = Amazing. Published
  reviews display only their star count, without the description.
  - `text`: required, maximum 500 characters.
  - `created_at`: automatic timestamp, displayed beneath the review body and
    used for newest-first ordering.
- Keep `/` as the homepage. Its view renders the current welcome content first,
  followed by the review form and feed.
- Use a Django `ModelForm`; render rating as five accessible native radio
  controls, visually presented as five clickable, literal star glyphs. Selecting
  a star fills it and every star to its left yellow; unselected stars remain
  visibly muted. Show a visible selected score and description alongside
  keyboard operation, visible focus, validation errors, and accessible rating
  text such as “4 out of 5 stars — Good.”
- Render all reviews below the form in `-created_at, -id` order. Each entry
  shows dish name, reviewer name, visual/textual rating, review text, and its
  timestamp beneath the text. Before the first post, show an empty-state
  message.
- Use Django CSRF protection, server-side validation, ORM access, and template
  auto-escaping. Public posts publish immediately; anonymous-spam protection is
  intentionally deferred and documented.
- Keep review-specific model, form, and rendering logic in `reviews`; extend
  the existing homepage template and shared CSS without removing its
  introductory content.

## Ordered tasks

- [ ] Create the `reviews` app, model, initial migration, and Django admin
  registration.
  - Acceptance: valid reviews persist; timestamps are assigned automatically;
    ratings outside 1–5 cannot persist through the database constraint.
  - Verify: focused model/migration tests and `python manage.py check`.

- [ ] Connect review creation and listing to the existing homepage.
  - Acceptance: the original welcome section remains at the top; GET renders
    the review form and newest-first feed below it; valid POST creates one
    review and redirects; invalid POST retains entered values and shows field
    errors.
  - Verify: Django client tests for valid, missing, oversized, and invalid-
    rating submissions.

- [ ] Implement the responsive review UI and accessible five-star picker.
  - Acceptance: each star is selectable by mouse and keyboard; selecting a
    star highlights it and all preceding stars; selected and displayed ratings
    include non-visual text; each review shows its
    timestamp beneath its body; an empty feed has a meaningful message.
  - Verify: browser test for form submission, visible feed entry, and
    timestamp; manual keyboard checks at mobile and desktop widths.

- [ ] Update documentation and repository tests.
  - Acceptance: docs match delivered behavior and deferred scope; homepage
    tests verify welcome content, review functionality, and timestamp
    rendering.
  - Verify: `git diff --check`, test suite, and static checks.

## Test plan

- Model/form validation: required values, 50/100/500-character boundaries, and
  only the five allowed whole-star values.
- Integration: a submitted valid review is saved once, redirects to `/`,
  appears before older reviews, and preserves the welcome section.
- UI: the welcome content, empty feed, validation errors, visible five-star
  selection with descriptions, rendered review star count without a
  description, timestamp placement, and escaped user-supplied review content.
- Full verification: `python scripts/verify_infrastructure.py`, `ruff format
  --check .`, `ruff check .`, `pyright`, `python manage.py check`, `pytest`,
  and `./scripts/smoke.sh`.

## Assumptions and defaults

- “Newest first” means descending `created_at`, then descending ID to resolve
  same-timestamp ties.
- Timestamps use the project’s configured `America/Los_Angeles` timezone and
  are rendered in a reader-friendly local date-and-time format.
- Reviews are anonymous: `reviewer_name` is self-entered text, not an account
  identity.
- No new dependencies, APIs, uploads, or authentication flow are needed for
  this MVP.
- This is the initial reviews schema; no pre-existing review ratings are
  migrated.
