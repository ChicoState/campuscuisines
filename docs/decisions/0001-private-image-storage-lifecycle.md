# ADR-001: Keep image assets private in object storage with recoverable deletion

## Status

Accepted

## Date

2026-10-01

## Context

Campus Cuisines needs reusable image assets before reviews or other food-content
models are specified. Images are user-controlled binary data, so they must not be
served as static files or stored as PostgreSQL blobs. The asset must stay private
until a feature deliberately publishes it, and accidental deletion needs a recovery
window without leaving it available to users.

Local development uses MinIO, while production will use provider-supported object
storage. Both require a stable model for metadata, storage keys, authorization, and
eventual cleanup.

## Decision

- Store image bytes in the configured private S3-compatible object store and store
  the UUID-generated object key plus metadata in PostgreSQL `ImageAsset` records.
  The local Compose `minio-init` service creates the bucket and disables anonymous
  access before Django starts.
- Accept only Pillow-verified JPEG, PNG, and WebP files. The implementation limits
  uploads to 5 MiB and 16 megapixels, rejects corrupt/decompression-bomb images, and
  does not accept SVG, GIF, HEIC, PDFs, or arbitrary files.
- In non-debug environments, uploads require an authenticated owner. Anonymous
  uploads are allowed only while `DJANGO_DEBUG=true` for disposable local work.
- Keep a new asset private. `signed_image_url` creates a five-minute signed URL only
  for the owner’s authenticated draft view or after an owning feature sets
  `published_at`. The helper refuses deleted assets.
- Soft-delete through `ImageAsset.soft_delete()`. The default manager hides deleted
  rows immediately; `all_objects` exists only for recovery and retention work.
- Run `python manage.py purge_deleted_images` once daily in production through a
  separately provisioned least-privilege scheduler. The command deletes objects
  before database records, retains a record when object deletion fails, writes only
  the asset identifier on failure, and can safely be rerun. Local developers invoke
  the command manually.

## Alternatives considered

### Public bucket URLs

Rejected because a guessed or copied URL would bypass Django authorization and a
private draft could become visible before publication.

### Image blobs in PostgreSQL

Rejected because large binary data complicates relational storage, backups, and
delivery while object storage already matches the selected infrastructure plan.

### Immediate hard deletion

Rejected because it prevents recovery from accidental removal. Retaining the private
object and metadata for 30 days provides a bounded recovery period.

## Consequences

- A URL issued before deletion can remain usable only until its five-minute expiry;
  no new URL is issued after soft deletion.
- Operators must ensure the production scheduler runs daily and has permission only
  to delete objects from the upload bucket and records through the application.
- This repository has no review model, explicit publish endpoint, delete UI, gallery,
  or public image browsing page. The future review feature must define the explicit
  relationship and call the established authorization and lifecycle APIs.
