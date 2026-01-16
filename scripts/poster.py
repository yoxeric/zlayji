import asyncio
import json
import argparse
import sys
import os
from playwright.async_api import async_playwright

COOKIE_PATH = "/opt/cookies"

class SocialPoster:
    def __init__(self, platform, image_path, caption):
        self.platform = platform.lower()
        self.image_path = os.path.abspath(image_path)
        self.caption = caption
        self.cookie_file = os.path.join(COOKIE_PATH, f"{self.platform}_cookies.json")

    async def run(self):
        if not os.path.exists(self.cookie_file):
            return {"error": f"Cookie file not found: {self.cookie_file}"}

        async with async_playwright() as p:
            # Launch browser with human-like args
            browser = await p.chromium.launch(headless=True)
            
            # Browser context with cookies
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            
            with open(self.cookie_file, 'r') as f:
                cookies = json.load(f)
                await context.add_cookies(cookies)

            page = await context.new_page()
            
            result = {"status": "failed", "platform": self.platform}

            try:
                if self.platform == "instagram":
                    result = await self.post_instagram(page)
                elif self.platform == "tiktok":
                    result = await self.post_tiktok(page)
                elif self.platform == "x":
                    result = await self.post_x(page)
                elif self.platform == "pinterest":
                    result = await self.post_pinterest(page)
                else:
                    result = {"error": f"Platform {self.platform} not supported"}
            except Exception as e:
                result = {"error": str(e), "status": "error"}
            
            await browser.close()
            return result

    async def post_instagram(self, page):
        """Automates Instagram upload flow"""
        await page.goto("https://www.instagram.com/")
        await page.wait_for_load_state("networkidle")
        
        # Check if logged in (look for profile icon or similar)
        if await page.query_selector('svg[aria-label="New post"]'):
            # Click 'Create'
            await page.click('svg[aria-label="New post"]')
            
            # Select from computer
            async with page.expect_file_chooser() as fc_info:
                await page.click('button:has-text("Select from computer")')
            file_chooser = await fc_info.value
            await file_chooser.set_files(self.image_path)
            
            # Interaction chain for posting
            await page.wait_for_selector('div:has-text("Next")')
            await page.click('div:has-text("Next")') # To Crop
            await page.wait_for_timeout(1000)
            await page.click('div:has-text("Next")') # To Edit
            await page.wait_for_timeout(1000)
            
            # Fill caption
            await page.fill('div[aria-label="Write a caption..."]', self.caption)
            
            # Share
            await page.click('div:has-text("Share")')
            await page.wait_for_selector('text=Your post has been shared.', timeout=60000)
            
            return {"status": "success", "platform": "instagram"}
        return {"status": "failed", "reason": "Not logged in (cookies invalid or expired)"}

    async def post_x(self, page):
        """Automates X (Twitter) upload flow"""
        await page.goto("https://x.com/compose/post")
        await page.wait_for_load_state("networkidle")
        
        if await page.query_selector('div[data-testid="tweetTextarea_0"]'):
            # Fill caption
            await page.fill('div[data-testid="tweetTextarea_0"]', self.caption)
            
            # Upload image
            async with page.expect_file_chooser() as fc_info:
                await page.click('div[aria-label="Add photos or video"]')
            file_chooser = await fc_info.value
            await file_chooser.set_files(self.image_path)
            
            # Wait for upload to complete (Post button becomes enabled)
            await page.wait_for_selector('div[data-testid="tweetButton"]', state="visible")
            await page.click('div[data-testid="tweetButton"]')
            
            return {"status": "success", "platform": "x"}
        return {"status": "failed", "reason": "Not logged in"}

    async def post_tiktok(self, page):
        """Automates TikTok upload flow (Desktop Web)"""
        await page.goto("https://www.tiktok.com/upload")
        await page.wait_for_load_state("networkidle")
        
        # TikTok upload often uses an iframe or specific dropzone
        iframe_element = await page.wait_for_selector('iframe[src*="tiktok.com/web-upload"]')
        frame = await iframe_element.content_frame()
        
        if frame:
            async with frame.expect_file_chooser() as fc_info:
                await frame.click('div:has-text("Select file")')
            file_chooser = await fc_info.value
            await file_chooser.set_files(self.image_path)
            
            # Wait for upload and fill caption
            await frame.wait_for_selector('div[contenteditable="true"]')
            # Clear default filename and add caption
            await frame.focus('div[contenteditable="true"]')
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await page.keyboard.type(self.caption)
            
            # Post
            await frame.click('button:has-text("Post")')
            await frame.wait_for_selector('text=Your video is being uploaded', timeout=60000)
            
            return {"status": "success", "platform": "tiktok"}
        return {"status": "failed", "reason": "TikTok upload frame not found"}

    async def post_pinterest(self, page):
        """Automates Pinterest Pin creation"""
        await page.goto("https://www.pinterest.com/pin-builder/")
        await page.wait_for_load_state("networkidle")
        
        if await page.query_selector('input[aria-label="File upload"]'):
            # Upload
            async with page.expect_file_chooser() as fc_info:
                await page.click('div[data-test-id="media-upload-container"]')
            file_chooser = await fc_info.value
            await file_chooser.set_files(self.image_path)
            
            # Fill Title (using first part of caption)
            title = self.caption.split('\n')[0][:100]
            await page.fill('input[placeholder="Add your title"]', title)
            
            # Fill Description
            await page.fill('div[aria-label="Tell everyone what your Pin is about"]', self.caption)
            
            # Publish
            await page.click('button:has-text("Publish")')
            
            return {"status": "success", "platform": "pinterest"}
        return {"status": "failed", "reason": "Not logged in or Pin builder not accessible"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Content Engine Poster")
    parser.add_argument("platform", choices=["instagram", "tiktok", "x", "pinterest", "youtube"], help="Target platform")
    parser.add_argument("image_path", help="Path to the image/video file")
    parser.add_argument("caption", help="Caption for the post")
    
    args = parser.parse_args()
    
    poster = SocialPoster(args.platform, args.image_path, args.caption)
    result = asyncio.run(poster.run())
    print(json.dumps(result, indent=2))
