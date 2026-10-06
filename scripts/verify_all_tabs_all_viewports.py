import asyncio
from playwright.async_api import async_playwright

VIEWPORTS = [
    ("Mobile 320", 320, 568),
    ("Mobile 360", 360, 640),
    ("Mobile 375", 375, 667),
    ("Mobile 390", 390, 844),
    ("Mobile 412", 412, 915),
    ("Tablet 768", 768, 1024),
    ("Laptop 1024", 1024, 768),
    ("Desktop 1440", 1440, 900),
]

TABS = ["today", "timeline", "states"]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        all_passed = True

        for vname, w, h in VIEWPORTS:
            print(f"\n--- Testing {vname} ({w}x{h}) ---")
            page = await browser.new_page(viewport={"width": w, "height": h})
            await page.goto("http://127.0.0.1:8000?state=rajasthan", wait_until="networkidle")
            # Enable dark theme
            await page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
            await page.wait_for_timeout(400)

            for tab in TABS:
                if w < 1024:
                    tab_btn = f'.bottom-nav [data-tab="{tab}"]'
                else:
                    tab_btn = f'.desktop-nav [data-tab="{tab}"]'
                
                await page.click(tab_btn)
                await page.wait_for_timeout(400)

                # Check horizontal overflow
                scroll_w = await page.evaluate("document.documentElement.scrollWidth")
                client_w = await page.evaluate("document.documentElement.clientWidth")
                body_scroll_w = await page.evaluate("document.body.scrollWidth")
                
                overflow = (scroll_w > client_w) or (body_scroll_w > client_w)
                print(f"  [{tab.upper()} tab] client={client_w}, scroll={scroll_w}, bodyScroll={body_scroll_w}, overflow={overflow}")
                
                if overflow:
                    all_passed = False
                    elements = await page.evaluate('''() => {
                        const dw = document.documentElement.clientWidth;
                        const res = [];
                        document.querySelectorAll('*').forEach(el => {
                            const r = el.getBoundingClientRect();
                            if (r.right > dw + 1) {
                                res.push({ tag: el.tagName, id: el.id, class: el.className, right: r.right, w: r.width });
                            }
                        });
                        return res.slice(0, 5);
                    }''')
                    print(f"    OVERFLOW ELEMENTS: {elements}")
                
                # If states tab, capture screenshot
                if tab == "states" and w in [375, 768, 1024]:
                    await page.screenshot(path=f"screenshots/verified_states_{w}.png")
                    print(f"    Saved screenshots/verified_states_{w}.png")

            await page.close()

        await browser.close()
        print(f"\nOVERALL RESULT: {'ALL PASSED!' if all_passed else 'FAILURES DETECTED!'}")
        assert all_passed, "Some viewports had horizontal overflow!"

if __name__ == "__main__":
    asyncio.run(main())

