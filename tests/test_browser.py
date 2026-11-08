import base64
import os

import pytest
from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.contrib.sessions.backends.db import SessionStore
from django.test import override_settings
from django.urls import reverse
from django.utils.crypto import get_random_string
from playwright.sync_api import expect, sync_playwright

from accounts.models import User
from core.models import ImageAsset
from reviews.models import Review, Tag, TagCategory

TEST_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": settings.STORAGES["staticfiles"],
}

ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4f50BAASvAdfA"
    "0BA+AAAAAElFTkSuQmCC"
)


@pytest.mark.browser
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(
    os.getenv("RUN_BROWSER_TESTS") != "true",
    reason="Set RUN_BROWSER_TESTS=true after installing Chromium.",
)
def test_sign_in_opens_a_dialog_and_preserves_the_page(live_server) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(live_server.url, wait_until="networkidle")

        sign_in = page.get_by_role("link", name="Sign in", exact=True)
        sign_in.click()

        dialog = page.get_by_role("dialog", name="Sign in to Campus Cuisines")
        expect(dialog).to_be_visible()
        expect(
            dialog.get_by_role("button", name="Continue with Google")
        ).to_be_visible()
        expect(
            dialog.locator('form[action="/accounts/google/login/"]')
        ).to_have_attribute("method", "post")
        expect(dialog.locator('input[name="next"]')).to_have_value("/")
        expect(dialog.locator('input[name="csrfmiddlewaretoken"]')).to_have_count(1)
        assert page.url == live_server.url + "/"

        page.mouse.click(1, 1)
        expect(dialog).not_to_be_visible()
        expect(sign_in).to_be_focused()

        sign_in.click()
        expect(dialog).to_be_visible()
        page.keyboard.press("Escape")
        expect(dialog).not_to_be_visible()
        expect(sign_in).to_be_focused()

        page.get_by_role("link", name="Continue to sign in").click()
        expect(dialog).to_be_visible()
        page.set_viewport_size({"width": 320, "height": 720})
        assert dialog.evaluate(
            "element => element.getBoundingClientRect().right <= window.innerWidth"
        )
        dialog.get_by_role("button", name="Close sign-in dialog").click()
        expect(dialog).not_to_be_visible()

        no_script = browser.new_context(java_script_enabled=False)
        fallback_page = no_script.new_page()
        fallback_page.goto(live_server.url, wait_until="networkidle")
        fallback_page.get_by_role("link", name="Sign in", exact=True).click()
        expect(
            fallback_page.get_by_role("heading", name="Sign in to Campus Cuisines")
        ).to_be_visible()
        assert fallback_page.url == live_server.url + "/accounts/login/"
        no_script.close()
        browser.close()


@pytest.mark.browser
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(
    os.getenv("RUN_BROWSER_TESTS") != "true",
    reason="Set RUN_BROWSER_TESTS=true after installing Chromium.",
)
def test_homepage_renders_in_chromium(live_server, client) -> None:
    user = User.objects.create_user(
        username="browser-student",
        email="browser-student@csuchico.edu",
        password="unused",
    )
    client.force_login(user)
    meat_type_category = TagCategory.objects.create(  # type: ignore[reportAttributeAccessIssue]
        name="Meat type"
    )
    vegetarian = Tag.objects.create(  # type: ignore[reportAttributeAccessIssue]
        category=meat_type_category, name="Vegetarian"
    )
    dietary_category = TagCategory.objects.create(  # type: ignore[reportAttributeAccessIssue]
        name="Dietary"
    )
    spicy = Tag.objects.create(  # type: ignore[reportAttributeAccessIssue]
        category=dietary_category, name="Spicy"
    )

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
        page.get_by_role("link", name="Reviews", exact=True).click()
        page.get_by_role("button", name="Make a review").click()

        review_dialog = page.get_by_role("dialog", name="Review a dish")
        expect(review_dialog).to_be_visible()
        page.mouse.click(1, 1)
        expect(review_dialog).not_to_be_visible()

        page.get_by_role("button", name="Make a review").click()
        expect(review_dialog).to_be_visible()

        expect(page.get_by_text("No reviews yet")).to_be_visible()

        page.get_by_role("button", name="Close review form").click()
        expect(review_dialog).not_to_be_visible()
        expect(page.get_by_role("link", name="Sign in", exact=True)).to_be_visible()
        page.get_by_role("link", name="Sign in", exact=True).click()
        expect(
            page.get_by_role("heading", name="Sign in to Campus Cuisines")
        ).to_be_visible()

        context = browser.new_context()
        context.add_cookies(
            [
                {
                    "name": "sessionid",
                    "value": client.cookies["sessionid"].value,
                    "url": live_server.url,
                }
            ]
        )
        page = context.new_page()
        page.goto(live_server.url, wait_until="networkidle")
        expect(
            page.get_by_role("dialog", name="Sign in to Campus Cuisines")
        ).to_have_count(0)
        expect(page.get_by_role("heading", name="Review tools")).to_have_count(0)
        expect(page.locator(".rating-picker__star")).to_have_count(0)
        expect(page.locator(".tag-dropdown")).to_have_count(0)
        page.get_by_role("link", name="Reviews", exact=True).click()
        page.get_by_role("button", name="Make a review").click()
        page.get_by_label("Dish name").fill("Mushroom ramen")
        page.get_by_label("Your name").fill("Avery")
        expect(page.get_by_role("radio")).to_have_count(5)
        stars = page.locator(".rating-picker__star")
        expect(stars).to_have_count(5)
        assert all(star.is_visible() for star in stars.all())
        assert (
            stars.first.evaluate("star => getComputedStyle(star).color")
            == "rgb(82, 96, 109)"
        )
        page.get_by_label("4 out of 5 stars — Good").click()
        expect(page.locator("[data-rating-picker-value]")).to_have_text(
            "4 out of 5 stars — Good"
        )
        expect(page.locator(".rating-picker__star--filled")).to_have_count(4)
        page.get_by_label("Your review").fill("Warm, savory, and excellent.")
        tag_dropdown = page.locator(".tag-dropdown")
        tag_dropdown.locator("summary").click()
        vegetarian_tag = page.get_by_label("Vegetarian")
        spicy_tag = page.get_by_label("Spicy")
        vegetarian_tag.check()
        spicy_tag.check()
        expect(page.locator("[data-tags-summary]")).to_have_text("2 tags selected")
        tag_dropdown.locator("summary").click()
        expect(tag_dropdown).not_to_have_attribute("open", "")
        tag_dropdown.locator("summary").click()
        expect(vegetarian_tag).to_be_checked()
        expect(spicy_tag).to_be_checked()
        page.get_by_role("button", name="Publish review").click()
        expect(page.get_by_role("heading", name="Mushroom ramen")).to_be_visible()
        expect(page.locator(".review__rating")).to_contain_text("4 out of 5 stars")
        expect(page.locator(".review__rating")).not_to_contain_text("Good")
        expect(page.locator(".review time")).to_be_visible()
        expect(page.locator("link[href*='core/site.css']")).to_have_count(1)
        assert not console_errors
        context.close()
        browser.close()

    review = Review.objects.get()  # type: ignore[reportAttributeAccessIssue]
    assert list(review.tags.all()) == [spicy, vegetarian]


@pytest.mark.browser
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(
    os.getenv("RUN_BROWSER_TESTS") != "true",
    reason="Set RUN_BROWSER_TESTS=true after installing Chromium.",
)
@override_settings(DEBUG=True, STORAGES=TEST_STORAGES)
def test_review_form_uploads_and_renders_an_image_in_chromium(
    live_server, client, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = User.objects.create_user(
        username="browser-image-student",
        email="browser-image-student@csuchico.edu",
        password="unused",
    )
    client.force_login(user)
    monkeypatch.setattr(
        "core.views.signed_image_url",
        lambda _asset, _viewer: (
            "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
        ),
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 320, "height": 720})
        page.context.add_cookies(
            [
                {
                    "name": "sessionid",
                    "value": client.cookies["sessionid"].value,
                    "url": live_server.url,
                }
            ]
        )
        console_errors: list[str] = []
        page.on(
            "console",
            lambda message: (
                console_errors.append(message.text) if message.type == "error" else None
            ),
        )

        page.goto(f"{live_server.url}/reviews/", wait_until="networkidle")
        page.get_by_role("button", name="Make a review").click()
        page.get_by_label("Dish name").fill("Mushroom ramen")
        page.get_by_label("Your name").fill("Avery")
        page.get_by_label("4 out of 5 stars — Good").click()
        page.get_by_label("Your review").fill("Warm, savory, and excellent.")
        page.get_by_label("Add an image (optional)").set_input_files(
            {
                "name": "ramen.png",
                "mimeType": "image/png",
                "buffer": ONE_PIXEL_PNG,
            }
        )
        page.get_by_role("button", name="Publish review").click()

        image = page.get_by_role("img", name="Photo of Mushroom ramen")
        expect(image).to_be_visible()
        assert (
            image.evaluate("element => getComputedStyle(element).objectFit") == "cover"
        )
        assert (
            image.evaluate("element => getComputedStyle(element).maxHeight") == "320px"
        )
        assert not console_errors
        browser.close()


@pytest.mark.browser
@pytest.mark.skipif(
    os.getenv("RUN_BROWSER_TESTS") != "true",
    reason="Set RUN_BROWSER_TESTS=true after installing Chromium.",
)
@override_settings(DEBUG=True)
def test_image_upload_requires_sign_in_in_chromium(live_server) -> None:
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

        expect(
            page.get_by_role("heading", name="Sign in to Campus Cuisines")
        ).to_be_visible()
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
        username="image-owner",
        email="image-owner@csuchico.edu",
        password=get_random_string(32),
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
