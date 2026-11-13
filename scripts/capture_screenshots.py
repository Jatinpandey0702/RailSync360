import asyncio
from playwright.async_api import async_playwright

async def capture():
    async with async_playwright() as p:
        # Launch Chrome
        browser = await p.chromium.launch(
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            headless=True
        )
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # 1. Search / Home Page
        print("Capturing 01_search_page.png...")
        await page.goto("http://localhost:5173/", wait_until="networkidle")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=r"c:\Users\imja3\Downloads\ADBMS EXP-9\docs\screenshots\01_search_page.png", full_page=True)

        # 2. Login Page
        print("Capturing 02_login_page.png...")
        await page.goto("http://localhost:5173/login", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=r"c:\Users\imja3\Downloads\ADBMS EXP-9\docs\screenshots\02_login_page.png")

        # 3. Log In as Passenger
        print("Logging in as passenger...")
        await page.fill('input[type="email"]', "passenger@example.com")
        await page.fill('input[type="password"]', "Passenger123!")
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(1500)

        # 4. Booking Page
        print("Capturing 03_booking_page.png...")
        await page.goto("http://localhost:5173/book?journeyId=1&travelClass=AC&passengers=1", wait_until="networkidle")
        await page.wait_for_timeout(1200)
        await page.screenshot(path=r"c:\Users\imja3\Downloads\ADBMS EXP-9\docs\screenshots\03_booking_page.png", full_page=True)

        # 5. Trips Page (My Bookings)
        print("Capturing 04_trips_page.png...")
        await page.goto("http://localhost:5173/trips", wait_until="networkidle")
        await page.wait_for_timeout(1200)
        await page.screenshot(path=r"c:\Users\imja3\Downloads\ADBMS EXP-9\docs\screenshots\04_trips_page.png", full_page=True)

        # 6. Booking Trends & Demand Analytics Page
        print("Capturing 05_booking_trends.png...")
        await page.goto("http://localhost:5173/trends", wait_until="networkidle")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=r"c:\Users\imja3\Downloads\ADBMS EXP-9\docs\screenshots\05_booking_trends.png", full_page=True)

        # 7. Live Radar Page
        print("Capturing 06_live_radar.png...")
        await page.goto("http://localhost:5173/live-status", wait_until="networkidle")
        await page.wait_for_timeout(1200)
        await page.screenshot(path=r"c:\Users\imja3\Downloads\ADBMS EXP-9\docs\screenshots\06_live_radar.png", full_page=True)

        # 8. Admin Console (Log in as Admin)
        print("Logging in as admin...")
        await page.goto("http://localhost:5173/login", wait_until="networkidle")
        await page.fill('input[type="email"]', "admin@railsync.internal")
        await page.fill('input[type="password"]', "admin123")
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(1500)

        print("Capturing 07_admin_console.png...")
        await page.goto("http://localhost:5173/admin", wait_until="networkidle")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=r"c:\Users\imja3\Downloads\ADBMS EXP-9\docs\screenshots\07_admin_console.png", full_page=True)

        await browser.close()
        print("All screenshots captured successfully!")

asyncio.run(capture())
