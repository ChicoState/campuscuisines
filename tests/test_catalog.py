import pytest

from catalog.filters import filter_tagged_queryset
from catalog.models import MenuItem, Tag, TagCategory

pytestmark = pytest.mark.django_db


def create_menu_item(name: str, tags: list[Tag]) -> MenuItem:
    item = MenuItem.objects.create(name=name)
    item.tags.set(tags)
    return item


def test_menu_items_can_use_shared_tags() -> None:
    category = TagCategory.objects.create(name="Dietary")
    vegetarian = Tag.objects.create(category=category, name="Vegetarian")

    item = create_menu_item("Veggie bowl", [vegetarian])

    assert list(item.tags.all()) == [vegetarian]  # type: ignore[reportAttributeAccessIssue]


def test_shared_tag_filter_supports_menu_item_queries() -> None:
    dietary = TagCategory.objects.create(name="Dietary")
    vegetarian = Tag.objects.create(category=dietary, name="Vegetarian")
    vegan = Tag.objects.create(category=dietary, name="Vegan")
    flavor = TagCategory.objects.create(name="Flavor")
    spicy = Tag.objects.create(category=flavor, name="Spicy")

    matching_item = create_menu_item("Spicy veggie bowl", [vegetarian, spicy])
    create_menu_item("Vegan noodles", [vegan])

    filtered = filter_tagged_queryset(
        MenuItem.objects.all(), {vegetarian.pk, vegan.pk, spicy.pk}
    )

    assert list(filtered) == [matching_item]
