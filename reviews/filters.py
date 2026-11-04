from collections.abc import Iterable

from django.db.models import QuerySet

from .models import Review, Tag


def get_selected_tag_ids(raw_tag_ids: Iterable[str | int]) -> set[int]:
    requested_ids = {
        int(value) for value in raw_tag_ids if str(value).isdigit() and int(value) > 0
    }
    if not requested_ids:
        return set()
    return set(Tag.objects.filter(pk__in=requested_ids).values_list("pk", flat=True))


def filter_reviews_by_tags(
    reviews: QuerySet[Review], raw_tag_ids: Iterable[str | int]
) -> QuerySet[Review]:
    selected_tag_ids = get_selected_tag_ids(raw_tag_ids)
    return filter_reviews_by_selected_tag_ids(reviews, selected_tag_ids)


def filter_reviews_by_selected_tag_ids(
    reviews: QuerySet[Review], selected_tag_ids: set[int]
) -> QuerySet[Review]:
    if not selected_tag_ids:
        return reviews

    tag_ids_by_category: dict[int, set[int]] = {}
    for tag_id, category_id in Tag.objects.filter(pk__in=selected_tag_ids).values_list(
        "pk", "category_id"
    ):
        tag_ids_by_category.setdefault(category_id, set()).add(tag_id)

    filtered_reviews = reviews
    for category_tag_ids in tag_ids_by_category.values():
        filtered_reviews = filtered_reviews.filter(tags__in=category_tag_ids)
    return filtered_reviews.distinct()
