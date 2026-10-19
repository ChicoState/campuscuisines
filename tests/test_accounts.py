from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import SESSION_KEY
from django.contrib.auth.models import Permission
from django.test import override_settings
from django.urls import reverse

from accounts.models import User


@pytest.mark.django_db
def test_sign_in_page_is_google_only_and_accessible(client) -> None:
    response = client.get(reverse("account-login"))

    assert response.status_code == 200
    assert response.context["next_url"] == "/"
    assert 'method="post"' in response.content.decode()
    assert "Continue with Google" in response.content.decode()
    assert "password" not in response.content.decode().lower()
    assert "Create an account" not in response.content.decode()


@pytest.mark.django_db
def test_sign_in_page_preserves_only_a_safe_local_next_url(client) -> None:
    response = client.get(reverse("account-login") + "?next=/admin/")
    unsafe_response = client.get(
        reverse("account-login") + "?next=https://evil.example/steal"
    )

    assert response.context["next_url"] == "/admin/"
    assert unsafe_response.context["next_url"] == "/"


@pytest.mark.django_db
def test_google_login_must_be_started_with_post(client) -> None:
    response = client.get(reverse("google_login"))

    assert response.status_code == 405
    assert response.headers["Allow"] == "POST"


def test_local_password_and_signup_routes_are_not_exposed(client) -> None:
    assert client.get("/accounts/signup/").status_code == 404
    assert client.get("/accounts/password/reset/").status_code == 404


@pytest.mark.django_db
def test_logout_requires_post_and_clears_session(client) -> None:
    user = User.objects.create_user(
        username="student", email="student@csuchico.edu", password="unused"
    )
    client.force_login(user)

    get_response = client.get(reverse("account-logout"))
    post_response = client.post(reverse("account-logout"))

    assert get_response.status_code == 405
    assert post_response.status_code == 302
    assert post_response.url == reverse("home")
    assert SESSION_KEY not in client.session


def test_admin_login_enters_through_google_sign_in(client) -> None:
    response = client.get("/admin/login/?next=/admin/auth/user/")

    assert response.status_code == 302
    assert response.url == "/accounts/login/?next=/admin/auth/user/"


@pytest.mark.django_db
@override_settings(
    SOCIALACCOUNT_PROVIDERS={
        "google": {
            "APP": {
                "client_id": "test-client.apps.googleusercontent.com",
                "secret": "test-client-secret",
                "key": "",
            },
            "SCOPE": ["openid", "email", "profile"],
        }
    }
)
def test_google_login_post_redirects_to_google_authorization(client) -> None:
    response = client.post(reverse("google_login"), {"next": "/admin/"})

    assert response.status_code == 302
    assert response.url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert set(parse_qs(urlparse(response.url).query)["scope"][0].split()) == {
        "openid",
        "email",
        "profile",
    }


@pytest.mark.django_db
@override_settings(
    SOCIALACCOUNT_PROVIDERS={
        "google": {
            "APP": {
                "client_id": "test-client.apps.googleusercontent.com",
                "secret": "test-client-secret",
                "key": "",
            },
            "SCOPE": ["openid", "email", "profile"],
        }
    }
)
@pytest.mark.parametrize(
    ("email", "verified", "requested_next", "expected_status", "redirect_url"),
    [
        ("student@csuchico.edu", True, "/images/upload/", 302, "/images/upload/"),
        ("student@csuchico.edu", True, "https://evil.example/", 302, "/"),
        ("student@gmail.com", True, "/images/upload/", 403, None),
        ("student@csuchico.edu", False, "/images/upload/", 403, None),
    ],
)
def test_google_callback_enforces_identity_before_account_or_session(
    client,
    email: str,
    verified: bool,
    requested_next: str,
    expected_status: int,
    redirect_url: str | None,
) -> None:
    start = client.post(reverse("google_login"), {"next": requested_next})
    state = parse_qs(urlparse(start.url).query)["state"][0]
    identity = {
        "sub": "google-subject-1",
        "email": email,
        "email_verified": verified,
        "given_name": "Test",
    }
    with (
        patch(
            "allauth.socialaccount.providers.google.views.GoogleOAuth2Adapter.get_access_token_data",
            return_value={"access_token": "fixture", "id_token": "fixture"},
        ),
        patch(
            "allauth.socialaccount.providers.google.views.GoogleOAuth2Adapter._decode_id_token",
            return_value=identity,
        ),
    ):
        response = client.get(
            reverse("google_callback"), {"state": state, "code": "fixture"}
        )

    assert response.status_code == expected_status
    if expected_status == 302:
        assert response.url == redirect_url
        assert User.objects.get(email=email).username == "student"
        assert SocialAccount.objects.get(uid="google-subject-1").provider == "google"  # type: ignore[reportAttributeAccessIssue]
        assert SESSION_KEY in client.session
    else:
        assert not User.objects.exists()
        assert not SocialAccount.objects.exists()  # type: ignore[reportAttributeAccessIssue]
        assert SESSION_KEY not in client.session


@pytest.mark.django_db
def test_only_eligible_staff_can_enter_admin(client) -> None:
    eligible_staff = User.objects.create_user(
        username="staff", email="staff@csuchico.edu", password="unused", is_staff=True
    )
    client.force_login(eligible_staff)
    staff_response = client.get("/admin/")

    client.logout()
    eligible_non_staff = User.objects.create_user(
        username="student", email="student@csuchico.edu", password="unused"
    )
    client.force_login(eligible_non_staff)
    non_staff_response = client.get("/admin/", follow=True)

    assert staff_response.status_code == 200
    assert non_staff_response.status_code == 200
    assert non_staff_response.redirect_chain[-1] == ("/", 302)


@pytest.mark.django_db
def test_ineligible_staff_is_not_authorized_for_admin(client) -> None:
    user = User.objects.create_user(
        username="outsider",
        email="outsider@gmail.com",
        password="unused",
        is_staff=True,
    )
    client.force_login(user)

    response = client.get("/admin/", follow=True)

    assert response.status_code == 200
    assert "Sign in to Campus Cuisines" in response.content.decode()
    assert not client.session.get(SESSION_KEY)


@pytest.mark.django_db
def test_staff_cannot_administer_user_accounts_even_with_model_permissions(
    client,
) -> None:
    staff = User.objects.create_user(
        username="staff", email="staff@csuchico.edu", password="unused", is_staff=True
    )
    staff.user_permissions.add(
        *Permission.objects.filter(
            content_type__app_label="accounts",
            codename__in=["add_user", "change_user", "view_user"],
        )
    )
    client.force_login(staff)

    assert client.get("/admin/accounts/user/").status_code == 403
    assert client.get(f"/admin/accounts/user/{staff.pk}/change/").status_code == 403

    staff.refresh_from_db()
    assert not staff.is_superuser


@pytest.mark.django_db
def test_eligible_superuser_can_administer_user_accounts(client) -> None:
    operator = User.objects.create_superuser(
        username="operator", email="operator@csuchico.edu", password="unused"
    )
    client.force_login(operator)

    assert client.get("/admin/accounts/user/").status_code == 200
