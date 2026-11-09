from collections import defaultdict
from collections.abc import Iterable
from typing import TypedDict

from django.db.models import QuerySet

from .models import Tag


class TagGroup(TypedDict):
    name: str
    tags: list[Tag]


def get_tag_groups() -> list[TagGroup]:
    groups: defaultdict[str, list[Tag]] = defaultdict(list)
    for tag in Tag.objects.select_related("category"):
        groups[tag.category.name].append(tag)
    return [{"name": name, "tags": tags} for name, tags in groups.items()]


def get_selected_tag_ids(raw_tag_ids: Iterable[str | int]) -> set[int]:
    requested_ids = {
        int(value) for value in raw_tag_ids if str(value).isdigit() and int(value) > 0
    }
    if not requested_ids:
        return set()
    return set(Tag.objects.filter(pk__in=requested_ids).values_list("pk", flat=True))


def filter_tagged_queryset(
    queryset: QuerySet,
    selected_tag_ids: set[int],
    relation_name: str = "tags",
) -> QuerySet:
    if not selected_tag_ids:
        return queryset

    tag_ids_by_category: dict[int, set[int]] = {}
    for tag_id, category_id in Tag.objects.filter(pk__in=selected_tag_ids).values_list(
        "pk", "category_id"
    ):
        tag_ids_by_category.setdefault(category_id, set()).add(tag_id)

    filtered_queryset = queryset
    for category_tag_ids in tag_ids_by_category.values():
        filtered_queryset = filtered_queryset.filter(
            **{f"{relation_name}__in": category_tag_ids}
        )
    return filtered_queryset.distinct()
