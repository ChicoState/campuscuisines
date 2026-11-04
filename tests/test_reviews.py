import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from reviews.forms import RATING_CHOICES, ReviewForm
from reviews.models import Review, Tag, TagCategory

pytestmark = pytest.mark.django_db


def test_review_form_offers_five_whole_star_choices_with_descriptions() -> None:
    assert RATING_CHOICES == [
        (1, "1 out of 5 stars — Bad"),
        (2, "2 out of 5 stars — Mediocre"),
        (3, "3 out of 5 stars — Fine"),
        (4, "4 out of 5 stars — Good"),
        (5, "5 out of 5 stars — Amazing"),
    ]


def test_review_form_saves_selected_tags() -> None:
    allergen_category = TagCategory.objects.create(  # type: ignore[reportAttributeAccessIssue]
        name="Allergens"
    )
    contains_peanuts = Tag.objects.create(  # type: ignore[reportAttributeAccessIssue]
        category=allergen_category, name="Contains peanuts"
    )
    meat_type_category = TagCategory.objects.create(  # type: ignore[reportAttributeAccessIssue]
        name="Meat type"
    )
    vegetarian = Tag.objects.create(  # type: ignore[reportAttributeAccessIssue]
        category=meat_type_category, name="Vegetarian"
    )

    form = ReviewForm(
        data={
            "dish_name": "Vegetarian pad thai",
            "reviewer_name": "Avery",
            "rating": 5,
            "text": "Great texture and flavor.",
            "tags": [str(contains_peanuts.pk), str(vegetarian.pk)],
        }
    )

    assert form.is_valid()
    review = form.save()
    assert list(review.tags.all()) == [contains_peanuts, vegetarian]


def test_review_form_rejects_unknown_tags() -> None:
    form = ReviewForm(
        data={
            "dish_name": "Vegetarian pad thai",
            "reviewer_name": "Avery",
            "rating": 5,
            "text": "Great texture and flavor.",
            "tags": ["999"],
        }
    )

    assert not form.is_valid()
    assert form.errors is not None
    assert "tags" in form.errors


def test_tag_names_are_unique_within_their_category() -> None:
    category = TagCategory.objects.create(  # type: ignore[reportAttributeAccessIssue]
        name="Allergens"
    )
    Tag.objects.create(  # type: ignore[reportAttributeAccessIssue]
        category=category, name="Contains peanuts"
    )

    with pytest.raises(IntegrityError):
        Tag.objects.create(  # type: ignore[reportAttributeAccessIssue]
            category=category, name="Contains peanuts"
        )


@pytest.mark.parametrize("rating", range(1, 6))
def test_review_form_accepts_each_whole_star_rating(rating: int) -> None:
    form = ReviewForm(
        data={
            "dish_name": "D" * 100,
            "reviewer_name": "R" * 50,
            "rating": rating,
            "text": "T" * 500,
        }
    )

    assert form.is_valid()


@pytest.mark.parametrize("rating", [0, 6])
def test_review_model_rejects_ratings_outside_five_star_range(rating: int) -> None:
    review = Review(
        dish_name="Tacos",
        reviewer_name="Avery",
        rating=rating,
        text="Crisp and flavorful.",
    )

    with pytest.raises(ValidationError):
        review.full_clean()


def test_review_rating_label_formats_whole_stars() -> None:
    review = Review(
        dish_name="Tacos",
        reviewer_name="Avery",
        rating=3,
        text="Crisp and flavorful.",
    )

    assert review.rating_label == "3 out of 5 stars — Fine"


@pytest.mark.django_db
def test_review_database_constraint_rejects_invalid_rating() -> None:
    with pytest.raises(IntegrityError):
        Review.objects.create(  # type: ignore[reportAttributeAccessIssue]
            dish_name="Tacos",
            reviewer_name="Avery",
            rating=0,
            text="Crisp and flavorful.",
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("dish_name", "D" * 101),
        ("reviewer_name", "R" * 51),
        ("text", "T" * 501),
    ],
)
def test_review_form_rejects_oversized_content(field: str, value: str) -> None:
    data = {
        "dish_name": "Tacos",
        "reviewer_name": "Avery",
        "rating": 5,
        "text": "Crisp and flavorful.",
    }
    data[field] = value

    form = ReviewForm(data=data)

    assert not form.is_valid()
    assert form.errors is not None
    assert field in form.errors
