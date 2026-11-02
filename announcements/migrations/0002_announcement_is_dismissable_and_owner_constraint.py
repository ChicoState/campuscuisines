from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("announcements", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="announcement",
            name="is_dismissable",
            field=models.BooleanField(default=True),
        ),
        migrations.RemoveConstraint(
            model_name="announcementdismissal",
            name="announcement_dismissal_has_owner",
        ),
        migrations.AddConstraint(
            model_name="announcementdismissal",
            constraint=models.CheckConstraint(
                condition=(
                    Q(user__isnull=False, session_key__isnull=True)
                    | Q(user__isnull=True, session_key__isnull=False)
                ),
                name="announcement_dismissal_has_owner",
            ),
        ),
    ]
