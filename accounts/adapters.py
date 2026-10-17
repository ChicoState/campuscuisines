from __future__ import annotations

from typing import Any, NoReturn, cast

from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.conf import settings
from django.http import HttpRequest, HttpResponseForbidden

from .models import User


class GoogleOnlySocialAccountAdapter(DefaultSocialAccountAdapter):
    """Accept only verified Google identities in the configured campus domains."""

    denial_exception = ImmediateHttpResponse

    def _deny(self) -> NoReturn:
        raise ImmediateHttpResponse(
            HttpResponseForbidden(
                b"Google sign-in is available only to verified eligible "
                b"campus accounts."
            )
        )

    def _identity(self, sociallogin: SocialLogin) -> tuple[str, str]:
        account = sociallogin.account
        if account is None or account.provider != "google":
            self._deny()

        account = cast(SocialAccount, account)
        extra_data = cast(dict[str, Any], account.extra_data or {})
        email = extra_data.get("email")
        if not isinstance(email, str) or not email.strip():
            self._deny()
        if extra_data.get("email_verified") is not True:
            self._deny()

        normalized_email = email.strip().lower()
        try:
            local_part, domain = normalized_email.rsplit("@", 1)
        except ValueError:
            self._deny()
        allowed_domains = settings.GOOGLE_OAUTH_ALLOWED_EMAIL_DOMAINS
        if not local_part or domain not in allowed_domains:
            self._deny()
        return normalized_email, local_part

    def pre_social_login(self, request: HttpRequest, sociallogin: SocialLogin) -> None:
        email, username = self._identity(sociallogin)
        existing_user = cast(User | None, sociallogin.user)
        if existing_user is not None and existing_user.pk:
            if str(existing_user.email).lower() != email:
                self._deny()
            return

        if User.objects.filter(username=username).exists():
            self._deny()
        if User.objects.filter(email=email).exists():
            self._deny()

        user = cast(User, sociallogin.user)
        user.email = email
        user.username = username  # type: ignore[reportAttributeAccessIssue]

    def populate_user(
        self, request: HttpRequest, sociallogin: SocialLogin, data: dict[str, Any]
    ) -> User:
        email, username = self._identity(sociallogin)
        user = cast(User, super().populate_user(request, sociallogin, data))
        user.email = email
        user.username = username  # type: ignore[reportAttributeAccessIssue]
        return user

    def is_open_for_signup(
        self, request: HttpRequest, sociallogin: SocialLogin
    ) -> bool:
        return True
