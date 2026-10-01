from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.db import models

from core.validators import validate_raster_image


def image_upload_path(_: models.Model, filename: str) -> str:
    """Generate a server-controlled object-storage key for an uploaded image."""
    return f"images/{uuid4()}{Path(filename).suffix.lower()}"


class ImageAsset(models.Model):
    """Private reusable image metadata backed by configured object storage."""

    file = models.ImageField(
        upload_to=image_upload_path, validators=[validate_raster_image]
    )
    alt_text = models.CharField(max_length=255)
    caption = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="image_assets",
    )

    class Meta:
        ordering = ["-created_at"]
