from typing import cast

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from catalog.models import Tag, TagCategory
from core.models import ImageAsset

__all__ = ["Report", "Review", "ReviewImage", "Tag", "TagCategory"]


class Review(models.Model):
    objects: models.Manager

    menu_item = models.ForeignKey(
        "catalog.MenuItem",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="reviews",
    )
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


class Report(models.Model):
    objects: models.Manager

    REPORT_TYPE_REVIEW = "review"
    REPORT_TYPE_IMAGE = "image"
    REPORT_TYPE_ACCOUNT = "account"
    REPORT_TYPE_CHOICES = [
        (REPORT_TYPE_REVIEW, "Review"),
        (REPORT_TYPE_IMAGE, "Image"),
        (REPORT_TYPE_ACCOUNT, "Account"),
    ]
    REASON_SPAM = "spam"
    REASON_INAPPROPRIATE = "inappropriate"
    REASON_OFFENSIVE = "offensive"
    REASON_OTHER = "other"
    REASON_CHOICES = [
        (REASON_SPAM, "Spam/scam"),
        (REASON_INAPPROPRIATE, "Inappropriate"),
        (REASON_OFFENSIVE, "Offensive"),
        (REASON_OTHER, "Other"),
    ]

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_submitted",
    )
    report_type = models.CharField(max_length=10, choices=REPORT_TYPE_CHOICES)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    custom_reason = models.CharField(max_length=500, blank=True)
    review = models.ForeignKey(
        Review,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="reports",
    )
    image = models.ForeignKey(
        ImageAsset,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="reports",
    )
    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="account_reports",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["reporter", "review"],
                condition=models.Q(report_type="review"),
                name="one_review_report_per_user",
            ),
            models.UniqueConstraint(
                fields=["reporter", "image"],
                condition=models.Q(report_type="image"),
                name="one_image_report_per_user",
            ),
            models.UniqueConstraint(
                fields=["reporter", "account"],
                condition=models.Q(report_type="account"),
                name="one_account_report_per_user",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        report_type="review",
                        review__isnull=False,
                        image__isnull=True,
                        account__isnull=True,
                    )
                    | models.Q(  # type: ignore[reportOperatorIssue]
                        report_type="image",
                        review__isnull=True,
                        image__isnull=False,
                        account__isnull=True,
                    )
                    | models.Q(
                        report_type="account",
                        review__isnull=True,
                        image__isnull=True,
                        account__isnull=False,
                    )
                ),
                name="report_type_has_matching_target",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        custom_reason = str(self.custom_reason or "")
        if self.reason == self.REASON_OTHER and not custom_reason.strip():
            raise ValidationError({"custom_reason": "Enter a custom reason."})
        if self.reason != self.REASON_OTHER and custom_reason.strip():
            raise ValidationError(
                {"custom_reason": "Custom text is only valid for Other."}
            )
