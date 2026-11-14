import asyncio
import os
from playwright.async_api import async_playwright

async def export_slides():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            headless=True
        )
        page = await browser.new_page(viewport={"width": 1440, "height": 810})
        
        file_path = os.path.abspath(r"c:\Users\imja3\Downloads\ADBMS EXP-9\docs\presentation\index.html")
        await page.goto(f"file:///{file_path.replace(os.sep, '/')}", wait_until="networkidle")
        await page.wait_for_timeout(1000)

        # Render and capture each of the 10 slides
        for i in range(1, 11):
            slide_id = f"#slide-{i}"
            slide_el = await page.query_selector(slide_id)
            if slide_el:
                output_path = rf"c:\Users\imja3\Downloads\ADBMS EXP-9\docs\presentation\slide_{i:02d}.png"
                print(f"Exporting {output_path}...")
                await slide_el.screenshot(path=output_path)
            else:
                print(f"Slide element {slide_id} not found!")

        await browser.close()
        print("All 10 slides rendered and captured as HD images successfully!")

asyncio.run(export_slides())
