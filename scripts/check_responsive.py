import asyncio
from playwright.async_api import async_playwright

VIEWPORTS = [
    ("Mobile Small", 320, 568),
    ("Mobile iPhone SE", 375, 667),
    ("Mobile iPhone 12/13/14", 390, 844),
    ("Mobile Android", 412, 915),
    ("Tablet Portrait", 768, 1024),
    ("Tablet Landscape", 1024, 768),
    ("Desktop 1440", 1440, 900),
]

async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for name, width, height in VIEWPORTS:
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.goto("http://127.0.0.1:8000", wait_until="networkidle")
            await page.wait_for_selector(".hero-card", timeout=8000)

            # Check horizontal overflow
            scroll_width = await page.evaluate("document.documentElement.scrollWidth")
            client_width = await page.evaluate("document.documentElement.clientWidth")
            body_scroll_width = await page.evaluate("document.body.scrollWidth")

            overflow = scroll_width > client_width or body_scroll_width > client_width
            print(f"[{name} {width}x{height}] clientWidth={client_width}, scrollWidth={scroll_width}, bodyScrollWidth={body_scroll_width}, OVERFLOW={overflow}")
            
            # Find overflowing elements if any
            if overflow:
                overflowing_elements = await page.evaluate('''() => {
                    const elements = [];
                    const docWidth = document.documentElement.clientWidth;
                    document.querySelectorAll('*').forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.right > docWidth + 1) {
                            elements.push({
                                tag: el.tagName,
                                id: el.id,
                                className: el.className,
                                right: rect.right,
                                width: rect.width
                            });
                        }
                    });
                    return elements.slice(0, 10);
                }''')
                print(f"   Overflowing elements in {name}: {overflowing_elements}")
            
            await page.screenshot(path=f"screenshots/check_{width}.png")
        await browser.close()

asyncio.run(check())

