from __future__ import annotations

import warnings
from typing import Any

from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_000_000
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


def validate_raster_image(uploaded_file: Any) -> None:
    """Validate allowed image content without trusting filename or MIME type."""
    if uploaded_file.size > MAX_IMAGE_BYTES:
        raise ValidationError("Image files must be 5 MiB or smaller.")

    file_object = uploaded_file.file
    original_position = file_object.tell()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            file_object.seek(0)
            with Image.open(file_object) as image:
                image.verify()

            file_object.seek(0)
            with Image.open(file_object) as image:
                if image.format not in ALLOWED_IMAGE_FORMATS:
                    raise ValidationError("Images must be JPEG, PNG, or WebP files.")
                if image.width * image.height > MAX_IMAGE_PIXELS:
                    raise ValidationError("Images must not exceed 16 megapixels.")
                image.load()
    except ValidationError:
        raise
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        OSError,
        SyntaxError,
        UnidentifiedImageError,
    ) as error:
        raise ValidationError("Upload a valid image file.") from error
    finally:
        file_object.seek(original_position)
