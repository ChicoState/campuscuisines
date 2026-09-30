from django.contrib.staticfiles import finders
from django.urls import reverse


def test_homepage_returns_a_welcome_page(client) -> None:
    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert "Campus Cuisines" in response.content.decode()


def test_homepage_stylesheet_is_discoverable() -> None:
    assert finders.find("core/site.css")
