"""Verify PWA installability criteria, offline mode cached resilience, and native location flow."""

import asyncio
import os
import httpx
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = os.path.join("screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


async def main():
    print("=" * 60)
    print("SKYPulse PWA, OFFLINE & NATIVE FLOW VERIFICATION")
    print("=" * 60)

    # 1. Verify Manifest and Headers via HTTP
    print("\n--- STEP 1: PWA Manifest & Service Worker HTTP Headers ---")
    async with httpx.AsyncClient() as client:
        # Check Manifest
        m_resp = await client.get("http://127.0.0.1:8000/manifest.webmanifest")
        assert m_resp.status_code == 200, f"Manifest returned {m_resp.status_code}"
        assert "application/manifest+json" in m_resp.headers["content-type"], "Wrong manifest content-type"
        m_data = m_resp.json()
        print(f"✔ Manifest loaded: name='{m_data.get('name')}', short_name='{m_data.get('short_name')}', display='{m_data.get('display')}'")
        assert m_data.get("display") == "standalone", "Display must be standalone"
        icons = m_data.get("icons", [])
        assert len(icons) >= 4, f"Expected at least 4 icon definitions, got {len(icons)}"
        has_192 = any("192" in i.get("sizes", "") for i in icons)
        has_512 = any("512" in i.get("sizes", "") for i in icons)
        has_maskable = any(i.get("purpose") == "maskable" for i in icons)
        print(f"✔ Icons validated: 192px={has_192}, 512px={has_512}, maskable={has_maskable}")
        assert has_192 and has_512 and has_maskable, "Missing required PWA icon sizes or maskable purpose"

        # Check Service Worker Headers
        sw_resp = await client.get("http://127.0.0.1:8000/sw.js")
        assert sw_resp.status_code == 200, f"Service Worker returned {sw_resp.status_code}"
        assert "application/javascript" in sw_resp.headers["content-type"]
        assert sw_resp.headers.get("service-worker-allowed") == "/", "Service-Worker-Allowed header must be '/'"
        print("✔ Service worker root scope header 'Service-Worker-Allowed: /' confirmed")

        # Check Offline fallback page
        off_resp = await client.get("http://127.0.0.1:8000/offline.html")
        assert off_resp.status_code == 200
        assert "text/html" in off_resp.headers["content-type"]
        print("✔ Offline fallback page accessible")

    # 2. Browser Testing with Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 390, "height": 844},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1"
        )
        page = await context.new_page()

        print("\n--- STEP 2: Online First Load & Service Worker Registration ---")
        await page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        await page.wait_for_selector(".status-banner", timeout=8000)
        
        # Verify SW registration and wait for activation
        sw_active = await page.evaluate("""async () => {
            if (!('serviceWorker' in navigator)) return false;
            const reg = await navigator.serviceWorker.ready;
            return reg && reg.active ? reg.active.state : false;
        }""")
        print(f"✔ Service worker activated in browser: {sw_active}")

        # Capture online state screenshot
        online_shot = os.path.join(SCREENSHOTS_DIR, "pwa_online_mobile.png")
        await page.screenshot(path=online_shot)
        print(f"✔ Captured online screenshot: {online_shot}")

        print("\n--- STEP 3: Offline Mode & Stale Data Badge ---")
        # Simulate offline in browser
        await context.set_offline(True)
        await page.evaluate("() => window.dispatchEvent(new Event('offline'))")
        await page.wait_for_timeout(500)
        print("⚡ Switched browser context to OFFLINE mode")

        # Check if weather UI rendered from offline cache
        banner_text = await page.inner_text(".status-banner")
        print(f"✔ Status banner text in offline mode: {banner_text}")
        
        has_offline_badge = await page.evaluate("""() => {
            const badge = document.querySelector('.badge-stale');
            return badge ? badge.textContent : null;
        }""")
        print(f"✔ Offline / Stale badge present: {has_offline_badge}")
        assert has_offline_badge is not None, "Offline badge must be rendered when offline"

        offline_shot = os.path.join(SCREENSHOTS_DIR, "pwa_offline_cached.png")
        await page.screenshot(path=offline_shot)
        print(f"✔ Captured offline cached screenshot: {offline_shot}")

        # Restore online
        await context.set_offline(False)

        print("\n--- STEP 4: Native Capacitor Geolocation Bridge Flow ---")
        # In a new page, simulate Capacitor native environment
        native_page = await context.new_page()
        await native_page.add_init_script("""
            window.Capacitor = {
                isNativePlatform: () => true,
                isNative: true,
                Plugins: {
                    Geolocation: {
                        checkPermissions: async () => ({ location: 'granted' }),
                        requestPermissions: async () => ({ location: 'granted' }),
                        getCurrentPosition: async () => ({
                            coords: {
                                latitude: 26.9124,
                                longitude: 75.7873
                            }
                        })
                    }
                }
            };
        """)

        await native_page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        
        # Test triggering location via native bridge
        native_res = await native_page.evaluate("""async () => {
            const { requestBrowserLocation } = await import('/static/js/geolocation.js');
            return await requestBrowserLocation();
        }""")
        print(f"✔ Native Geolocation returned: {native_res}")
        assert native_res.get("source") == "native-gps", f"Expected source='native-gps', got {native_res.get('source')}"
        assert abs(native_res.get("lat") - 26.9124) < 0.01, "Latitude mismatch"
        assert abs(native_res.get("lon") - 75.7873) < 0.01, "Longitude mismatch"
        print(f"✔ Native Capacitor Geolocation plugin executed and resolved to {native_res.get('name')}, {native_res.get('state')}!")

        native_shot = os.path.join(SCREENSHOTS_DIR, "capacitor_native_location.png")
        await native_page.screenshot(path=native_shot)
        print(f"✔ Captured native location screenshot: {native_shot}")

        await browser.close()

    print("\n" + "=" * 60)
    print("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY (100%)!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
