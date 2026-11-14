import asyncio
import os
from playwright.async_api import async_playwright

OUTPUT_DIR = r"c:\Users\imja3\Downloads\ADBMS EXP-9\docs\ppt_screenshots"

async def capture_ppt_visuals():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            headless=True
        )
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # -------------------------------------------------------------
        # Visual 1: Title Slide Hero / Header Graphic
        # Prompt: Deep navy background, prominent logo, bold typography
        # -------------------------------------------------------------
        print("Capturing Visual 1 (Title Hero)...")
        await page.goto("http://localhost:5173/", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        # Capture the header + hero search banner
        header_el = await page.query_selector("header") or await page.query_selector("nav")
        banner_el = await page.query_selector(".bg-slate-900")
        if banner_el:
            await banner_el.screenshot(path=os.path.join(OUTPUT_DIR, "slide_01_title_cover.png"))
        else:
            await page.screenshot(path=os.path.join(OUTPUT_DIR, "slide_01_title_cover.png"), clip={"x": 0, "y": 0, "width": 1440, "height": 380})

        # -------------------------------------------------------------
        # Visual 2: Executive Summary & Problem (Search & Inventory Cards)
        # -------------------------------------------------------------
        print("Capturing Visual 2 (Executive Summary Cards)...")
        # Click search to show available scheduled journeys with inventory cards
        search_btn = await page.query_selector('button[type="submit"]')
        if search_btn:
            await search_btn.click()
            await page.wait_for_timeout(1200)
        # Capture the train services / inventory availability section
        results_el = await page.query_selector(".space-y-4")
        if results_el:
            await results_el.screenshot(path=os.path.join(OUTPUT_DIR, "slide_02_executive_summary.png"))
        else:
            await page.screenshot(path=os.path.join(OUTPUT_DIR, "slide_02_executive_summary.png"), clip={"x": 100, "y": 250, "width": 1240, "height": 550})

        # -------------------------------------------------------------
        # Visual 3: Comparative Database Topology
        # -------------------------------------------------------------
        print("Capturing Visual 3 (Comparative Database Topology)...")
        # Log in as admin to show multi-system diagnostics
        await page.goto("http://localhost:5173/login", wait_until="networkidle")
        await page.fill('input[type="email"]', "admin@railsync.internal")
        await page.fill('input[type="password"]', "admin123")
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(1200)

        await page.goto("http://localhost:5173/admin", wait_until="networkidle")
        await page.wait_for_timeout(1200)
        # Capture top admin diagnostics and system status
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "slide_03_database_topology.png"), clip={"x": 100, "y": 80, "width": 1240, "height": 500})

        # -------------------------------------------------------------
        # Visual 4: System Architecture & Data Flow (Outbox Event Telemetry)
        # -------------------------------------------------------------
        print("Capturing Visual 4 (Architecture Outbox Telemetry)...")
        # Scroll down to Transactional Outbox table
        outbox_table = await page.query_selector("table")
        if outbox_table:
            await outbox_table.screenshot(path=os.path.join(OUTPUT_DIR, "slide_04_system_architecture.png"))
        else:
            await page.screenshot(path=os.path.join(OUTPUT_DIR, "slide_04_system_architecture.png"), clip={"x": 100, "y": 550, "width": 1240, "height": 450})

        # -------------------------------------------------------------
        # Visual 5: Relational Schema & Journey Inventory (Booking Form Detail)
        # -------------------------------------------------------------
        print("Capturing Visual 5 (Relational Schema & Inventory)...")
        await page.goto("http://localhost:5173/book?journeyId=1&travelClass=AC&passengers=1", wait_until="networkidle")
        await page.wait_for_timeout(1200)
        # Capture booking form with class, fare, capacity, and passenger inputs
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "slide_05_relational_schema.png"), clip={"x": 180, "y": 80, "width": 1080, "height": 650})

        # -------------------------------------------------------------
        # Visual 6: Core Algorithms (Waitlist / Booking State in Trips)
        # -------------------------------------------------------------
        print("Capturing Visual 6 (Core Algorithms & Booking State)...")
        await page.goto("http://localhost:5173/trips", wait_until="networkidle")
        await page.wait_for_timeout(1200)
        # Capture trip cards with PNR, seat status (CNF/WL), and cancellation action
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "slide_06_core_algorithms.png"), clip={"x": 150, "y": 80, "width": 1140, "height": 650})

        # -------------------------------------------------------------
        # Visual 7: User Interface Walkthrough (Live Radar Page)
        # -------------------------------------------------------------
        print("Capturing Visual 7 (UI Walkthrough Live Radar)...")
        await page.goto("http://localhost:5173/live-status", wait_until="networkidle")
        await page.wait_for_timeout(1200)
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "slide_07_ui_walkthrough.png"), clip={"x": 100, "y": 80, "width": 1240, "height": 650})

        # -------------------------------------------------------------
        # Visual 8: Verification & Stress Testing (Trends Analytics Charts)
        # -------------------------------------------------------------
        print("Capturing Visual 8 (Booking Trends & Demand Verification)...")
        await page.goto("http://localhost:5173/trends", wait_until="networkidle")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "slide_08_verification_testing.png"), clip={"x": 100, "y": 80, "width": 1240, "height": 650})

        # -------------------------------------------------------------
        # Visual 9: Security & Authentication (Login Dialog & Credentials)
        # -------------------------------------------------------------
        print("Capturing Visual 9 (Security & Auth Portal)...")
        # Logout / go to login page
        await page.goto("http://localhost:5173/login", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "slide_09_security_auth.png"), clip={"x": 350, "y": 80, "width": 740, "height": 680})

        # -------------------------------------------------------------
        # Visual 10: Design Highlights (Full Search App Interface)
        # -------------------------------------------------------------
        print("Capturing Visual 10 (Design Highlights)...")
        await page.goto("http://localhost:5173/", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "slide_10_design_highlights.png"), clip={"x": 0, "y": 0, "width": 1440, "height": 750})

        await browser.close()
        print("All PPT screenshot visuals captured successfully!")

asyncio.run(capture_ppt_visuals())
