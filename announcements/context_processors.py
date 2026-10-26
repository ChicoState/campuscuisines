from django.http import HttpRequest

from announcements.models import Announcement


def announcement_panel(request: HttpRequest) -> dict[str, object]:
    queryset = Announcement.objects.filter(is_active=True)
    if request.user.is_authenticated:  # type: ignore[union-attr]
        queryset = queryset.exclude(dismissals__user=request.user)  # type: ignore[attr-defined]
    elif request.session.session_key:  # type: ignore[attr-defined]
        queryset = queryset.exclude(  # type: ignore[attr-defined]
            dismissals__session_key=request.session.session_key  # type: ignore[attr-defined]
        )

    return {
        "announcement_items": queryset,
        "announcement_count": queryset.count(),
    }
