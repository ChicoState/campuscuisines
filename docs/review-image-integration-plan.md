# Review Image Integration Specification and Plan

## Status

Implemented on 2026-10-11.

## Objective

Let a reviewer optionally select one image while submitting a dish review in local
debug development. The application validates, stores, attaches, and publishes that
image with the review, then renders it alongside the review in the newest-first
homepage feed. Existing reviews without an image remain unchanged.

This completes the deferred review-to-image integration from
`docs/image-upload-plan.md` without adding public production uploads before account
flows exist.

## Confirmed decisions

- A review supports zero or one image in this release.
- The data model will use a feature-owned `ReviewImage` association in `reviews`,
  rather than a generic relation or a field on `ImageAsset`. A database uniqueness
  constraint permits one association per review now; removing that constraint and
  adding ordering later permits multiple images without moving the relationship.
- The upload control uses the review form's multipart submission. It is presented as
  an "Add image" button that opens the native file picker.
- The selected file is the only image field shown to the reviewer. The server sets
  `ImageAsset.alt_text` to `Photo of <dish name>` and leaves `caption` empty.
- Image attachment is available only with `DJANGO_DEBUG=true`. In non-debug mode,
  the homepage must reject any submitted image file and must not create an image
  record, object-storage object, or association. Normal anonymous text-only reviews
  retain their current behavior.
- A valid debug-mode image is marked published atomically with its review so public
  rendering uses `core.services.images.signed_image_url` and its five-minute URL.
- Images are displayed below the review text, constrained with CSS to the review
  card width and a bounded height using `object-fit: cover`; the full source bytes
  are retained and no thumbnail/transformation pipeline is introduced.

## Existing contracts to preserve

- Image bytes remain in private object storage; only metadata and generated keys are
  stored in PostgreSQL.
- `ImageAsset` continues to be independently owned by `core`, with `reviews`
  defining the explicit association.
- JPEG, PNG, and WebP validation, 5 MiB upload limit, 16-megapixel limit, soft
  deletion, and signed URL authorization remain authoritative.
- Templates must use `signed_image_url`; never use storage paths or static URLs.
- Existing reviews have no association and render normally without empty image UI.

## Technical design

```text
debug-mode multipart review POST
        |
        v
Review submission form validates review fields and optional image
        |
        +-- no image --> create and publish text-only review
        |
        +-- image --> create review + ImageAsset + ReviewImage association
                        set ImageAsset.published_at
        |
        v
homepage feed fetches review associations and signs published image URLs
        |
        v
review card renders the responsive, bounded image
```

The `reviews` app will own a `ReviewImage` model with a `ForeignKey` to `Review`
and a `OneToOneField` to `ImageAsset`. A uniqueness constraint on `review` enforces
the first-release cardinality. This keeps `core.ImageAsset` product-neutral while
making the future path explicit: remove the per-review uniqueness constraint and add
an ordering field when multiple images are specified.

The homepage view will prefetch the single association and generate a signed URL
only for its published, non-deleted asset. A soft-deleted asset is omitted rather
than causing the entire feed to fail.

## Commands

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

## Testing strategy

- Model/migration tests: association cardinality, deletion behavior, and compatibility
  with reviews that have no image.
- View tests: debug upload creates an image with generated alt text, association, and
  publication timestamp; invalid image creates no review or image; non-debug uploads
  are rejected; text-only reviews continue to work.
- Rendering tests: signed URL is requested only for an attached published image;
  deleted or missing images do not break the feed; output has correct alt text.
- Browser test: select an image through the review form, publish it, and verify the
  image appears in the submitted review with bounded review-card presentation.

## Boundaries

- Always: validate untrusted image input server-side, enforce CSRF, preserve private
  storage, use signed URLs, and run the stated checks before committing.
- Ask first: authentication changes, production anonymous uploads, new dependencies,
  image transformations, moderation, or changing the one-image constraint.
- Never: expose object keys directly, store image bytes in PostgreSQL or `STATIC_ROOT`,
  use a generic foreign key, or publish anonymous uploads in non-debug mode.

## Ordered implementation tasks

### Task 1: Add the explicit association and migration

- Acceptance: a review can have at most one active `ReviewImage` association; the
  association owns no image bytes; existing reviews remain valid.
- Verify: focused migration/model tests and `DJANGO_DEBUG=true python manage.py check`.
- Likely files: `reviews/models.py`, `reviews/migrations/`, `reviews/admin.py`, and
  `tests/test_review_images.py`.

### Task 2: Add the debug-only review submission slice

- Acceptance: the multipart form accepts an optional validated image in debug mode,
  creates its review and association, assigns generated alt text, and publishes the
  asset. Invalid input leaves no persisted review, asset, or association. Non-debug
  image submission is rejected.
- Verify: focused form/view tests.
- Depends on: Task 1.
- Likely files: `reviews/forms.py`, `core/views.py`, `tests/test_core.py`, and
  `tests/test_review_images.py`.

### Checkpoint: creation and authorization

- All focused tests pass, and text-only submission behavior is unchanged.

### Task 3: Render attached images in the feed

- Acceptance: attached published images display with signed URLs and generated alt
  text; image-less and soft-deleted-image reviews render normally.
- Verify: rendering/view tests.
- Depends on: Tasks 1–2.
- Likely files: `core/views.py`, `templates/core/home.html`, and tests.

### Task 4: Add responsive review-card image styling and browser coverage

- Acceptance: an attached image fits the review card without distortion or layout
  overflow at mobile and desktop widths; browser coverage proves the full flow.
- Verify: browser test and manual responsive checks.
- Depends on: Task 3.
- Likely files: `static/core/site.css`, `tests/test_browser.py`, and template files.

### Task 5: Update durable documentation and complete quality review

- Acceptance: README, agent guidance, and approved plans accurately describe the
  debug-only review image capability and future multi-image path.
- Verify: full command list, `git diff --check`, secret review, and code review.
- Depends on: Tasks 1–4.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Anonymous production upload bypass | Reject uploaded image data when `DEBUG` is false, including crafted POSTs. |
| Orphaned object after a storage failure | Validate before persistence; handle save failures as a form error and retain the existing cleanup lifecycle. |
| Deleted image breaks public feed | Query active assets only and omit an unavailable association during rendering. |
| Future cardinality migration | Keep the association in `reviews` and isolate the one-image restriction in a removable constraint. |

## Success criteria

- In debug mode, a reviewer can add one validated image from the review form and see
  it with the newly published review.
- Image metadata has generated alt text, private object storage retains the bytes,
  and rendering uses a signed URL.
- In non-debug mode, no anonymous image upload or association can be created.
- Existing text-only reviews continue to display normally.
