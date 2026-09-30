# Implementation Plan: Reusable Image Uploads

## Status

Approved product direction. This plan guides the image-asset foundation; a later
review specification will define the review model and its image cardinality.

## Reviewed outcome

Campus Cuisines needs a reusable image asset capability: an authorized user uploads
an image, Django persists an initially private and unattached image record, and a
later publishing action can make it renderable wherever a product feature needs it
(for example, a review). A standalone gallery is explicitly out of scope.

"Stored in the database" means PostgreSQL stores the image record and object-storage
key. Image bytes are stored in MinIO locally and provider object storage in
production. This follows the existing infrastructure plan and avoids putting large
binary blobs in relational database rows.

## Proposed first-version boundaries

### In scope

- Uploading validated raster images through a Django workflow. Before account flows
  exist, local development may use an anonymous-only development path; production
  uploads require an authenticated user. The development path may also attach those
  anonymous assets to development reviews so the later integration can be built and
  tested before account screens exist.
- Persisting reusable image metadata and a storage key in PostgreSQL.
- Rendering an image record in a Django template, including accessible alternate text.
- Local MinIO and future production object-storage support.
- Automated model, upload, view, and browser verification.

### Out of scope

- A gallery, image browsing page, or image search.
- Reviews, restaurants, menu items, or any other product model not yet designed.
- Public anonymous uploads, moderation, image transformation, thumbnails, CDN work,
  and image-editing tools.
- Storing binary image files directly in PostgreSQL.

## Proposed architecture

```text
Authorized uploader
       |
       | multipart POST
       v
Django upload form --> validation --> private object storage (MinIO locally)
                                   |               |
                                   v               v
                       PostgreSQL ImageAsset    image bytes
                                   |
                                   | later publish action associates the asset
                                   v
                         public review/feature renders a controlled image URL
```

The proposed `core.ImageAsset` model is deliberately an asset only; it has no
generic foreign key and no guessed relationship to future product models. When a
review feature is specified, it can reference one or more `ImageAsset` records with
an explicit relationship chosen for that workflow.

Suggested fields:

- `file`: `ImageField`, whose value is a generated object-storage key.
- `alt_text`: required text used in every rendered image.
- `caption`: optional plain text.
- `created_at`: immutable upload timestamp.
- `uploaded_by`: required relationship to the authenticated uploader in production;
  nullable only for disposable local-development uploads before accounts exist.
- `published_at`: nullable timestamp. It is `NULL` for newly uploaded assets and is
  set only by an explicit publishing action, such as publishing an associated review.
  Public pages may render only assets whose `published_at` is set.
- `deleted_at`: nullable soft-delete timestamp. A deleted asset is excluded from all
  normal queries and its delivery authorization is revoked immediately.

The upload key should use a server-generated UUID, such as
`images/<uuid>.<extension>`; never derive a storage path from the original filename.

## Design decisions already supported by the repository

- Use Django 5.2, PostgreSQL, `django-storages`, boto3, and the existing MinIO
  Compose service.
- Add Pillow as an explicit, hash-locked dependency because Django `ImageField`
  validates image content through it.
- Configure Django's default media storage separately from WhiteNoise static-file
  storage. Uploads must never go in `STATIC_ROOT`.
- Create the development bucket before uploads; production bucket provisioning and
  credentials remain external deployment concerns.
- Keep the upload bucket private. Use signed object-storage URLs with a five-minute
  expiry for template rendering; generate a URL only after Django has verified that
  the request may see the image. Do not expose new uploads as public bucket URLs.

## Security and authorization rules

- Allow JPEG, PNG, and WebP only after inspecting image content, rather than trusting
  a filename or request MIME type.
- Initial limits: 5 MiB uploaded size and 16 megapixels decoded dimensions; reject
  corrupt files and decompression bombs.
- Reject SVG, GIF, HEIC, PDFs, and arbitrary file uploads for this first version.
- In non-debug environments, require authentication for every upload and require an
  asset to belong to the acting user before that user can view, attach, publish, or
  delete it. Use normal Django CSRF protection and server-generated storage names.
- Permit anonymous uploads only when `DJANGO_DEBUG=true`; this branch must be
  unavailable when `DJANGO_DEBUG=false`, including when an authentication rollout is
  incomplete. In that same debug-only mode, anonymous assets may be attached to and
  published with development reviews. Development uploads and reviews are
  intentionally disposable.
- Soft-delete image records: remove them from every user-visible query and stop
  generating URLs immediately. A URL issued before deletion can remain usable only
  until its five-minute expiry. Retain the private object and metadata for 30 days,
  then permanently purge both through an auditable cleanup task.
- Store only configuration references and secrets in environment variables; do not
  commit populated credential files.

## Implementation tasks

1. **Add the image dependency and storage settings.** Add Pillow to
   `requirements.in`, regenerate both hash-locked requirement files with the
   repository's documented pip-tools command, and configure the Django default media
   storage for the existing MinIO service. Provision the local bucket deterministically
   before the application accepts uploads.

   - Acceptance: `ImageField` saves bytes to MinIO and never to `STATIC_ROOT` or the
     application container filesystem.
   - Likely files: `requirements.in`, both lock files, `config/settings.py`,
     `compose.yml`, `.env.example`, and a setup script or Compose init service.

2. **Create the reusable asset model and migration.** Add `core.ImageAsset` with the
   fields above, UUID-based upload paths, a default manager that excludes soft-deleted
   records, and a Django migration. Add `Pillow`-based validation for the supported
   types, size, and pixel limits.

   - Acceptance: a valid upload creates exactly one database record and one private
     storage object; rejected input creates neither.
   - Likely files: `core/models.py`, `core/migrations/`, `core/validators.py`, and
     model tests.

3. **Implement the upload and private-asset application workflow.** Add a Django
   form/view/URL for uploads. In production-like settings it requires the authenticated
   owner; before account screens exist, the same route has a tightly tested anonymous
   branch only when `DJANGO_DEBUG=true`. Do not make an Admin-only workflow the public
   contract.

   - Acceptance: a non-debug anonymous request is rejected even if it bypasses the
     UI; a debug-mode anonymous request succeeds only locally.
   - Likely files: `core/forms.py`, `core/views.py`, `core/urls.py`,
     `config/urls.py`, templates, and view tests.

4. **Implement controlled rendering and publication.** Provide a small service or
   template helper that produces a signed URL only after the requester is authorized.
   A private asset can be rendered by its owner in an authorized draft context; a
   public page can render an asset only after the owning workflow sets `published_at`.

   - Acceptance: newly uploaded assets are not publicly retrievable; publishing makes
     an associated asset renderable; soft deletion removes it from the application
     immediately and any already-issued URL expires within five minutes.
   - Likely files: `core/services/images.py` (or equivalent), views/templates, and
     authorization tests.

5. **Integrate with reviews when the review feature is built.** The review feature
   defines an explicit relationship to `ImageAsset`; it must not use a generic foreign
   key. In debug mode, tests must cover anonymous upload → attach to development review
   → publish review → render image. In non-debug mode, enforce the review author's
   ownership of any attached asset.

   - Acceptance: the review flow works before account screens exist in local debug
     mode and does not allow anonymous production use.
   - Dependency: Task 4 and the future review specification.

6. **Implement retention cleanup.** Add an idempotent Django management command that
   finds soft-deleted assets older than 30 days, deletes their storage objects, then
   removes their database records. Run it once daily in production and manually in
   local development. Plan the production scheduler and least-privilege identity as a
   separate infrastructure change before release.

   - Acceptance: retries are safe; objects younger than 30 days remain; older objects
     and their records are both removed; failures are logged without exposing secrets.
   - Likely files: `core/management/commands/`, tests, README, and later deployment
     infrastructure.

7. **Document and verify the vertical slices.** Add an ADR for object storage,
   privacy, and retention; document changed developer commands; execute the full
   repository verification suite after each completed slice.

## Verification targets

- A permitted uploader can submit a valid image and receives a usable image record.
- PostgreSQL contains image metadata and the generated storage key; MinIO contains
  the corresponding bytes.
- Disallowed, corrupt, oversized, and excessive-dimension files fail safely.
- A Django template renders the selected record's storage URL and required alt text.
- When no record is supplied, the consuming page renders without an image error.
- `python scripts/verify_infrastructure.py`, Ruff, Pyright, Django checks, pytest,
  browser tests, and `./scripts/smoke.sh` pass before merge.

## Decision record and intentional deferral

1. **Upload authority:** the eventual workflow permits any
   authenticated user to upload through an application form. Until accounts exist,
   local development permits anonymous uploads only under `DJANGO_DEBUG=true`; this
   is not a production capability.
2. **Initial visibility:** uploads are private and unattached by
   default. A later, explicit user publishing action, such as publishing a review,
   makes an associated image public.
3. **Asset lifecycle:** deleting an image hides it and revokes
   access immediately. Keep its private object and metadata for 30 days, then
   permanently delete both.
4. **Retention execution:** an automated production scheduler
   runs the purge once daily. Local development invokes the same Django management
   command manually. The production scheduler resource and its least-privilege
   identity must be included in the later infrastructure implementation plan.
5. **Future review cardinality:** whether a review supports one or many images is
   intentionally deferred to the review specification. It does not block this asset
   foundation, because `ImageAsset` has no guessed review relationship.
