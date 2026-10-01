from __future__ import annotations

from typing import Protocol, cast

from django.core.exceptions import PermissionDenied

from accounts.models import User
from core.models import ImageAsset

SIGNED_URL_EXPIRY_SECONDS = 5 * 60


class SignedUrlStorage(Protocol):
    def url(self, name: str, *, expire: int) -> str: ...


def signed_image_url(asset: ImageAsset, viewer: User | None) -> str:
    """Return a short-lived URL only when the viewer may render the asset."""
    if asset.deleted_at is not None:
        raise PermissionDenied("You are not allowed to view this image.")

    is_owner = (
        asset.uploaded_by_id is not None
        and viewer is not None
        and asset.uploaded_by_id == viewer.pk
    )
    if asset.published_at is None and not is_owner:
        raise PermissionDenied("You are not allowed to view this image.")

    if not asset.file.name:
        raise ValueError("An image asset must have a stored file.")

    storage = cast(SignedUrlStorage, asset.file.storage)
    return storage.url(asset.file.name, expire=SIGNED_URL_EXPIRY_SECONDS)
