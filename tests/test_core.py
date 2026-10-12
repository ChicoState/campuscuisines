from datetime import timedelta
from pathlib import Path
from typing import cast

import pytest
from django.contrib.staticfiles import finders
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from reviews.models import Review


@pytest.mark.django_db
def test_homepage_shows_an_empty_review_feed(client) -> None:
    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert "No reviews yet" in response.content.decode()


@pytest.mark.django_db
def test_homepage_renders_five_rating_stars(client) -> None:
    response = client.get(reverse("home"))

    content = response.content.decode()
    assert content.count('class="rating-picker__star" data-rating-star=') == 5


@pytest.mark.django_db
def test_valid_review_submission_creates_a_review_and_redirects(client) -> None:
    response = client.post(
        reverse("home"),
        {
            "dish_name": "Mushroom ramen",
            "reviewer_name": "Avery",
            "rating": 4,
            "text": "Warm, savory, and excellent.",
        },
    )

    assert response.status_code == 302
    assert (
        Review.objects.filter(dish_name="Mushroom ramen").count()  # type: ignore[reportAttributeAccessIssue]
        == 1
    )


@pytest.mark.django_db
def test_review_submission_renders_only_the_selected_star_count(client) -> None:
    response = client.post(
        reverse("home"),
        {
            "dish_name": "Mushroom ramen",
            "reviewer_name": "Avery",
            "rating": 4,
            "text": "Warm, savory, and excellent.",
        },
        follow=True,
    )

    assert response.status_code == 200
    review_rating = (
        response.content.decode()
        .split('class="review__rating"', 1)[1]
        .split("</p>", 1)[0]
    )
    assert "4 out of 5 stars" in review_rating
    assert "Good" not in review_rating


@pytest.mark.django_db
def test_review_submission_requires_a_csrf_token() -> None:
    csrf_client = Client(enforce_csrf_checks=True)

    response = csrf_client.post(
        reverse("home"),
        {
            "dish_name": "Mushroom ramen",
            "reviewer_name": "Avery",
            "rating": 3,
            "text": "Warm, savory, and excellent.",
        },
    )

    assert response.status_code == 403  # type: ignore[reportAttributeAccessIssue]
    assert Review.objects.count() == 0  # type: ignore[reportAttributeAccessIssue]


@pytest.mark.django_db
def test_invalid_review_submission_keeps_values_and_shows_errors(client) -> None:
    response = client.post(
        reverse("home"),
        {"dish_name": "Mushroom ramen", "reviewer_name": "Avery", "rating": 0},
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert "Mushroom ramen" in content
    assert "Ensure this value is greater than or equal to 1" in content
    assert "This field is required" in content
    assert Review.objects.count() == 0  # type: ignore[reportAttributeAccessIssue]


@pytest.mark.django_db
def test_homepage_lists_newest_review_first_and_escapes_review_text(client) -> None:
    older = Review.objects.create(  # type: ignore[reportAttributeAccessIssue]
        dish_name="Older dish",
        reviewer_name="Avery",
        rating=3,
        text="Perfectly fine.",
    )
    newer = Review.objects.create(  # type: ignore[reportAttributeAccessIssue]
        dish_name="Newer dish",
        reviewer_name="Jordan",
        rating=5,
        text="<script>alert('not executable')</script>",
    )
    Review.objects.filter(pk=older.pk).update(  # type: ignore[reportAttributeAccessIssue]
        created_at=timezone.now() - timedelta(days=1)
    )

    response = client.get(reverse("home"))

    content = response.content.decode()
    assert content.index("Newer dish") < content.index("Older dish")
    assert "&lt;script&gt;alert(&#x27;not executable&#x27;)&lt;/script&gt;" in content
    review_rating = content.split('class="review__rating"', 1)[1].split("</p>", 1)[0]
    assert "5 out of 5 stars" in review_rating
    assert "Amazing" not in review_rating
    assert newer.created_at.strftime("%Y") in content


@pytest.mark.django_db
def test_homepage_returns_a_welcome_page(client) -> None:
    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert "Campus Cuisines" in response.content.decode()


def test_homepage_stylesheet_is_discoverable() -> None:
    assert finders.find("core/site.css")


def test_rating_picker_uses_visible_star_glyphs_with_a_contrasting_color() -> None:
    stylesheet_path = cast(str | None, finders.find("core/site.css"))

    assert stylesheet_path is not None
    stylesheet = Path(stylesheet_path).read_text()
    assert "color: var(--color-muted)" in stylesheet
    assert "clip-path" not in stylesheet
