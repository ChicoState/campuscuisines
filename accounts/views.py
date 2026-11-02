from allauth.socialaccount.providers.google.views import oauth2_login
from django.conf import settings
from django.contrib.auth import logout as django_logout
from django.contrib.auth.views import redirect_to_login
from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .access import is_eligible_user


def safe_next_url(request: HttpRequest) -> str:
    raw_candidate = request.POST.get("next") or request.GET.get("next") or "/"
    candidate = raw_candidate if isinstance(raw_candidate, str) else "/"
    if url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return "/"


def login(request: HttpRequest) -> HttpResponse:
    if is_eligible_user(getattr(request, "user", None)):
        return redirect(safe_next_url(request))
    if getattr(request, "user", None) is not None and request.user.is_authenticated:  # type: ignore[reportAttributeAccessIssue]
        django_logout(request)
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    return render(
        request,
        "account/login.html",
        {
            "next_url": safe_next_url(request),
        },
    )


def google_login(request: HttpRequest) -> HttpResponse:
    app = settings.SOCIALACCOUNT_PROVIDERS.get("google", {}).get("APP", {})
    if not app.get("client_id") or not app.get("secret"):
        return HttpResponse(
            b"Google sign-in is not configured on this server. Contact the site "
            b"administrator.",
            status=503,
        )
    return oauth2_login(request)


def logout(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    django_logout(request)
    return redirect("home")


def admin_login(request: HttpRequest) -> HttpResponse:
    if is_eligible_user(getattr(request, "user", None)) and not request.user.is_staff:  # type: ignore[reportAttributeAccessIssue]
        return redirect("home")
    return redirect_to_login(safe_next_url(request), login_url=reverse("account-login"))
