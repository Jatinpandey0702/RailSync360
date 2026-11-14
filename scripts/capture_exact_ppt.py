import asyncio
import os
from playwright.async_api import async_playwright
from PIL import Image

OUT_DIR = r"c:\Users\imja3\Downloads\ADBMS EXP-9\docs\ppt_screenshots"
os.makedirs(OUT_DIR, exist_ok=True)

async def capture_all():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            headless=True
        )
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # -------------------------------------------------------------------
        # Slide 1: Left portrait image (5.00" x 7.50", 2:3 ratio) -> 800 x 1200
        # Prompt: Deep navy background (#1B1B27) with subtle vertical security stripes,
        # modern train logo icon, bold typography reading 'RailSync 360'
        # -------------------------------------------------------------------
        print("Rendering Slide 1 visual...")
        await page.goto("http://localhost:5173/", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        # Capture the train search brand card / train route overview
        await page.screenshot(
            path=os.path.join(OUT_DIR, "slide_01.png"),
            clip={"x": 50, "y": 60, "width": 550, "height": 825}
        )

        # -------------------------------------------------------------------
        # Slide 2: Right portrait image (5.00" x 7.50", 2:3 ratio) -> 800 x 1200
        # Content: Problem Definition & Reservation Trilemma
        # -------------------------------------------------------------------
        print("Rendering Slide 2 visual...")
        # Search to show results
        btn = await page.query_selector('button[type="submit"]')
        if btn:
            await btn.click()
            await page.wait_for_timeout(1200)
        await page.screenshot(
            path=os.path.join(OUT_DIR, "slide_02.png"),
            clip={"x": 480, "y": 150, "width": 560, "height": 840}
        )

        # -------------------------------------------------------------------
        # Slide 3: Left area for Problem Definition / Objectives (5.5" x 6.0")
        # -------------------------------------------------------------------
        print("Rendering Slide 3 visual...")
        await page.screenshot(
            path=os.path.join(OUT_DIR, "slide_03.png"),
            clip={"x": 50, "y": 80, "width": 640, "height": 720}
        )

        # -------------------------------------------------------------------
        # Slide 4: Right portrait image (5.00" x 7.50", 2:3 ratio) -> 800 x 1200
        # Content: Comparative Database Topology
        # -------------------------------------------------------------------
        print("Rendering Slide 4 visual...")
        # Login as admin to see diagnostics & outbox
        await page.goto("http://localhost:5173/login", wait_until="networkidle")
        await page.fill('input[type="email"]', "admin@railsync.internal")
        await page.fill('input[type="password"]', "admin123")
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(1200)

        await page.goto("http://localhost:5173/admin", wait_until="networkidle")
        await page.wait_for_timeout(1200)
        await page.screenshot(
            path=os.path.join(OUT_DIR, "slide_04.png"),
            clip={"x": 500, "y": 80, "width": 560, "height": 840}
        )

        # -------------------------------------------------------------------
        # Slide 7: Left portrait image (5.00" x 7.50", 2:3 ratio) -> 800 x 1200
        # Content: Core Algorithms, Locking & Guarantees
        # -------------------------------------------------------------------
        print("Rendering Slide 7 visual...")
        await page.goto("http://localhost:5173/trips", wait_until="networkidle")
        await page.wait_for_timeout(1200)
        await page.screenshot(
            path=os.path.join(OUT_DIR, "slide_07.png"),
            clip={"x": 480, "y": 80, "width": 560, "height": 840}
        )

        # -------------------------------------------------------------------
        # Slide 8: Wide landscape screenshot showcase (11.89" x 4.80") -> 1400 x 560
        # Content: User Interface Walkthrough (Live Radar / App showcase)
        # -------------------------------------------------------------------
        print("Rendering Slide 8 visual...")
        await page.goto("http://localhost:5173/live-status", wait_until="networkidle")
        await page.wait_for_timeout(1200)
        await page.screenshot(
            path=os.path.join(OUT_DIR, "slide_08.png"),
            clip={"x": 50, "y": 80, "width": 1340, "height": 620}
        )

        # -------------------------------------------------------------------
        # Slide 9: Right side landscape image (4.80" x 4.20") -> 960 x 840
        # Content: Verification & Concurrency Stress Testing
        # -------------------------------------------------------------------
        print("Rendering Slide 9 visual...")
        await page.goto("http://localhost:5173/trends", wait_until="networkidle")
        await page.wait_for_timeout(1500)
        await page.screenshot(
            path=os.path.join(OUT_DIR, "slide_09.png"),
            clip={"x": 200, "y": 100, "width": 1040, "height": 720}
        )

        # -------------------------------------------------------------------
        # Slide 10: Right side image box (3.83" x 3.12") -> 760 x 620
        # Content: Security & System Architecture Highlights
        # -------------------------------------------------------------------
        print("Rendering Slide 10 visual...")
        await page.goto("http://localhost:5173/login", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        await page.screenshot(
            path=os.path.join(OUT_DIR, "slide_10.png"),
            clip={"x": 380, "y": 120, "width": 680, "height": 550}
        )

        await browser.close()
        print("Playwright captures complete!")

asyncio.run(capture_all())
