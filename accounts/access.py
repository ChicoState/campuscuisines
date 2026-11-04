from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.views import redirect_to_login
from django.http import HttpRequest, HttpResponse

from .models import User


def is_eligible_user(user: Any) -> bool:
    if not isinstance(user, User) or not user.is_authenticated or not user.is_active:
        return False
    try:
        _, domain = str(user.email).lower().rsplit("@", 1)
    except ValueError:
        return False
    return domain in settings.GOOGLE_OAUTH_ALLOWED_EMAIL_DOMAINS


def eligible_login_required[ViewT: Callable[..., HttpResponse]](view: ViewT) -> ViewT:
    @wraps(view)
    def wrapped(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not is_eligible_user(getattr(request, "user", None)):
            return redirect_to_eligible_login(request)
        return view(request, *args, **kwargs)

    return wrapped  # type: ignore[return-value]


def redirect_to_eligible_login(request: HttpRequest) -> HttpResponse:
    if getattr(request, "user", None) is not None and request.user.is_authenticated:  # type: ignore[reportAttributeAccessIssue]
        logout(request)
    return redirect_to_login(request.get_full_path())
