from django.contrib import admin

from .models import Report, Review, ReviewImage


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("review", "reporter", "created_at")
    list_select_related = ("review", "reporter")
    search_fields = ("review__dish_name", "reporter__email")
    ordering = ("-created_at", "-id")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "dish_name",
        "menu_item",
        "reviewer_name",
        "rating_label",
        "created_at",
    )
    list_filter = ("menu_item", "created_at")
    search_fields = ("dish_name", "reviewer_name", "text")
    list_select_related = ("menu_item",)
    ordering = ("-created_at", "-id")


@admin.register(ReviewImage)
class ReviewImageAdmin(admin.ModelAdmin):
    list_display = ("review", "image")
    list_select_related = ("review", "image")
