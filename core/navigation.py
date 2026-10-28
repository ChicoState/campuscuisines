from django.urls import reverse

NAVIGATION_ITEMS = (
    {
        "label": "Home",
        "url_name": "home",
        "active_url_names": ("home",),
    },
    {
        "label": "Reviews",
        "url_name": "reviews",
        "active_url_names": ("reviews",),
    },
    {
        "label": "Map/Locations",
        "url_name": "map",
        "active_url_names": ("map",),
    },
    {
        "label": "About Us",
        "url_name": "about",
        "active_url_names": ("about",),
    },
    {
        "label": "Account",
        "url_name": "account",
        "active_url_names": ("account",),
    },
)


def navigation(request):
    current_url_name = getattr(request.resolver_match, "url_name", None)
    items = [
        {
            **item,
            "url": reverse(item["url_name"]),
            "active": current_url_name in item["active_url_names"],
        }
        for item in NAVIGATION_ITEMS
    ]
    return {"navigation_items": items}
