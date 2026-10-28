import pytest
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from core.models import ImageAsset


@pytest.mark.django_db
def test_primary_navigation_has_five_tabs_and_no_images_tab(client) -> None:
    response = client.get(reverse("home"))

    assert response.status_code == 200
    navigation = response.content.decode().split(
        '<nav aria-label="Primary navigation">', 1
    )[1]
    labels = [
        "Home",
        "Reviews",
        "Map/Locations",
        "About Us",
        "Account",
    ]
    assert [navigation.index(label) for label in labels] == sorted(
        navigation.index(label) for label in labels
    )
    assert "Images" not in navigation
    assert navigation.count('aria-current="page"') == 1


@pytest.mark.django_db
def test_nested_image_upload_route_does_not_add_an_images_tab(client) -> None:
    with override_settings(DEBUG=True):
        response = client.get(reverse("image-upload"))

    assert response.status_code == 200
    navigation = response.content.decode().split(
        '<nav aria-label="Primary navigation">', 1
    )[1]
    assert "Images" not in navigation


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", ["reviews", "images", "map", "about", "account"])
def test_navigation_pages_render(client, url_name: str) -> None:
    response = client.get(reverse(url_name))

    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("url_name", "active_label"),
    [
        ("home", "Home"),
        ("reviews", "Reviews"),
        ("map", "Map/Locations"),
        ("about", "About Us"),
        ("account", "Account"),
    ],
)
def test_navigation_marks_only_the_current_tab(
    client, url_name: str, active_label: str
) -> None:
    response = client.get(reverse(url_name))
    content = response.content.decode()
    navigation = content.split('<nav aria-label="Primary navigation">', 1)[1].split(
        "</nav>", 1
    )[0]

    assert navigation.count('aria-current="page"') == 1
    assert f'aria-current="page">{active_label}</a>' in navigation


@pytest.mark.django_db
def test_home_does_not_contain_the_removed_visit_planning_section(client) -> None:
    response = client.get(reverse("home"))

    content = response.content.decode()
    assert "Plan your visit" not in content
    assert "Estom Jamston Hall" not in content


@pytest.mark.django_db
def test_reviews_page_owns_review_form_and_home_is_a_landing_page(client) -> None:
    home = client.get(reverse("home"))
    reviews = client.get(reverse("reviews"))

    assert 'action="' not in home.content.decode()
    assert 'name="dish_name"' not in home.content.decode()
    assert 'name="dish_name"' in reviews.content.decode()


@pytest.mark.django_db
def test_images_page_lists_only_published_images(client, monkeypatch) -> None:
    published = ImageAsset.objects.create(
        file="images/published.png",
        alt_text="Published meal",
        published_at=timezone.now(),
    )
    ImageAsset.objects.create(file="images/draft.png", alt_text="Draft meal")
    monkeypatch.setattr(
        "core.views.signed_image_url",
        lambda asset, _viewer: f"https://images.test/{asset.pk}",
    )

    response = client.get(reverse("images"))

    content = response.content.decode()
    assert response.status_code == 200
    assert "Published meal" in content
    assert f"https://images.test/{published.pk}" in content
    assert "Draft meal" not in content


@pytest.mark.django_db
def test_images_page_omits_deleted_images_and_shows_empty_state(client) -> None:
    deleted = ImageAsset.objects.create(
        file="images/deleted.png", alt_text="Deleted meal"
    )
    deleted.soft_delete()

    response = client.get(reverse("images"))

    content = response.content.decode()
    assert response.status_code == 200
    assert "No published images yet." in content
    assert "Deleted meal" not in content


@pytest.mark.django_db
def test_map_page_is_an_explicit_placeholder(client) -> None:
    response = client.get(reverse("map"))

    assert "The campus food map is coming soon." in response.content.decode()


@pytest.mark.django_db
def test_legacy_home_review_submission_redirects_to_reviews(client) -> None:
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
    assert response.url == reverse("reviews")
