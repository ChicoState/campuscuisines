from datetime import datetime
from typing import cast

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class TagCategory(models.Model):
    objects: models.Manager

    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "reviews_tagcategory"
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
        db_table = "reviews_tag"
        constraints = [
            models.UniqueConstraint(
                fields=["category", "name"], name="unique_tag_name_per_category"
            )
        ]
        ordering = ["category__name", "name"]

    def __str__(self) -> str:
        return f"{self.category}: {cast(str, self.name)}"


class FoodItem(models.Model):
    """A reusable dish that can be selected for one or more menu slots."""

    objects: models.Manager

    name = models.CharField(max_length=100)
    description = models.TextField(max_length=500, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="submitted_food_items",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="food_items")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self) -> str:
        return cast(str, self.name)


class MenuItemQuerySet(models.QuerySet):
    def available_at(self, moment: datetime | None = None):
        moment = moment or timezone.now()
        local_moment = (
            timezone.localtime(moment)
            if timezone.is_aware(moment)
            else timezone.make_aware(moment, timezone.get_current_timezone())
        )
        return self.filter(
            is_active=True,
            weekday=local_moment.weekday(),
            available_from__lte=local_moment.time(),
            available_until__gt=local_moment.time(),
        ).select_related("food_item")


class MenuItem(models.Model):
    """A scheduled publication of a FoodItem on the public menu."""

    WEEKDAYS = (
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    )

    objects = MenuItemQuerySet.as_manager()  # type: ignore[reportCallIssue]

    # Compatibility fields preserve existing placeholder records/tests. New
    # menu records should provide food_item and a complete recurring schedule.
    food_item = models.ForeignKey(
        FoodItem,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="menu_items",
    )
    name = models.CharField(max_length=100, blank=True)
    description = models.TextField(max_length=500, blank=True)
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAYS, blank=True, null=True)
    available_from = models.TimeField(blank=True, null=True)
    available_until = models.TimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)  # type: ignore[reportArgumentType]
    tags = models.ManyToManyField(Tag, blank=True, related_name="menu_items")

    class Meta:
        ordering = ["weekday", "available_from", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(available_from__lt=models.F("available_until")),
                name="menu_item_start_before_end",
            )
        ]

    @property
    def display_name(self) -> str:
        return cast(
            str,
            self.food_item.name
            if self.food_item_id  # type: ignore[reportAttributeAccessIssue]
            else self.name,
        )

    @property
    def display_description(self) -> str:
        return cast(
            str,
            self.food_item.description
            if self.food_item_id  # type: ignore[reportAttributeAccessIssue]
            else self.description,
        )

    def clean(self) -> None:
        super().clean()
        if self.food_item_id is None and not self.name:  # type: ignore[reportAttributeAccessIssue]
            raise ValidationError({"food_item": "Select a food item."})
        schedule_fields = (self.weekday, self.available_from, self.available_until)
        if any(value is None for value in schedule_fields) and any(
            value is not None for value in schedule_fields
        ):
            raise ValidationError("Weekday and both availability times are required.")
        if (
            self.available_from is not None
            and self.available_until is not None
            and self.available_from >= self.available_until
        ):
            raise ValidationError(
                {"available_until": "End time must be after start time."}
            )

    def __str__(self) -> str:
        return self.display_name
