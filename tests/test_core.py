from datetime import timedelta
from pathlib import Path
from typing import cast

import pytest
from django.contrib.staticfiles import finders
from django.test import Client, SimpleTestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from reviews.models import Review, Tag, TagCategory


def eligible_user() -> User:
    return User.objects.create_user(
        username="student", email="student@csuchico.edu", password="unused"
    )


@pytest.mark.django_db
def test_reviews_page_shows_an_empty_review_feed(client) -> None:
    response = client.get(reverse("reviews"))

    assert response.status_code == 200
    assert "No reviews yet" in response.content.decode()


@pytest.mark.django_db
def test_reviews_page_renders_five_rating_stars(client) -> None:
    response = client.get(reverse("reviews"))
    content = response.content.decode()
    assert content.count('class="rating-picker__star" data-rating-star=') == 5


@pytest.mark.django_db
def test_signed_in_homepage_does_not_render_review_tools(client) -> None:
    client.force_login(eligible_user())
    response = client.get(reverse("home"))

    content = response.content.decode()
    assert "Review tools" not in content
    assert 'class="rating-picker__star"' not in content
    assert 'class="tag-dropdown"' not in content


@pytest.mark.django_db
def test_invalid_tag_submission_preserves_selected_tags_and_opens_dropdown(
    client,
) -> None:
    client.force_login(eligible_user())
    category = TagCategory.objects.create(  # type: ignore[reportAttributeAccessIssue]
        name="Dietary"
    )
    vegetarian = Tag.objects.create(  # type: ignore[reportAttributeAccessIssue]
        category=category, name="Vegetarian"
    )

    response = client.post(
        reverse("home"),
        {
            "dish_name": "Mushroom ramen",
            "reviewer_name": "Avery",
            "rating": 0,
            "text": "Warm, savory, and excellent.",
            "tags": [str(vegetarian.pk)],
        },
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert '<details class="tag-dropdown" open>' in content
    assert f'id="id_tags_{vegetarian.pk}"' in content
    SimpleTestCase().assertContains(
        response,
        f'<input id="id_tags_{vegetarian.pk}" name="tags" type="checkbox" '
        f'value="{vegetarian.pk}" checked>',
        html=True,
    )
    assert 'data-tags-summary="1 tag selected"' in content


@pytest.mark.django_db
def test_valid_review_submission_creates_a_review_and_redirects(client) -> None:
    client.force_login(eligible_user())
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
def test_review_submission_saves_selected_tags(client) -> None:
    client.force_login(eligible_user())
    category = TagCategory.objects.create(  # type: ignore[reportAttributeAccessIssue]
        name="Meat type"
    )
    vegetarian = Tag.objects.create(  # type: ignore[reportAttributeAccessIssue]
        category=category, name="Vegetarian"
    )

    response = client.post(
        reverse("home"),
        {
            "dish_name": "Mushroom ramen",
            "reviewer_name": "Avery",
            "rating": 4,
            "text": "Warm, savory, and excellent.",
            "tags": [str(vegetarian.pk)],
        },
    )

    review = Review.objects.get()  # type: ignore[reportAttributeAccessIssue]
    assert response.status_code == 302
    assert list(review.tags.all()) == [vegetarian]


@pytest.mark.django_db
def test_review_submission_renders_only_the_selected_star_count(client) -> None:
    client.force_login(eligible_user())
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
    client.force_login(eligible_user())
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
def test_anonymous_homepage_is_public_but_review_submission_is_authenticated(
    client,
) -> None:
    get_response = client.get(reverse("home"))
    post_response = client.post(
        reverse("home"),
        {
            "dish_name": "Mushroom ramen",
            "reviewer_name": "Avery",
            "rating": 4,
            "text": "Warm, savory, and excellent.",
        },
    )

    assert get_response.status_code == 200
    assert "Continue to sign in" in get_response.content.decode()
    assert post_response.status_code == 302
    assert post_response.url == "/accounts/login/?next=/"
    assert not Review.objects.exists()  # type: ignore[reportAttributeAccessIssue]


@pytest.mark.django_db
def test_ineligible_signed_in_user_cannot_submit_a_review(client) -> None:
    outsider = User.objects.create_user(
        username="outsider", email="outsider@gmail.com", password="unused"
    )
    client.force_login(outsider)

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
    assert response.url == "/accounts/login/?next=/"
    assert not Review.objects.exists()  # type: ignore[reportAttributeAccessIssue]


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

    response = client.get(reverse("reviews"))

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


@pytest.mark.django_db
def test_homepage_renders_one_admin_announcement_dialog(client) -> None:
    response = client.get(reverse("home"))

    content = response.content.decode()
    assert response.status_code == 200
    assert "data-announcement-open" in content
    assert "<dialog" in content
    assert 'class="announcement-dialog"' in content
    assert content.count("data-announcement-item") == 1
    assert "Test announcement" in content
    assert "Posted by Admin" in content
    assert "core/announcements.js" in content


def test_homepage_stylesheet_is_discoverable() -> None:
    assert finders.find("core/site.css")


def test_rating_picker_uses_visible_star_glyphs_with_a_contrasting_color() -> None:
    stylesheet_path = cast(str | None, finders.find("core/site.css"))

    assert stylesheet_path is not None
    stylesheet = Path(stylesheet_path).read_text()
    assert "color: var(--color-muted)" in stylesheet
    assert "clip-path" not in stylesheet


def test_review_section_headings_stack_their_label_title_and_action() -> None:
    stylesheet_path = cast(str | None, finders.find("core/site.css"))

    assert stylesheet_path is not None
    stylesheet = Path(stylesheet_path).read_text()
    heading_rules = stylesheet.split(".reviews-section__heading {", 1)[1].split("}", 1)[
        0
    ]

    assert "display: grid" in heading_rules
    assert "justify-items: start" in heading_rules
    assert "gap: var(--space-2)" in heading_rules

    assert ".reviews-section__action" in stylesheet
    action_rules = stylesheet.split(".reviews-section__action {", 1)[1].split("}", 1)[0]
    assert "position: fixed" in action_rules
    assert "bottom: var(--space-4)" in action_rules
    assert "right: var(--space-4)" in action_rules


def test_home_welcome_spacing_matches_other_page_sections() -> None:
    stylesheet_path = cast(str | None, finders.find("core/site.css"))

    assert stylesheet_path is not None
    stylesheet = Path(stylesheet_path).read_text()
    welcome_rules = stylesheet.split(".welcome {", 1)[1].split("}", 1)[0]

    assert "padding-block: var(--space-12)" in welcome_rules
    assert "clamp(" not in welcome_rules
