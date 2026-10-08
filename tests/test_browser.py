import os

import pytest
from playwright.sync_api import expect, sync_playwright


@pytest.mark.browser
@pytest.mark.django_db(transaction=True)
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
        expect(page.get_by_text("No reviews yet")).to_be_visible()
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
        page.get_by_role("button", name="Publish review").click()
        expect(page.get_by_role("heading", name="Mushroom ramen")).to_be_visible()
        expect(page.locator(".review__rating")).to_contain_text("4 out of 5 stars")
        expect(page.locator(".review__rating")).not_to_contain_text("Good")
        expect(page.locator(".review time")).to_be_visible()
        expect(page.locator("link[href*='core/site.css']")).to_have_count(1)
        assert not console_errors
        browser.close()
