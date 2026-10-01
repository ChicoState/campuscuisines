from __future__ import annotations

import io
import re

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile


def make_image_file(
    *,
    image_format: str = "PNG",
    name: str = "campus-meal.png",
    size: tuple[int, int] = (20, 20),
) -> SimpleUploadedFile:
    from PIL import Image

    image_data = io.BytesIO()
    Image.new("RGB", size, color="gold").save(image_data, format=image_format)
    return SimpleUploadedFile(name, image_data.getvalue())


@pytest.mark.django_db
def test_image_asset_uses_a_uuid_storage_key_without_the_original_filename() -> None:
    from core.models import ImageAsset, image_upload_path

    asset = ImageAsset(
        file="images/existing-object.png",
        alt_text="A campus meal",
    )
    asset.save()

    object_key = image_upload_path(asset, "campus-meal.png")

    assert asset.file.name == "images/existing-object.png"
    assert re.fullmatch(r"images/[0-9a-f-]{36}\.png", object_key)


def test_image_asset_rejects_an_unsupported_image_format() -> None:
    from core.models import ImageAsset

    asset = ImageAsset(
        file=make_image_file(image_format="GIF", name="animated.gif"),
        alt_text="An animated campus meal",
    )

    with pytest.raises(ValidationError, match="JPEG, PNG, or WebP"):
        asset.full_clean()


def test_image_asset_rejects_corrupt_file_content() -> None:
    from core.models import ImageAsset

    asset = ImageAsset(
        file=SimpleUploadedFile("meal.png", b"not an image"),
        alt_text="A corrupt image",
    )

    with pytest.raises(ValidationError, match="valid image"):
        asset.full_clean()


def test_image_asset_rejects_files_larger_than_five_mebibytes() -> None:
    from core.models import ImageAsset

    asset = ImageAsset(
        file=make_image_file(image_format="BMP", name="meal.bmp", size=(2_000, 1_000)),
        alt_text="An oversized image",
    )

    with pytest.raises(ValidationError, match="5 MiB"):
        asset.full_clean()


def test_image_asset_rejects_images_larger_than_sixteen_megapixels() -> None:
    from core.models import ImageAsset

    asset = ImageAsset(
        file=make_image_file(size=(4_001, 4_000)),
        alt_text="An oversized campus meal",
    )

    with pytest.raises(ValidationError, match="16 megapixels"):
        asset.full_clean()


def test_image_asset_rejects_pillow_decompression_bombs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from PIL import Image

    from core.models import ImageAsset

    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 1)
    asset = ImageAsset(
        file=make_image_file(),
        alt_text="A decompression bomb",
    )

    with pytest.raises(ValidationError, match="valid image"):
        asset.full_clean()
