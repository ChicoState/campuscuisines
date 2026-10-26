from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q


class Announcement(models.Model):
    objects: models.Manager

    title = models.CharField(max_length=200)
    author_name = models.CharField(max_length=100, default="Admin")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  # type: ignore[reportArgumentType]

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self) -> str:
        return self.title  # type: ignore[return-value]


class AnnouncementDismissal(models.Model):
    objects: models.Manager

    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name="dismissals",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="announcement_dismissals",
    )
    session_key = models.CharField(max_length=40, blank=True, null=True)
    dismissed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(user__isnull=False) | Q(session_key__isnull=False),
                name="announcement_dismissal_has_owner",
            ),
            models.UniqueConstraint(
                fields=["announcement", "user"],
                condition=Q(user__isnull=False),
                name="unique_announcement_dismissal_user",
            ),
            models.UniqueConstraint(
                fields=["announcement", "session_key"],
                condition=Q(session_key__isnull=False),
                name="unique_announcement_dismissal_session",
            ),
        ]
