import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q


def create_test_announcement(apps, schema_editor):
    announcement = apps.get_model("announcements", "Announcement")
    announcement.objects.get_or_create(
        title="Test announcement",
        defaults={
            "author_name": "Admin",
            "body": "This is a test announcement.",
        },
    )


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Announcement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("author_name", models.CharField(default="Admin", max_length=100)),
                ("body", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"ordering": ["-created_at", "-pk"]},
        ),
        migrations.CreateModel(
            name="AnnouncementDismissal",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("session_key", models.CharField(blank=True, max_length=40, null=True)),
                ("dismissed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "announcement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dismissals",
                        to="announcements.announcement",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="announcement_dismissals",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="announcementdismissal",
            constraint=models.CheckConstraint(
                condition=Q(user__isnull=False) | Q(session_key__isnull=False),
                name="announcement_dismissal_has_owner",
            ),
        ),
        migrations.AddConstraint(
            model_name="announcementdismissal",
            constraint=models.UniqueConstraint(
                condition=Q(user__isnull=False),
                fields=("announcement", "user"),
                name="unique_announcement_dismissal_user",
            ),
        ),
        migrations.AddConstraint(
            model_name="announcementdismissal",
            constraint=models.UniqueConstraint(
                condition=Q(session_key__isnull=False),
                fields=("announcement", "session_key"),
                name="unique_announcement_dismissal_session",
            ),
        ),
        migrations.RunPython(create_test_announcement, migrations.RunPython.noop),
    ]
