from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.validators import validate_raster_image


def image_upload_path(_: models.Model, filename: str) -> str:
    """Generate a server-controlled object-storage key for an uploaded image."""
    return f"images/{uuid4()}{Path(filename).suffix.lower()}"


class ActiveImageAssetManager(models.Manager):
    """Return only image assets that have not been soft deleted."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class ImageAsset(models.Model):
    """Private reusable image metadata backed by configured object storage."""

    objects: ActiveImageAssetManager
    all_objects: models.Manager
    uploaded_by_id: int | None

    file = models.ImageField(
        upload_to=image_upload_path, validators=[validate_raster_image]
    )
    alt_text = models.CharField(max_length=255)
    caption = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="image_assets",
    )

    objects = ActiveImageAssetManager()
    all_objects = models.Manager()

    def soft_delete(self) -> None:
        """Hide this asset while retaining its record and private object."""
        if self.deleted_at is None:
            self.deleted_at = timezone.now()
            self.save(update_fields=["deleted_at"])

    class Meta:
        ordering = ["-created_at"]
