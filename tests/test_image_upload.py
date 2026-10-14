from __future__ import annotations

import io

import pytest
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils.crypto import get_random_string

from accounts.models import User
from core.models import ImageAsset

TEST_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": settings.STORAGES["staticfiles"],
}


def valid_image() -> SimpleUploadedFile:
    from PIL import Image

    image_data = io.BytesIO()
    Image.new("RGB", (20, 20), color="gold").save(image_data, format="PNG")
    return SimpleUploadedFile("campus-meal.png", image_data.getvalue())


@pytest.mark.django_db
@override_settings(DEBUG=True, STORAGES=TEST_STORAGES)
def test_debug_mode_allows_anonymous_image_uploads(client) -> None:
    response = client.post(
        reverse("image-upload"),
        {"file": valid_image(), "alt_text": "A campus meal", "caption": "Lunch"},
    )

    asset = ImageAsset.objects.get()

    assert response.status_code == 302
    assert response.url == reverse("image-upload")
    assert asset.uploaded_by is None
    assert default_storage.exists(asset.file.name)


@pytest.mark.django_db
@override_settings(DEBUG=False, STORAGES=TEST_STORAGES)
def test_non_debug_mode_rejects_anonymous_image_uploads(client) -> None:
    get_response = client.get(reverse("image-upload"))
    response = client.post(
        reverse("image-upload"),
        {"file": valid_image(), "alt_text": "A campus meal"},
    )

    assert get_response.status_code == 302
    assert get_response.url == f"/accounts/login/?next={reverse('image-upload')}"
    assert response.status_code == 302
    assert response.url == f"/accounts/login/?next={reverse('image-upload')}"
    assert not ImageAsset.objects.exists()


@pytest.mark.django_db
@override_settings(DEBUG=False, STORAGES=TEST_STORAGES)
def test_non_debug_mode_records_the_authenticated_uploader(client) -> None:
    user = User.objects.create_user(
        username="upload-owner", password=get_random_string(32)
    )
    client.force_login(user)

    response = client.post(
        reverse("image-upload"),
        {"file": valid_image(), "alt_text": "A campus meal"},
    )

    assert response.status_code == 302
    asset = ImageAsset.objects.get()
    assert response.url == reverse("image-detail", kwargs={"pk": asset.pk})
    assert asset.uploaded_by == user


@pytest.mark.django_db
@override_settings(DEBUG=True, STORAGES=TEST_STORAGES)
def test_invalid_upload_creates_no_asset_or_storage_object(client) -> None:
    response = client.post(
        reverse("image-upload"),
        {
            "file": SimpleUploadedFile("not-an-image.png", b"not an image"),
            "alt_text": "Invalid image",
        },
    )

    assert response.status_code == 200
    assert "Upload a valid image" in response.content.decode()
    assert not ImageAsset.objects.exists()
    with pytest.raises(FileNotFoundError):
        default_storage.listdir("images")
