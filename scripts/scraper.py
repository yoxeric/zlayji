import os
import json
import asyncio
import requests
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

# Constants
SOURCES_URL = os.getenv("SOURCES_JSON_URL", "https://raw.githubusercontent.com/user/repo/main/sources.json")
OUTPUT_DIR = "downloads"

async def fetch_sources():
    """Fetch sources.json from GitHub or local file."""
    if SOURCES_URL.startswith("http"):
        response = requests.get(SOURCES_URL)
        response.raise_for_status()
        return response.json()
    else:
        with open(SOURCES_URL, 'r') as f:
            return json.load(f)

async def scrape_source(url, category):
    """Scrape images from a given URL using Playwright."""
    print(f"Scraping {url} for category {category}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_api_context()
        page = await page.new_page()
        
        await page.goto(url)
        
        # Handle infinite scroll
        for _ in range(5):  # Adjust scroll count as needed
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            
        # Extract image URLs (this needs to be specialized per source)
        # Example for generic images
        images = await page.evaluate("""
            () => Array.from(document.querySelectorAll('img'))
                       .map(img => img.src)
                       .filter(src => src.startsWith('http'))
        """)
        
        await browser.close()
        return images

async def main():
    try:
        sources = await fetch_sources()
        for source in sources:
            urls = await scrape_source(source['url'], source['category'])
            print(f"Found {len(urls)} images for {source['category']}")
            # TODO: Filter and download high-res versions
            # TODO: Integrate with Gemini for filtering
            
    except Exception as e:
        print(f"Error in scraper: {e}")

if __name__ == "__main__":
    asyncio.run(main())
