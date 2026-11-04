from collections.abc import Iterable

from django.db.models import QuerySet

from catalog.filters import filter_tagged_queryset, get_selected_tag_ids

from .models import Review


def filter_reviews_by_tags(
    reviews: QuerySet[Review], raw_tag_ids: Iterable[str | int]
) -> QuerySet[Review]:
    selected_tag_ids = get_selected_tag_ids(raw_tag_ids)
    return filter_reviews_by_selected_tag_ids(reviews, selected_tag_ids)


def filter_reviews_by_selected_tag_ids(
    reviews: QuerySet[Review], selected_tag_ids: set[int]
) -> QuerySet[Review]:
    return filter_tagged_queryset(reviews, selected_tag_ids)
