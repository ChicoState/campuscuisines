import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reviews", "0003_tag_tagcategory_review_tags_tag_category_and_more")
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="TagCategory",
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
                        ("name", models.CharField(max_length=50, unique=True)),
                    ],
                    options={
                        "ordering": ["name"],
                        "db_table": "reviews_tagcategory",
                    },
                ),
                migrations.CreateModel(
                    name="Tag",
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
                        ("name", models.CharField(max_length=50)),
                        (
                            "category",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="tags",
                                to="catalog.tagcategory",
                            ),
                        ),
                    ],
                    options={
                        "ordering": ["category__name", "name"],
                        "db_table": "reviews_tag",
                        "constraints": [
                            models.UniqueConstraint(
                                fields=("category", "name"),
                                name="unique_tag_name_per_category",
                            )
                        ],
                    },
                ),
            ],
        ),
        migrations.CreateModel(
            name="MenuItem",
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
                (
                    "tags",
                    models.ManyToManyField(
                        blank=True, related_name="menu_items", to="catalog.tag"
                    ),
                ),
            ],
            options={"ordering": ["name", "id"]},
        ),
    ]
