import asyncio
from playwright.async_api import async_playwright
import time
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1600, "height": 900})
        print("Navigating to dashboard...")
        await page.goto("http://127.0.0.1:8000/dashboard.html", wait_until="networkidle")
        await asyncio.sleep(2)

        # Start DEMO mode
        print("Starting Demo Mode...")
        await page.click("#btn-demo")
        await asyncio.sleep(2)
        
        # Turn sound on
        print("Enabling sound...")
        await page.click("#btn-sound")
        await asyncio.sleep(1)
        
        # Take screenshot of the top half
        print("Taking top screenshot...")
        os.makedirs("C:/Users/Welcome/.gemini/antigravity-ide/brain/9c848341-d8e8-41c2-9a08-5fa53dad11ce", exist_ok=True)
        top_path = "C:/Users/Welcome/.gemini/antigravity-ide/brain/9c848341-d8e8-41c2-9a08-5fa53dad11ce/final_dashboard_top.png"
        await page.screenshot(path=top_path, type="png")
        print(f"Saved {top_path}")

        # Switch to Explainability tab
        print("Switching to Explainability tab...")
        tabs = await page.locator(".tab-btn").all()
        for t in tabs:
            text = await t.inner_text()
            if "Explainability" in text:
                await t.click()
                break
        
        await asyncio.sleep(2)
        
        # Take screenshot of the full page to capture the PINN engine
        print("Taking full page screenshot...")
        bottom_path = "C:/Users/Welcome/.gemini/antigravity-ide/brain/9c848341-d8e8-41c2-9a08-5fa53dad11ce/final_dashboard_explain.png"
        await page.screenshot(path=bottom_path, full_page=True, type="png")
        print(f"Saved {bottom_path}")
        
        # Trigger flare programmatically for a moment to see the alert update
        print("Triggering flare logic...")
        await page.evaluate("idx = 65; tick();") # Jump to flare index
        await asyncio.sleep(2)
        flare_path = "C:/Users/Welcome/.gemini/antigravity-ide/brain/9c848341-d8e8-41c2-9a08-5fa53dad11ce/final_dashboard_flare.png"
        await page.screenshot(path=flare_path, full_page=True, type="png")
        print(f"Saved {flare_path}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
