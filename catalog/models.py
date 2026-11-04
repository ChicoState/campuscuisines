from typing import cast

from django.db import models


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


class MenuItem(models.Model):
    objects: models.Manager

    name = models.CharField(max_length=100)
    description = models.TextField(max_length=500, blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="menu_items")

    class Meta:
        ordering = ["name", "id"]

    def __str__(self) -> str:
        return cast(str, self.name)
