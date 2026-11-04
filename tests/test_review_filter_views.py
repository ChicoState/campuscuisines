import pytest

from reviews.models import Review, Tag, TagCategory

pytestmark = pytest.mark.django_db


def create_review(dish_name: str, tags: list[Tag]) -> Review:
    review = Review.objects.create(
        dish_name=dish_name,
        reviewer_name="Avery",
        rating=4,
        text=f"Review of {dish_name}",
    )
    review.tags.set(tags)
    return review


def test_home_filters_reviews_by_selected_tag(client) -> None:
    category = TagCategory.objects.create(name="Dietary")
    vegetarian = Tag.objects.create(category=category, name="Vegetarian")
    create_review("Veggie bowl", [vegetarian])
    create_review("Chicken bowl", [])

    response = client.get("/", {"review_tag": str(vegetarian.pk)})

    assert response.status_code == 200
    content = response.content.decode()
    assert "Veggie bowl" in content
    assert "Chicken bowl" not in content
    assert 'class="tag-dropdown review-filter__dropdown"' in content
    assert "Filter reviews by tag" in content
    selected_tag_html = content.split(f'id="review-tag-{vegetarian.pk}"', 1)[1]
    assert f'value="{vegetarian.pk}"' in selected_tag_html[:220]
    assert "checked" in selected_tag_html[:220]


def test_home_ignores_unknown_review_tag_filter(client) -> None:
    create_review("Chicken bowl", [])

    response = client.get("/", {"review_tag": "not-a-tag"})

    assert response.status_code == 200
    assert "Chicken bowl" in response.content.decode()
