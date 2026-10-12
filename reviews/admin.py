from django.contrib import admin

from .models import Review, ReviewImage


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("dish_name", "reviewer_name", "rating_label", "created_at")
    list_filter = ("created_at",)
    search_fields = ("dish_name", "reviewer_name", "text")
    ordering = ("-created_at", "-id")


@admin.register(ReviewImage)
class ReviewImageAdmin(admin.ModelAdmin):
    list_display = ("review", "image")
    list_select_related = ("review", "image")
