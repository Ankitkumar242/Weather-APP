import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Test on 375px mobile
        page = await browser.new_page(viewport={"width": 375, "height": 667})
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        await page.wait_for_selector(".bottom-nav", timeout=5000)

        # Click State Dashboard
        await page.click('.bottom-nav [data-tab="states"]')
        await page.wait_for_timeout(1000)

        # Select Rajasthan
        await page.select_option("#select-state", "rajasthan")
        await page.wait_for_timeout(1000)

        # Inspect select dimensions
        data = await page.evaluate('''() => {
            const sel = document.getElementById("select-state");
            const selSort = document.getElementById("select-city-sort");
            const card = sel.closest(".glass-card");
            const rect = sel.getBoundingClientRect();
            const cardRect = card.getBoundingClientRect();
            const docWidth = document.documentElement.clientWidth;
            return {
                selectWidth: rect.width,
                selectLeft: rect.left,
                selectRight: rect.right,
                cardWidth: cardRect.width,
                cardLeft: cardRect.left,
                cardRight: cardRect.right,
                docWidth: docWidth,
                selectSortRight: selSort ? selSort.getBoundingClientRect().right : null,
                isSelectOverflowingCard: rect.right > cardRect.right + 1,
                isSelectOverflowingDoc: rect.right > docWidth + 1
            };
        }''')
        print("DIMS:", data)

        await page.screenshot(path="screenshots/user_reported_bug.png")
        print("Captured screenshots/user_reported_bug.png")
        await browser.close()

asyncio.run(run())

