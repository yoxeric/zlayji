import asyncio
import json
import argparse
import sys
import re
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def scrape_wallpapers(url, scrolls=5):
    """
    Scrapes high-resolution wallpaper images from a given URL using Crawl4AI.
    Uses infinite scrolling to load content.
    """
    
    # Define the extraction strategy for images
    # We'll look for img tags and common class patterns for high-res images
    schema = {
        "name": "Wallpaper Images",
        "baseSelector": "img",
        "fields": [
            {
                "name": "src",
                "selector": "img",
                "attr": "src"
            },
            {
                "name": "alt",
                "selector": "img",
                "attr": "alt"
            },
            {
                "name": "data_src",
                "selector": "img",
                "attr": "data-src"
            }
        ]
    }
    
    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=False)
    
    browser_config = BrowserConfig(
        headless=True,
        browser_type="chromium",
    )
    
    # Configure scrolling and wait for content
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=extraction_strategy,
        js_code=[
            f"window.scrollTo(0, document.body.scrollHeight);",
            "await new Promise(r => setTimeout(r, 2000));"
        ] * scrolls, # Repeat scroll command N times
        wait_for="css:img",
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)
        
        if not result.success:
            print(json.dumps({"error": f"Scrape failed: {result.error_message}"}))
            return

        # Process results
        raw_images = json.loads(result.extracted_content)
        unique_images = []
        seen_urls = set()

        # Filtering logic for high-res images
        # 1. Look for keywords like 'original', 'high', '1080', 'raw' in URL
        # 2. Filter out small thumbnails or icons
        # 3. Many sites use data-src for original quality
        
        for img in raw_images:
            img_url = img.get('data_src') or img.get('src')
            if not img_url or img_url in seen_urls:
                continue
            
            # Basic validation for image URLs
            if not any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                continue

            # Heuristic for high-res: 
            # - Avoid 'thumb', 'small', '150x', '300x'
            # - Favor 'original', 'full', 'large', or specific dimensions
            is_thumbnail = any(pattern in img_url.lower() for pattern in ['thumb', 'small', 'icon', 'square'])
            
            if not is_thumbnail:
                seen_urls.add(img_url)
                unique_images.append({
                    "url": img_url,
                    "alt": img.get('alt', ''),
                    "platform_origin": url
                })

        # Return the final JSON list
        print(json.dumps(unique_images, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Content Engine Scraper")
    parser.add_argument("url", help="Target URL to scrape")
    parser.add_argument("--scrolls", type=int, default=5, help="Number of times to scroll down")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(scrape_wallpapers(args.url, args.scrolls))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
