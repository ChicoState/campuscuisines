from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
        ("reviews", "0003_tag_tagcategory_review_tags_tag_category_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="review",
                    name="tags",
                    field=models.ManyToManyField(
                        blank=True, related_name="reviews", to="catalog.tag"
                    ),
                ),
                migrations.DeleteModel(name="Tag"),
                migrations.DeleteModel(name="TagCategory"),
            ],
        )
    ]
