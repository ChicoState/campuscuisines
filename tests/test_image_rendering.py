from __future__ import annotations

from datetime import datetime
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from django.core.exceptions import PermissionDenied
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

from accounts.models import User
from core.models import ImageAsset


def image_asset(
    *, uploaded_by: User, published_at: datetime | None = None
) -> ImageAsset:
    return ImageAsset.objects.create(
        file="images/campus-meal.png",
        alt_text="A campus meal",
        caption="Lunch",
        uploaded_by=uploaded_by,
        published_at=published_at,
    )


@pytest.mark.django_db
def test_new_image_assets_are_unpublished() -> None:
    user = User.objects.create_user(
        username="image-owner", password=get_random_string(32)
    )

    asset = image_asset(uploaded_by=user)

    assert asset.published_at is None


@pytest.mark.django_db
@override_settings(OBJECT_STORAGE_PUBLIC_ENDPOINT="http://browser-storage.test:9000")
def test_signed_image_url_uses_the_browser_reachable_storage_endpoint() -> None:
    from core.services.images import SIGNED_URL_EXPIRY_SECONDS, signed_image_url

    user = User.objects.create_user(
        username="image-owner", password=get_random_string(32)
    )
    asset = image_asset(uploaded_by=user)

    url = signed_image_url(asset, user)

    parsed_url = urlparse(url)
    assert parsed_url.scheme == "http"
    assert parsed_url.netloc == "browser-storage.test:9000"
    assert parsed_url.path == "/campus-cuisines-uploads/images/campus-meal.png"
    assert parse_qs(parsed_url.query)["X-Amz-Expires"] == [
        str(SIGNED_URL_EXPIRY_SECONDS)
    ]


@pytest.mark.django_db
def test_signed_image_url_rejects_non_owners_for_an_unpublished_asset() -> None:
    from core.services.images import signed_image_url

    owner = User.objects.create_user(
        username="image-owner", password=get_random_string(32)
    )
    other_user = User.objects.create_user(
        username="other-user", password=get_random_string(32)
    )
    asset = image_asset(uploaded_by=owner)

    with pytest.raises(PermissionDenied):
        signed_image_url(asset, other_user)


@pytest.mark.django_db
def test_signed_image_url_rejects_anonymous_rendering_of_an_unpublished_asset() -> None:
    from core.services.images import signed_image_url

    user = User.objects.create_user(
        username="image-owner", password=get_random_string(32)
    )
    asset = image_asset(uploaded_by=user)

    with pytest.raises(PermissionDenied):
        signed_image_url(asset, None)


@pytest.mark.django_db
@override_settings(OBJECT_STORAGE_PUBLIC_ENDPOINT="http://browser-storage.test:9000")
def test_signed_image_url_allows_public_rendering_after_publication() -> None:
    from core.services.images import signed_image_url

    user = User.objects.create_user(
        username="image-owner", password=get_random_string(32)
    )
    asset = image_asset(uploaded_by=user, published_at=timezone.now())

    url = signed_image_url(asset, None)

    assert url.startswith("http://browser-storage.test:9000/")


@pytest.mark.django_db
def test_owner_can_render_an_unpublished_image_asset(client) -> None:
    user = User.objects.create_user(
        username="image-owner", password=get_random_string(32)
    )
    asset = image_asset(uploaded_by=user)
    client.force_login(user)

    with patch(
        "core.views.signed_image_url",
        return_value="https://storage.example.test/private-image?signature=token",
    ):
        response = client.get(reverse("image-detail", kwargs={"pk": asset.pk}))

    assert response.status_code == 200
    assert 'src="https://storage.example.test/private-image?signature=token"' in (
        response.content.decode()
    )
    assert 'alt="A campus meal"' in response.content.decode()


@pytest.mark.django_db
def test_non_owner_cannot_render_an_unpublished_image_asset(client) -> None:
    owner = User.objects.create_user(
        username="image-owner", password=get_random_string(32)
    )
    other_user = User.objects.create_user(
        username="other-user", password=get_random_string(32)
    )
    asset = image_asset(uploaded_by=owner)
    client.force_login(other_user)

    response = client.get(reverse("image-detail", kwargs={"pk": asset.pk}))

    assert response.status_code == 403
