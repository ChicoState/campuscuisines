from django.db import migrations


def create_non_dismissable_announcement(apps, schema_editor):
    announcement = apps.get_model("announcements", "Announcement")
    announcement.objects.get_or_create(
        title="Read-only announcement",
        defaults={
            "author_name": "Admin",
            "body": "This announcement must remain visible.",
            "is_dismissable": False,
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ("announcements", "0002_announcement_is_dismissable_and_owner_constraint"),
    ]

    operations = [
        migrations.RunPython(
            create_non_dismissable_announcement,
            migrations.RunPython.noop,
        ),
    ]
