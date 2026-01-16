import os
import asyncio
import json
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

COOKIES_DIR = "cookies"

async def save_cookies(context, account_name):
    """Save browser context cookies to a file."""
    cookies = await context.cookies()
    os.makedirs(COOKIES_DIR, exist_ok=True)
    with open(f"{COOKIES_DIR}/{account_name}_cookies.json", 'w') as f:
        json.dump(cookies, f)

async def load_cookies(context, account_name):
    """Load browser context cookies from a file."""
    path = f"{COOKIES_DIR}/{account_name}_cookies.json"
    if os.path.exists(path):
        with open(path, 'r') as f:
            cookies = json.load(f)
            await context.add_cookies(cookies)
        return True
    return False

class SocialPoster:
    def __init__(self, account_name):
        self.account_name = account_name

    async def post_to_instagram(self, image_path, caption):
        """Automate Instagram web upload."""
        print(f"[{self.account_name}] Posting to Instagram...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            # Mobile emulation is often easier for Instagram uploads
            iphone_13 = p.devices['iPhone 13']
            context = await browser.new_context(**iphone_13)
            
            has_cookies = await load_cookies(context, self.account_name)
            page = await context.new_page()
            
            await page.goto("https://www.instagram.com/")
            
            if not has_cookies:
                print(f"[{self.account_name}] No cookies found. Manual login required or implement login logic.")
                # TODO: Implement login logic if needed, or ask user to provide cookies
                await browser.close()
                return False

            # Selector logic for 'Create' button and upload flow
            try:
                # This is highly dependent on IG's current web UI
                # Example: look for the 'New Post' button
                await page.click("svg[aria-label='New post']")
                # ... (Handle file picker, caption input, share button)
                print(f"[{self.account_name}] Successfully posted to Instagram.")
                await save_cookies(context, self.account_name)
            except Exception as e:
                print(f"[{self.account_name}] Error posting to Instagram: {e}")
            
            await browser.close()

    async def post_to_tiktok(self, video_path, caption):
        """Automate TikTok web upload."""
        print(f"[{self.account_name}] Posting to TikTok...")
        # Similar logic to Instagram but for TikTok's web UI
        pass

    async def post_to_x(self, image_path, caption):
        """Automate X (Twitter) web upload."""
        print(f"[{self.account_name}] Posting to X...")
        pass

async def main():
    # Example usage
    poster = SocialPoster("main_account")
    # await poster.post_to_instagram("wallpaper.jpg", "Check this out! #wallpaper")

if __name__ == "__main__":
    asyncio.run(main())
