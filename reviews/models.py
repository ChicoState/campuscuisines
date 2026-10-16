from typing import cast

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import ImageAsset


class TagCategory(models.Model):
    objects: models.Manager

    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return cast(str, self.name)


class Tag(models.Model):
    objects: models.Manager

    category = models.ForeignKey(
        TagCategory, on_delete=models.CASCADE, related_name="tags"
    )
    name = models.CharField(max_length=50)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["category", "name"], name="unique_tag_name_per_category"
            )
        ]
        ordering = ["category__name", "name"]

    def __str__(self) -> str:
        return f"{self.category}: {cast(str, self.name)}"


class Review(models.Model):
    dish_name = models.CharField(max_length=100)
    reviewer_name = models.CharField(max_length=50)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    text = models.TextField(max_length=500)
    tags = models.ManyToManyField(Tag, blank=True, related_name="reviews")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name="review_rating_between_one_and_five_stars",
            )
        ]
        ordering = ["-created_at", "-id"]

    @property
    def rating_label(self) -> str:
        descriptions = {1: "Bad", 2: "Mediocre", 3: "Fine", 4: "Good", 5: "Amazing"}
        rating = cast(int, self.rating)
        return f"{rating} out of 5 stars — {descriptions[rating]}"

    def __str__(self) -> str:
        return f"{self.dish_name} — {self.rating_label}"


class ReviewImage(models.Model):
    """An explicit image association owned by the review feature."""

    objects: models.Manager

    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name="image_links"
    )
    image = models.OneToOneField(
        ImageAsset, on_delete=models.PROTECT, related_name="review_image"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["review"], name="one_image_per_review")
        ]
