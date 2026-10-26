from django.contrib.admin.views.decorators import staff_member_required
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from announcements.models import Announcement, AnnouncementDismissal


def _dismissal_owner(request: HttpRequest) -> dict[str, object]:
    if request.user.is_authenticated:  # type: ignore[union-attr]
        return {"user": request.user, "session_key": None}  # type: ignore[attr-defined]

    if request.session.session_key is None:  # type: ignore[attr-defined]
        request.session.save()  # type: ignore[attr-defined]
    return {"user": None, "session_key": request.session.session_key}  # type: ignore[attr-defined]


def dismiss(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method != "POST":
        return HttpResponse(status=405)

    announcement = get_object_or_404(Announcement, pk=pk, is_active=True)
    try:
        with transaction.atomic():  # type: ignore[reportGeneralTypeIssues]
            AnnouncementDismissal.objects.create(
                announcement=announcement, **_dismissal_owner(request)
            )
    except IntegrityError:
        pass

    next_url = request.POST.get("next", "")
    if url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect("home")


def history(request: HttpRequest) -> HttpResponse:
    announcements = Announcement.objects.all()
    return render(
        request,
        "announcements/history.html",
        {"announcements": announcements},
    )


@staff_member_required
def reannounce(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method != "POST":
        return HttpResponse(status=405)

    announcement = get_object_or_404(Announcement, pk=pk)
    with transaction.atomic():  # type: ignore[reportGeneralTypeIssues]
        announcement.is_active = True
        announcement.save(update_fields=["is_active"])
        announcement.dismissals.all().delete()

    return redirect("announcement-history")
