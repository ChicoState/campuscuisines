from __future__ import annotations

from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

from accounts.models import User
from core.models import ImageAsset

TEST_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": settings.STORAGES["staticfiles"],
}


def image_asset(*, uploaded_by: User) -> ImageAsset:
    object_key = default_storage.save(
        f"images/{get_random_string(12)}.png", ContentFile(b"image bytes")
    )
    return ImageAsset.objects.create(
        file=object_key,
        alt_text="A campus meal",
        uploaded_by=uploaded_by,
    )


@pytest.mark.django_db
@override_settings(STORAGES=TEST_STORAGES)
def test_soft_delete_hides_an_asset_without_removing_its_storage_object() -> None:
    user = User.objects.create_user(
        username="image-owner", password=get_random_string(32)
    )
    asset = image_asset(uploaded_by=user)
    object_key = asset.file.name

    asset.soft_delete()

    assert not ImageAsset.objects.filter(pk=asset.pk).exists()
    deleted_asset = ImageAsset.all_objects.get(pk=asset.pk)
    assert deleted_asset.deleted_at is not None
    assert default_storage.exists(object_key)


@pytest.mark.django_db
@override_settings(STORAGES=TEST_STORAGES)
def test_soft_deleted_asset_cannot_receive_a_signed_url() -> None:
    from django.core.exceptions import PermissionDenied

    from core.services.images import signed_image_url

    user = User.objects.create_user(
        username="image-owner", password=get_random_string(32)
    )
    asset = image_asset(uploaded_by=user)
    asset.soft_delete()

    with patch.object(asset.file.storage, "url") as storage_url:
        with pytest.raises(PermissionDenied):
            signed_image_url(asset, user)

    storage_url.assert_not_called()


@pytest.mark.django_db
@override_settings(STORAGES=TEST_STORAGES)
def test_soft_deleted_asset_is_not_retrievable_from_the_image_detail_view(
    client,
) -> None:
    user = User.objects.create_user(
        username="image-owner", password=get_random_string(32)
    )
    asset = image_asset(uploaded_by=user)
    asset.soft_delete()
    client.force_login(user)

    response = client.get(reverse("image-detail", kwargs={"pk": asset.pk}))

    assert response.status_code == 404


@pytest.mark.django_db
@override_settings(STORAGES=TEST_STORAGES)
def test_purge_deleted_images_removes_only_expired_assets() -> None:
    user = User.objects.create_user(
        username="image-owner", password=get_random_string(32)
    )
    expired_asset = image_asset(uploaded_by=user)
    recent_asset = image_asset(uploaded_by=user)
    active_asset = image_asset(uploaded_by=user)
    expired_object_key = expired_asset.file.name
    recent_object_key = recent_asset.file.name

    expired_asset.soft_delete()
    recent_asset.soft_delete()
    ImageAsset.all_objects.filter(pk=expired_asset.pk).update(
        deleted_at=timezone.now() - timedelta(days=31)
    )
    ImageAsset.all_objects.filter(pk=recent_asset.pk).update(
        deleted_at=timezone.now() - timedelta(days=29)
    )

    output = StringIO()
    call_command("purge_deleted_images", stdout=output)

    assert not ImageAsset.all_objects.filter(pk=expired_asset.pk).exists()
    assert not default_storage.exists(expired_object_key)
    assert ImageAsset.all_objects.filter(pk=recent_asset.pk).exists()
    assert default_storage.exists(recent_object_key)
    assert ImageAsset.objects.filter(pk=active_asset.pk).exists()
    assert "Purged 1 image asset." in output.getvalue()

    second_output = StringIO()
    call_command("purge_deleted_images", stdout=second_output)

    assert "Purged 0 image assets." in second_output.getvalue()


@pytest.mark.django_db
@override_settings(STORAGES=TEST_STORAGES)
def test_purge_deleted_images_keeps_the_record_when_storage_deletion_fails() -> None:
    user = User.objects.create_user(
        username="image-owner", password=get_random_string(32)
    )
    asset = image_asset(uploaded_by=user)
    asset.soft_delete()
    ImageAsset.all_objects.filter(pk=asset.pk).update(
        deleted_at=timezone.now() - timedelta(days=31)
    )
    error_output = StringIO()

    with patch.object(
        default_storage, "delete", side_effect=RuntimeError("storage-secret")
    ):
        call_command("purge_deleted_images", stderr=error_output)

    assert ImageAsset.all_objects.filter(pk=asset.pk).exists()
    assert f"Failed to purge image asset {asset.pk}." in error_output.getvalue()
    assert "storage-secret" not in error_output.getvalue()
