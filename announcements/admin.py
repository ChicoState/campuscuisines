from django.contrib import admin

from announcements.models import Announcement, AnnouncementDismissal


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "author_name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title", "body", "author_name")


@admin.register(AnnouncementDismissal)
class AnnouncementDismissalAdmin(admin.ModelAdmin):
    list_display = ("announcement", "user", "session_key", "dismissed_at")
    list_filter = ("dismissed_at",)
