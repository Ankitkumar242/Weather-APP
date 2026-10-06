"""Browser verification script using Playwright.
Tests all acceptance criteria, responsive viewports (375, 768, 1440 px), themes,
and captures screenshots into the artifact directory.
"""

import asyncio
import os

from playwright.async_api import async_playwright

SCREENSHOT_DIR = r"C:\Users\ankit\.gemini\antigravity\brain\d693c550-b3be-4ce7-8880-7ac2606f12c9\screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

BASE_URL = "http://127.0.0.1:8000"

async def run_verification() -> None:
    console_errors: list[str] = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # 1. Desktop 1440px (Light & Dark)
        print("Testing Desktop 1440px...")
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        
        # Load page with debug mode
        await page.goto(f"{BASE_URL}/?debug=1", wait_until="networkidle")
        await page.wait_for_selector(".hero-temp-big", timeout=10000)
        await asyncio.sleep(2) # Allow charts to render smoothly
        
        # Desktop Light Screenshot
        shot_desktop_light = os.path.join(SCREENSHOT_DIR, "desktop_1440_light.png")
        await page.screenshot(path=shot_desktop_light, full_page=True)
        print(f"Captured {shot_desktop_light}")
        
        # Toggle Dark Mode via Settings
        await page.click("#btn-open-settings")
        await page.wait_for_selector("#settings-modal.active")
        await page.click('#settings-theme [data-theme="dark"]')
        await page.click("#btn-close-settings")
        await asyncio.sleep(1)
        
        # Desktop Dark Screenshot
        shot_desktop_dark = os.path.join(SCREENSHOT_DIR, "desktop_1440_dark.png")
        await page.screenshot(path=shot_desktop_dark, full_page=True)
        print(f"Captured {shot_desktop_dark}")

        # 2. Test 15-Day Timeline Tab & Table toggle
        print("Testing 15-Day Timeline Tab...")
        await page.click('.desktop-tab-btn[data-tab="timeline"]')
        await asyncio.sleep(1)
        
        # Click Table view
        await page.click('[data-view="table"]')
        await asyncio.sleep(1)
        shot_timeline_table = os.path.join(SCREENSHOT_DIR, "timeline_table_view.png")
        await page.screenshot(path=shot_timeline_table)
        print(f"Captured {shot_timeline_table}")
        
        # Switch back to cards view and test Next 7 filter
        await page.click('[data-view="cards"]')
        await page.click('[data-segment="forecast"]')
        await asyncio.sleep(1)
        shot_timeline_forecast = os.path.join(SCREENSHOT_DIR, "timeline_forecast_segment.png")
        await page.screenshot(path=shot_timeline_forecast)
        print(f"Captured {shot_timeline_forecast}")

        # 3. Test State Dashboard
        print("Testing State Dashboard Tab...")
        await page.click('.desktop-tab-btn[data-tab="states"]')
        await page.wait_for_selector("#select-state")
        
        # Select Rajasthan
        await page.select_option("#select-state", "rajasthan")
        await page.wait_for_selector(".city-card", timeout=8000)
        await asyncio.sleep(2)
        
        shot_state_dashboard = os.path.join(SCREENSHOT_DIR, "state_dashboard_rajasthan.png")
        await page.screenshot(path=shot_state_dashboard, full_page=True)
        print(f"Captured {shot_state_dashboard}")

        # Drill down into a city (e.g. first city card in Rajasthan)
        first_city = await page.wait_for_selector(".city-card")
        if first_city:
            await first_city.click()
        await page.wait_for_selector(".hero-temp-big", timeout=8000)
        await asyncio.sleep(1)
        print("Successfully drilled down into city!")

        # 4. Tablet 768px Viewport
        print("Testing Tablet 768px...")
        page_tablet = await browser.new_page(viewport={"width": 768, "height": 1024})
        page_tablet.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        await page_tablet.goto(f"{BASE_URL}/", wait_until="networkidle")
        await page_tablet.wait_for_selector(".hero-temp-big", timeout=10000)
        await asyncio.sleep(1)
        
        shot_tablet = os.path.join(SCREENSHOT_DIR, "tablet_768.png")
        await page_tablet.screenshot(path=shot_tablet, full_page=True)
        print(f"Captured {shot_tablet}")
        await page_tablet.close()

        # 5. Mobile 375px Viewport
        print("Testing Mobile 375px...")
        page_mobile = await browser.new_page(viewport={"width": 375, "height": 667})
        page_mobile.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        await page_mobile.goto(f"{BASE_URL}/", wait_until="networkidle")
        await page_mobile.wait_for_selector(".hero-temp-big", timeout=10000)
        await asyncio.sleep(1)
        
        shot_mobile = os.path.join(SCREENSHOT_DIR, "mobile_375.png")
        await page_mobile.screenshot(path=shot_mobile, full_page=True)
        print(f"Captured {shot_mobile}")
        
        # Test mobile bottom navigation to Timeline
        await page_mobile.click('.nav-tab-btn[data-tab="timeline"]')
        await asyncio.sleep(1)
        shot_mobile_timeline = os.path.join(SCREENSHOT_DIR, "mobile_375_timeline.png")
        await page_mobile.screenshot(path=shot_mobile_timeline)
        print(f"Captured {shot_mobile_timeline}")
        await page_mobile.close()

        # 6. Test Live Search
        print("Testing Live Search...")
        await page.click('.desktop-tab-btn[data-tab="today"]')
        await page.fill("#search-input", "Bengaluru")
        await page.wait_for_selector(".search-item", timeout=6000)
        await page.click(".search-item")
        await page.wait_for_selector(".hero-temp-big", timeout=8000)
        await asyncio.sleep(1)
        print("Search selection successful!")

        # 7. Test Unit Toggle (°C to °F)
        print("Testing Unit Toggle (°C to °F)...")
        await page.click("#btn-open-settings")
        await page.wait_for_selector("#settings-modal.active")
        await page.click('#settings-unit-temp [data-unit="F"]')
        await page.click("#btn-close-settings")
        await asyncio.sleep(1)
        
        unit_text = await page.inner_text(".hero-temp-unit")
        print(f"Hero unit after toggle: {unit_text}")
        assert "°F" in unit_text, f"Expected °F but got {unit_text}"
        
        await browser.close()
        
    print("\n--- BROWSER VERIFICATION SUMMARY ---")
    print(f"Total Console Errors: {len(console_errors)}")
    if console_errors:
        print("Console errors logged:")
        for err in console_errors:
            print("  -", err)
    else:
        print("All console logs clean! Zero console errors.")

if __name__ == "__main__":
    asyncio.run(run_verification())

