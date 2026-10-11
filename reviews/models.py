from typing import cast

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    dish_name = models.CharField(max_length=100)
    reviewer_name = models.CharField(max_length=50)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    text = models.TextField(max_length=500)
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
