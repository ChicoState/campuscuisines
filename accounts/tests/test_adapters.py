from typing import cast

import pytest
from allauth.socialaccount.models import EmailAddress, SocialAccount, SocialLogin
from django.http import HttpRequest
from django.test import override_settings

from accounts.adapters import GoogleOnlySocialAccountAdapter
from accounts.models import User


def social_login(
    *,
    provider: str = "google",
    email: str | None = "student@csuchico.edu",
    verified: bool = True,
    uid: str = "google-subject-1",
) -> SocialLogin:
    account = SocialAccount(provider=provider, uid=uid)
    account.extra_data = cast(  # type: ignore[reportAttributeAccessIssue]
        dict[str, object],
        {
            "email": email,
            "email_verified": verified,
            "sub": uid,
        },
    )
    email_addresses = (
        []
        if email is None
        else [EmailAddress(email=email, verified=verified, primary=True)]
    )
    return SocialLogin(
        user=User(),
        account=account,
        email_addresses=email_addresses,
    )


@pytest.mark.django_db
def test_verified_google_identity_populates_immutable_fields() -> None:
    login = social_login()
    adapter = GoogleOnlySocialAccountAdapter()

    adapter.pre_social_login(HttpRequest(), login)
    user = adapter.populate_user(
        HttpRequest(), login, {"email": "student@csuchico.edu"}
    )

    assert user.email == "student@csuchico.edu"
    assert user.username == "student"


@pytest.mark.django_db
def test_google_userinfo_verified_email_is_accepted() -> None:
    login = social_login()
    extra_data = cast(dict[str, object], login.account.extra_data)  # type: ignore[reportAttributeAccessIssue]
    extra_data.pop("email_verified")
    extra_data["verified_email"] = True

    GoogleOnlySocialAccountAdapter().pre_social_login(HttpRequest(), login)

    assert cast(User, login.user).email == "student@csuchico.edu"


@pytest.mark.django_db
def test_overlong_email_local_part_is_denied_without_username_fallback() -> None:
    login = social_login(email=f"{'a' * 151}@csuchico.edu")

    with pytest.raises(GoogleOnlySocialAccountAdapter.denial_exception):
        GoogleOnlySocialAccountAdapter().pre_social_login(HttpRequest(), login)

    assert not User.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("provider", "email", "verified"),
    [
        ("github", "student@csuchico.edu", True),
        ("google", "student@csuchico.edu", False),
        ("google", "student@gmail.com", True),
        ("google", None, True),
    ],
)
def test_ineligible_social_identity_is_rejected(
    provider: str, email: str | None, verified: bool
) -> None:
    adapter = GoogleOnlySocialAccountAdapter()

    with pytest.raises(adapter.denial_exception):
        adapter.pre_social_login(
            HttpRequest(),
            social_login(provider=provider, email=email, verified=verified),
        )

    assert not User.objects.exists()


@pytest.mark.django_db
def test_existing_username_collision_is_rejected_without_creating_a_user() -> None:
    User.objects.create_user(
        username="student", email="other@csuchico.edu", password="unused"
    )
    adapter = GoogleOnlySocialAccountAdapter()

    with pytest.raises(adapter.denial_exception):
        adapter.pre_social_login(HttpRequest(), social_login())

    assert User.objects.count() == 1


@pytest.mark.django_db
def test_case_insensitive_username_collision_is_rejected() -> None:
    User.objects.create_user(
        username="Student", email="other@csuchico.edu", password="unused"
    )

    with pytest.raises(GoogleOnlySocialAccountAdapter.denial_exception):
        GoogleOnlySocialAccountAdapter().pre_social_login(HttpRequest(), social_login())

    assert User.objects.count() == 1


@pytest.mark.django_db
@override_settings(ACCOUNT_USERNAME_BLACKLIST=["student"])
def test_disallowed_username_is_denied_without_allauth_fallback() -> None:
    with pytest.raises(GoogleOnlySocialAccountAdapter.denial_exception):
        GoogleOnlySocialAccountAdapter().pre_social_login(HttpRequest(), social_login())

    assert not User.objects.exists()


@pytest.mark.django_db
def test_existing_social_account_must_keep_the_same_verified_email() -> None:
    user = User.objects.create_user(
        username="student", email="student@csuchico.edu", password="unused"
    )
    login = social_login(email="student@gmail.com")
    login.user = user
    adapter = GoogleOnlySocialAccountAdapter()

    with pytest.raises(adapter.denial_exception):
        adapter.pre_social_login(HttpRequest(), login)


@pytest.mark.django_db
def test_email_is_immutable_after_creation() -> None:
    user = User.objects.create_user(
        username="student", email="student@csuchico.edu", password="unused"
    )
    user.email = "changed@csuchico.edu"

    with pytest.raises(ValueError, match="email identity is immutable"):
        user.save()
