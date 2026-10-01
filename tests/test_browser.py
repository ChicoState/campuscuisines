import os

import pytest
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.contrib.sessions.backends.db import SessionStore
from django.test import override_settings
from django.urls import reverse
from django.utils.crypto import get_random_string
from playwright.sync_api import expect, sync_playwright

from accounts.models import User
from core.models import ImageAsset


@pytest.mark.browser
@pytest.mark.skipif(
    os.getenv("RUN_BROWSER_TESTS") != "true",
    reason="Set RUN_BROWSER_TESTS=true after installing Chromium.",
)
def test_homepage_renders_in_chromium(live_server) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        console_errors: list[str] = []
        page.on(
            "console",
            lambda message: (
                console_errors.append(message.text) if message.type == "error" else None
            ),
        )

        page.goto(live_server.url, wait_until="networkidle")

        expect(
            page.get_by_role("heading", name="Welcome to Campus Cuisines")
        ).to_be_visible()
        expect(page.locator("link[href*='core/site.css']")).to_have_count(1)
        assert not console_errors
        browser.close()


@pytest.mark.browser
@pytest.mark.skipif(
    os.getenv("RUN_BROWSER_TESTS") != "true",
    reason="Set RUN_BROWSER_TESTS=true after installing Chromium.",
)
@override_settings(DEBUG=True)
def test_image_upload_form_renders_in_chromium(live_server) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        console_errors: list[str] = []
        page.on(
            "console",
            lambda message: (
                console_errors.append(message.text) if message.type == "error" else None
            ),
        )

        page.goto(f"{live_server.url}/images/upload/", wait_until="networkidle")

        expect(page.get_by_role("heading", name="Upload an image")).to_be_visible()
        expect(page.get_by_label("File")).to_be_visible()
        expect(page.get_by_label("Alt text")).to_be_visible()
        expect(page.get_by_role("button", name="Upload image")).to_be_visible()
        assert not console_errors
        browser.close()


@pytest.mark.browser
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(
    os.getenv("RUN_BROWSER_TESTS") != "true",
    reason="Set RUN_BROWSER_TESTS=true after installing Chromium.",
)
def test_owner_can_render_an_unpublished_image_in_chromium(
    live_server, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = User.objects.create_user(
        username="image-owner", password=get_random_string(32)
    )
    asset = ImageAsset.objects.create(
        file="images/campus-meal.png",
        alt_text="A campus meal",
        uploaded_by=user,
    )
    monkeypatch.setattr(
        "core.views.signed_image_url",
        lambda _asset, _viewer: (
            "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
        ),
    )
    session = SessionStore()
    session[SESSION_KEY] = str(user.pk)
    session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
    session[HASH_SESSION_KEY] = user.get_session_auth_hash()
    session.save()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context()
        context.add_cookies(
            [
                {
                    "name": "sessionid",
                    "value": session.session_key,
                    "url": live_server.url,
                }
            ]
        )
        page = context.new_page()
        console_errors: list[str] = []
        page.on(
            "console",
            lambda message: (
                console_errors.append(message.text) if message.type == "error" else None
            ),
        )

        page.goto(
            f"{live_server.url}{reverse('image-detail', kwargs={'pk': asset.pk})}",
            wait_until="networkidle",
        )

        expect(page.get_by_role("heading", name="Uploaded image")).to_be_visible()
        expect(page.get_by_role("img", name="A campus meal")).to_be_visible()
        assert not console_errors
        browser.close()
