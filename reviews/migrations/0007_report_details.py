import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

LEGACY_REASON = "Legacy report imported before reasons were collected."


def backfill_report_details(apps, schema_editor):
    Report = apps.get_model("reviews", "Report")
    Report.objects.update(
        report_type="review",
        reason="other",
        custom_reason=LEGACY_REASON,
    )


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0003_imageasset_deleted_at"),
        ("reviews", "0006_report"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="account",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="account_reports",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="report",
            name="custom_reason",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="report",
            name="image",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reports",
                to="core.imageasset",
            ),
        ),
        migrations.AddField(
            model_name="report",
            name="reason",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="report",
            name="report_type",
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AlterField(
            model_name="report",
            name="reporter",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reports_submitted",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="report",
            name="review",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reports",
                to="reviews.review",
            ),
        ),
        migrations.RunPython(backfill_report_details, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="report",
            name="reason",
            field=models.CharField(
                choices=[
                    ("spam", "Spam/scam"),
                    ("inappropriate", "Inappropriate"),
                    ("offensive", "Offensive"),
                    ("other", "Other"),
                ],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="report",
            name="report_type",
            field=models.CharField(
                choices=[
                    ("review", "Review"),
                    ("image", "Image"),
                    ("account", "Account"),
                ],
                max_length=10,
            ),
        ),
        migrations.RemoveConstraint(
            model_name="report",
            name="one_report_per_user_review",
        ),
        migrations.AddConstraint(
            model_name="report",
            constraint=models.UniqueConstraint(
                condition=models.Q(report_type="review"),
                fields=("reporter", "review"),
                name="one_review_report_per_user",
            ),
        ),
        migrations.AddConstraint(
            model_name="report",
            constraint=models.UniqueConstraint(
                condition=models.Q(report_type="image"),
                fields=("reporter", "image"),
                name="one_image_report_per_user",
            ),
        ),
        migrations.AddConstraint(
            model_name="report",
            constraint=models.UniqueConstraint(
                condition=models.Q(report_type="account"),
                fields=("reporter", "account"),
                name="one_account_report_per_user",
            ),
        ),
        migrations.AddConstraint(
            model_name="report",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(
                        report_type="review",
                        review__isnull=False,
                        image__isnull=True,
                        account__isnull=True,
                    )
                    | models.Q(  # type: ignore[reportOperatorIssue]
                        report_type="image",
                        review__isnull=True,
                        image__isnull=False,
                        account__isnull=True,
                    )
                    | models.Q(
                        report_type="account",
                        review__isnull=True,
                        image__isnull=True,
                        account__isnull=False,
                    )
                ),
                name="report_type_has_matching_target",
            ),
        ),
    ]
