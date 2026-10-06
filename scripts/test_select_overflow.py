import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for w in [320, 360, 375, 412, 600, 768, 800, 1024]:
            page = await browser.new_page(viewport={"width": w, "height": 700})
            await page.goto("http://127.0.0.1:8000?state=rajasthan", wait_until="networkidle")
            await page.wait_for_selector("#select-state", timeout=8000)

            dims = await page.eval_on_selector("#select-state", """el => {
                const rect = el.getBoundingClientRect();
                const parentRect = el.parentElement.getBoundingClientRect();
                const cardRect = el.closest(".glass-card").getBoundingClientRect();
                const docWidth = document.documentElement.clientWidth;
                return {
                    width: rect.width,
                    right: rect.right,
                    parentWidth: parentRect.width,
                    parentRight: parentRect.right,
                    cardWidth: cardRect.width,
                    cardRight: cardRect.right,
                    docWidth: docWidth,
                    overflow: rect.right > docWidth || rect.right > cardRect.right
                };
            }""")
            print(f"Viewport {w}px: {dims}")
        await browser.close()

asyncio.run(test())

