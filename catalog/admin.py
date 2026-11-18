from django.contrib import admin

from .models import FoodItem, MenuItem, Tag, TagCategory


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ("name", "submitted_by", "created_at")
    search_fields = ("name", "description")
    filter_horizontal = ("tags",)
    list_select_related = ("submitted_by",)


@admin.register(TagCategory)
class TagCategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
    list_filter = ("category",)
    search_fields = ("name",)
    list_select_related = ("category",)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = (
        "food_item",
        "weekday",
        "available_from",
        "available_until",
        "is_active",
    )
    list_filter = ("weekday", "is_active")
    search_fields = ("food_item__name", "name")
    autocomplete_fields = ("food_item",)
    filter_horizontal = ("tags",)
