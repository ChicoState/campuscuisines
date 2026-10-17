from __future__ import annotations

import io

import pytest
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from core.models import ImageAsset
from reviews.models import Review, ReviewImage

TEST_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": settings.STORAGES["staticfiles"],
}


def valid_image() -> SimpleUploadedFile:
    from PIL import Image

    image_data = io.BytesIO()
    Image.new("RGB", (20, 20), color="gold").save(image_data, format="PNG")
    return SimpleUploadedFile("campus-meal.png", image_data.getvalue())


def review() -> Review:
    return Review.objects.create(  # type: ignore[reportAttributeAccessIssue]
        dish_name="Mushroom ramen",
        reviewer_name="Avery",
        rating=4,
        text="Warm, savory, and excellent.",
    )


@pytest.mark.django_db
def test_review_image_allows_only_one_image_per_review() -> None:
    first_asset = ImageAsset.objects.create(
        file="images/first.png", alt_text="First ramen photo"
    )
    second_asset = ImageAsset.objects.create(
        file="images/second.png", alt_text="Second ramen photo"
    )
    posted_review = review()

    ReviewImage.objects.create(review=posted_review, image=first_asset)

    with pytest.raises(IntegrityError):
        ReviewImage.objects.create(review=posted_review, image=second_asset)


@pytest.mark.django_db
@override_settings(DEBUG=True, STORAGES=TEST_STORAGES)
def test_debug_review_submission_attaches_and_publishes_an_uploaded_image(
    client,
) -> None:
    client.force_login(
        User.objects.create_user(
            username="reviewer", email="reviewer@csuchico.edu", password="unused"
        )
    )
    response = client.post(
        reverse("home"),
        {
            "dish_name": "Mushroom ramen",
            "reviewer_name": "Avery",
            "rating": 4,
            "text": "Warm, savory, and excellent.",
            "image": valid_image(),
        },
    )

    posted_review = Review.objects.get()  # type: ignore[reportAttributeAccessIssue]
    review_image = ReviewImage.objects.get()

    assert response.status_code == 302
    assert review_image.review == posted_review
    assert review_image.image.alt_text == "Photo of Mushroom ramen"
    assert review_image.image.caption == ""
    assert review_image.image.published_at is not None
    assert default_storage.exists(review_image.image.file.name)


@pytest.mark.django_db
@override_settings(DEBUG=False, STORAGES=TEST_STORAGES)
def test_non_debug_review_submission_rejects_an_image_without_persisting_data(
    client,
) -> None:
    client.force_login(
        User.objects.create_user(
            username="reviewer", email="reviewer@csuchico.edu", password="unused"
        )
    )
    response = client.post(
        reverse("home"),
        {
            "dish_name": "Mushroom ramen",
            "reviewer_name": "Avery",
            "rating": 4,
            "text": "Warm, savory, and excellent.",
            "image": valid_image(),
        },
    )

    assert response.status_code == 200
    assert (
        "Image uploads are only available in local debug mode."
        in response.content.decode()
    )
    assert not Review.objects.exists()  # type: ignore[reportAttributeAccessIssue]
    assert not ImageAsset.objects.exists()
    assert not ReviewImage.objects.exists()


@pytest.mark.django_db
def test_homepage_renders_an_attached_published_review_image(
    client, monkeypatch
) -> None:
    image = ImageAsset.objects.create(
        file="images/ramen.png",
        alt_text="Photo of Mushroom ramen",
        published_at=timezone.now(),
    )
    ReviewImage.objects.create(review=review(), image=image)
    monkeypatch.setattr(
        "core.views.signed_image_url",
        lambda _image, _viewer: "https://images.test/ramen",
    )

    response = client.get(reverse("home"))

    content = response.content.decode()
    assert 'class="review__image"' in content
    assert 'src="https://images.test/ramen"' in content
    assert 'alt="Photo of Mushroom ramen"' in content


@pytest.mark.django_db
def test_homepage_omits_a_soft_deleted_review_image(client, monkeypatch) -> None:
    image = ImageAsset.objects.create(
        file="images/ramen.png",
        alt_text="Photo of Mushroom ramen",
        published_at=timezone.now(),
    )
    ReviewImage.objects.create(review=review(), image=image)
    image.soft_delete()
    monkeypatch.setattr(
        "core.views.signed_image_url", lambda _image, _viewer: "unexpected"
    )

    response = client.get(reverse("home"))

    assert 'class="review__image"' not in response.content.decode()
