from urllib.parse import parse_qs, urlparse

import pytest
from django.contrib.auth import SESSION_KEY
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
