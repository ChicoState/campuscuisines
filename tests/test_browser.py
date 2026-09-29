import os

import pytest
from playwright.sync_api import expect, sync_playwright


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
