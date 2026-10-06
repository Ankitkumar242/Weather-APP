import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Test widths from 700 to 1100 in steps of 50
        for w in range(700, 1150, 50):
            page = await browser.new_page(viewport={"width": w, "height": 800})
            await page.goto("http://127.0.0.1:8000?state=rajasthan", wait_until="networkidle")
            # Set dark theme
            await page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
            await page.wait_for_selector("#select-state", timeout=5000)

            # Check if select-state or its siblings overflow the card or the window
            data = await page.evaluate('''() => {
                const sel = document.getElementById("select-state");
                const selSort = document.getElementById("select-city-sort");
                const btnAll = document.getElementById("btn-show-all-india");
                const card = sel.closest(".glass-card");
                const cardRect = card.getBoundingClientRect();
                const docWidth = document.documentElement.clientWidth;

                const rSel = sel.getBoundingClientRect();
                const rSort = selSort ? selSort.getBoundingClientRect() : null;
                const rBtn = btnAll ? btnAll.getBoundingClientRect() : null;

                return {
                    docWidth,
                    cardRight: cardRect.right,
                    selRight: rSel.right,
                    sortRight: rSort ? rSort.right : null,
                    btnRight: rBtn ? rBtn.right : null,
                    overflowCard: (rSel.right > cardRect.right) || (rSort && rSort.right > cardRect.right) || (rBtn && rBtn.right > cardRect.right),
                    overflowDoc: (rSel.right > docWidth) || (rSort && rSort.right > docWidth) || (rBtn && rBtn.right > docWidth),
                };
            }''')
            print(f"Width {w}px: {data}")
            if data['overflowCard'] or data['overflowDoc']:
                await page.screenshot(path=f"screenshots/overflow_found_{w}.png")
                print(f"!!! OVERFLOW FOUND AT {w}px!")
        await browser.close()

asyncio.run(run())

