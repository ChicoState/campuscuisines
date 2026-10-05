from __future__ import annotations

import boto3
from botocore.config import Config
from django.conf import settings
from django.core.exceptions import PermissionDenied

from accounts.models import User
from core.models import ImageAsset

SIGNED_URL_EXPIRY_SECONDS = 5 * 60


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

    browser_storage = boto3.client(
        "s3",
        aws_access_key_id=settings.OBJECT_STORAGE_ACCESS_KEY,
        aws_secret_access_key=settings.OBJECT_STORAGE_SECRET_KEY,
        endpoint_url=settings.OBJECT_STORAGE_PUBLIC_ENDPOINT,
        region_name=settings.OBJECT_STORAGE_REGION,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    return browser_storage.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.OBJECT_STORAGE_BUCKET, "Key": asset.file.name},
        ExpiresIn=SIGNED_URL_EXPIRY_SECONDS,
    )
