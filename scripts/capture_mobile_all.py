import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 375, "height": 667})
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        await page.wait_for_selector(".hero-card", timeout=8000)

        # 1. Today View Mobile
        await page.screenshot(path="screenshots/mobile_375_today_fixed.png")
        print("Captured mobile_375_today_fixed.png")

        # 2. Timeline View Mobile
        await page.click('.bottom-nav [data-tab="timeline"]')
        await page.wait_for_timeout(600)
        await page.screenshot(path="screenshots/mobile_375_timeline_fixed.png")
        print("Captured mobile_375_timeline_fixed.png")

        # 3. State Dashboard View Mobile
        await page.click('.bottom-nav [data-tab="states"]')
        await page.wait_for_timeout(800)
        await page.screenshot(path="screenshots/mobile_375_states_fixed.png")
        print("Captured mobile_375_states_fixed.png")

        # 4. Settings Modal Mobile
        await page.click("#btn-open-settings")
        await page.wait_for_timeout(500)
        await page.screenshot(path="screenshots/mobile_375_settings_fixed.png")
        print("Captured mobile_375_settings_fixed.png")

        await browser.close()

asyncio.run(run())
