import pytest
from django.utils import timezone

from reviews.filters import filter_reviews_by_tags
from reviews.models import Review, Tag, TagCategory

pytestmark = pytest.mark.django_db


def make_review(dish_name: str, tags: list[Tag]) -> Review:
    review = Review.objects.create(
        dish_name=dish_name,
        reviewer_name="Avery",
        rating=4,
        text=f"Review of {dish_name}",
        created_at=timezone.now(),
    )
    review.tags.set(tags)
    return review


def test_review_filter_matches_any_selected_tag_within_one_category() -> None:
    dietary = TagCategory.objects.create(name="Dietary")
    vegetarian = Tag.objects.create(category=dietary, name="Vegetarian")
    vegan = Tag.objects.create(category=dietary, name="Vegan")
    spicy = TagCategory.objects.create(name="Flavor")
    hot = Tag.objects.create(category=spicy, name="Spicy")

    vegetarian_review = make_review("Veggie bowl", [vegetarian])
    vegan_review = make_review("Tofu noodles", [vegan])
    make_review("Chicken curry", [hot])

    filtered = filter_reviews_by_tags(
        Review.objects.all(), [str(vegetarian.pk), str(vegan.pk)]
    )

    assert list(filtered) == [vegan_review, vegetarian_review]


def test_review_filter_requires_a_match_in_each_selected_category() -> None:
    dietary = TagCategory.objects.create(name="Dietary")
    vegetarian = Tag.objects.create(category=dietary, name="Vegetarian")
    flavor = TagCategory.objects.create(name="Flavor")
    spicy = Tag.objects.create(category=flavor, name="Spicy")

    matching_review = make_review("Spicy veggie bowl", [vegetarian, spicy])
    make_review("Veggie bowl", [vegetarian])
    make_review("Spicy chicken", [spicy])

    filtered = filter_reviews_by_tags(
        Review.objects.all(), [str(vegetarian.pk), str(spicy.pk)]
    )

    assert list(filtered) == [matching_review]


def test_review_filter_ignores_unknown_or_malformed_tag_ids() -> None:
    dietary = TagCategory.objects.create(name="Dietary")
    vegetarian = Tag.objects.create(category=dietary, name="Vegetarian")
    matching_review = make_review("Veggie bowl", [vegetarian])
    other_review = make_review("Chicken bowl", [])

    filtered = filter_reviews_by_tags(
        Review.objects.all(), [str(vegetarian.pk), "not-an-id", "999999"]
    )

    assert list(filtered) == [matching_review]
    assert other_review not in filtered


def test_review_filter_without_selections_keeps_all_reviews() -> None:
    dietary = TagCategory.objects.create(name="Dietary")
    vegetarian = Tag.objects.create(category=dietary, name="Vegetarian")
    oldest_review = make_review("Chicken bowl", [])
    newest_review = make_review("Veggie bowl", [vegetarian])

    filtered = filter_reviews_by_tags(Review.objects.all(), [])

    assert list(filtered) == [newest_review, oldest_review]
