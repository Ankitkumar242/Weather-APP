import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        print("1. Navigating to http://127.0.0.1:8000...")
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        await page.wait_for_selector(".hero-card", timeout=10000)

        # Check default English text
        today_tab_text = await page.text_content('.desktop-tab-btn[data-tab="today"]')
        print(f"Default Today tab: {today_tab_text.strip()}")
        assert "Today" in today_tab_text, "Expected 'Today' in English tab"

        lang_btn_text = await page.text_content("#btn-toggle-lang")
        print(f"Header Lang toggle text: {lang_btn_text.strip()}")

        # Click language toggle button
        print("2. Clicking #btn-toggle-lang to switch to Hindi...")
        await page.click("#btn-toggle-lang")
        await page.wait_for_timeout(600)

        # Check Hindi text
        hindi_today_tab = await page.text_content('.desktop-tab-btn[data-tab="today"]')
        print(f"Hindi Today tab: {hindi_today_tab.strip()}")
        assert "आज का मौसम" in hindi_today_tab, "Expected 'आज का मौसम' in Hindi tab"

        hero_feels = await page.text_content(".hero-feels-like")
        print(f"Hero feels like: {hero_feels.strip()}")
        assert "महसूस" in hero_feels, "Expected 'महसूस' in hero feels like"

        os.makedirs("screenshots", exist_ok=True)
        await page.screenshot(path="screenshots/desktop_hindi.png", full_page=False)
        print("Captured screenshots/desktop_hindi.png")

        # Check 15-Day Timeline tab in Hindi
        print("3. Switching to 15-Day Timeline tab in Hindi...")
        await page.click('.desktop-tab-btn[data-tab="timeline"]')
        await page.wait_for_timeout(600)
        timeline_title = await page.text_content(".timeline-header h2")
        print(f"Timeline title: {timeline_title.strip()}")
        assert "15-दिवसीय" in timeline_title, "Expected Hindi timeline title"
        await page.screenshot(path="screenshots/timeline_hindi.png", full_page=False)
        print("Captured screenshots/timeline_hindi.png")

        # Check State Dashboard tab in Hindi
        print("4. Switching to State Dashboard tab in Hindi...")
        await page.click('.desktop-tab-btn[data-tab="states"]')
        await page.wait_for_timeout(1000)
        state_title = await page.text_content(".state-controls h2")
        print(f"State dashboard title: {state_title.strip()}")
        assert "राज्य" in state_title, "Expected Hindi state title"
        await page.screenshot(path="screenshots/states_hindi.png", full_page=False)
        print("Captured screenshots/states_hindi.png")

        # Check Settings modal
        print("5. Opening Settings modal...")
        await page.click("#btn-open-settings")
        await page.wait_for_timeout(500)
        settings_modal_active = await page.is_visible("#settings-modal.active")
        print(f"Settings modal visible: {settings_modal_active}")
        await page.screenshot(path="screenshots/settings_lang.png")
        print("Captured screenshots/settings_lang.png")

        # Switch back to English in Settings modal
        print("6. Clicking English in settings modal...")
        await page.click('#settings-lang [data-lang="en"]')
        await page.wait_for_timeout(600)
        await page.click("#btn-close-settings")
        await page.wait_for_timeout(400)

        en_today_tab = await page.text_content('.desktop-tab-btn[data-tab="today"]')
        print(f"Switched back to English: {en_today_tab.strip()}")
        assert "Today" in en_today_tab, "Expected 'Today' after switching back to English"

        await browser.close()

        print(f"Console errors: {console_errors}")
        assert len(console_errors) == 0, f"Found console errors: {console_errors}"
        print("ALL LANGUAGE VERIFICATION CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    asyncio.run(main())

