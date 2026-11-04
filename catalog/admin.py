from django.contrib import admin

from .models import MenuItem, Tag, TagCategory


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
    list_display = ("name",)
    search_fields = ("name", "description")
    filter_horizontal = ("tags",)
