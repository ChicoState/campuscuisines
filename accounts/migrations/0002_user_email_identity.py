from django.db import migrations, models


def normalize_and_audit_emails(apps, schema_editor) -> None:
    User = apps.get_model("accounts", "User")
    seen: dict[str, int] = {}
    for user in User.objects.all().only("pk", "email").iterator():
        email = (user.email or "").strip().lower()
        if not email:
            raise RuntimeError(
                "Cannot make User.email required: every existing user must have an email."
            )
        if email in seen:
            raise RuntimeError(
                "Cannot make User.email unique: duplicate identities exist for "
                f"user IDs {seen[email]} and {user.pk}."
            )
        seen[email] = user.pk
        if user.email != email:
            User.objects.filter(pk=user.pk).update(email=email)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]

    operations = [
        migrations.RunPython(normalize_and_audit_emails, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(
                editable=False,
                max_length=254,
                unique=True,
                verbose_name="email address",
            ),
        ),
    ]
