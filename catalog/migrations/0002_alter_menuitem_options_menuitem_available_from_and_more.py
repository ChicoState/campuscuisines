import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="menuitem",
            options={"ordering": ["weekday", "available_from", "id"]},
        ),
        migrations.AddField(
            model_name="menuitem",
            name="available_from",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="menuitem",
            name="available_until",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="menuitem",
            name="is_active",
            field=models.BooleanField(default=True),  # pyright: ignore[reportArgumentType]
        ),
        migrations.AddField(
            model_name="menuitem",
            name="weekday",
            field=models.PositiveSmallIntegerField(
                blank=True,
                choices=[
                    (0, "Monday"),
                    (1, "Tuesday"),
                    (2, "Wednesday"),
                    (3, "Thursday"),
                    (4, "Friday"),
                    (5, "Saturday"),
                    (6, "Sunday"),
                ],
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="menuitem",
            name="name",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.CreateModel(
            name="FoodItem",
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
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "submitted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="submitted_food_items",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "tags",
                    models.ManyToManyField(
                        blank=True, related_name="food_items", to="catalog.tag"
                    ),
                ),
            ],
            options={
                "ordering": ["name", "id"],
            },
        ),
        migrations.AddField(
            model_name="menuitem",
            name="food_item",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="menu_items",
                to="catalog.fooditem",
            ),
        ),
        migrations.AddConstraint(
            model_name="menuitem",
            constraint=models.CheckConstraint(
                condition=models.Q(("available_from__lt", models.F("available_until"))),
                name="menu_item_start_before_end",
            ),
        ),
    ]
