from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.models import User
from catalog.filters import filter_tagged_queryset
from catalog.models import FoodItem, MenuItem, Tag, TagCategory

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


def test_food_item_records_submitter_and_shared_tags() -> None:
    user = User.objects.create_user(
        username="food-contributor", email="food-contributor@csuchico.edu"
    )
    category = TagCategory.objects.create(name="Dietary")
    vegetarian = Tag.objects.create(category=category, name="Vegetarian")

    food_item = FoodItem.objects.create(
        name="Vegetable ramen",
        description="Miso broth and seasonal vegetables.",
        submitted_by=user,
    )
    food_item.tags.add(vegetarian)

    assert food_item.submitted_by == user
    assert list(food_item.tags.all()) == [vegetarian]


def test_menu_item_links_food_item_and_matches_current_schedule() -> None:
    food_item = FoodItem.objects.create(name="Lunch bowl")
    now = timezone.localtime(timezone.now()).replace(second=0, microsecond=0)
    menu_item = MenuItem.objects.create(
        food_item=food_item,
        weekday=now.weekday(),
        available_from=(now - timedelta(minutes=30)).time(),
        available_until=(now + timedelta(minutes=30)).time(),
    )

    assert list(MenuItem.objects.available_at(now)) == [menu_item]


def test_menu_item_rejects_an_end_time_before_its_start_time() -> None:
    menu_item = MenuItem(
        food_item=FoodItem(name="Breakfast burrito"),
        weekday=1,
        available_from="12:00",
        available_until="11:00",
    )

    with pytest.raises(ValidationError):
        menu_item.full_clean()


def test_menu_item_available_query_excludes_inactive_and_wrong_time() -> None:
    now = timezone.localtime(timezone.now()).replace(second=0, microsecond=0)
    food_item = FoodItem.objects.create(name="Dinner special")
    active = MenuItem.objects.create(
        food_item=food_item,
        weekday=now.weekday(),
        available_from=(now - timedelta(minutes=5)).time(),
        available_until=(now + timedelta(minutes=5)).time(),
    )
    MenuItem.objects.create(
        food_item=FoodItem.objects.create(name="Inactive special"),
        weekday=now.weekday(),
        available_from=(now - timedelta(minutes=5)).time(),
        available_until=(now + timedelta(minutes=5)).time(),
        is_active=False,
    )

    assert list(MenuItem.objects.available_at(now)) == [active]
