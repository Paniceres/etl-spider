import asyncio
from spider_rs import Website, Page
from urllib.parse import urlparse, parse_qs, urlunparse
from typing import Any, Dict, Set, List
from bs4 import BeautifulSoup

class GuiacoresScraper:
    def __init__(self, base_url: str = "https://www.guiacores.com.ar"):
        self.base_url = base_url
        self.detail_urls: Set[str] = set()
        self.extracted_data: List[Dict[str, Any]] = []

    def extract_detail_id(self, page: Page):
        """Extracts the detail ID from links on the search results page."""
        if not page.get_html():
            return

        # Using a simple string search for demonstration, more robust parsing might be needed
        # based on the actual HTML structure. A library like BeautifulSoup could be used here.
        html_content = page.get_html()
        if html_content:
            for line in html_content.splitlines():
                if 'span class="nombre-comercio"' in line:
                    # This is a very basic approach, assuming the href is in the same line
                    start = line.find('href="?r=search/detail&id=')
                    if start != -1:
                        start += len('href="?r=search/detail&id=')
                        end = line.find('&', start)
                        if end != -1:
                            detail_id = line[start:end]
                            detail_url = f"{self.base_url}/index.php?r=search/detail&id={detail_id}"
                            self.detail_urls.add(detail_url)
                            print(f"Found detail URL: {detail_url}")


    async def scrape_detail_page(self, page: Page):
        """Scrapes data from a detail page."""
        if not page.get_html():
            print(f"Could not get HTML for detail page: {page.url}")
            return

        print(f"Scraping detail page: {page.url}")
        data = {"url": page.url}

        # Example: Extracting the title of the page
        data["title"] = page.title()

        # **Headless browsing and interaction with "Ver más":**
        # This part requires headless browser capabilities which are supported
        # by spider_rs by setting the headless parameter to True.
        # Interacting with elements like clicking a button and waiting for
        # dynamic content to load would typically be handled with more advanced
        # browser automation libraries like Playwright or Selenium, often used
        # in conjunction with a headless browser instance controlled by spider_rs.
        # The current version of spider_rs subscription callback provides the page
        # HTML after the initial load. To interact with the page dynamically
        # after initial load (like clicking "Ver más"), you would likely need
        # to use the underlying chromiumoxide features directly or integrate
        # a separate browser automation library that can connect to the headless
        # browser instance launched by spider_rs.

        # For this example, we will assume the initial page load
        # provides enough information or that the desired data is available on initial load,
        # or that headless browsing is primarily for rendering dynamic content on load.

        # **Implement "Ver más" waiting logic here:**
        # This is a placeholder. A real implementation would
        # likely involve waiting for a specific element to appear
        # or disappear after clicking the "Ver más" button.
        # For a simple demonstration, you could add a time.sleep()
        # import time
        # time.sleep(5) # Example: Wait for 5 seconds
        pass

        # Parse the HTML content using BeautifulSoup
        # provides enough information or that the desired data is available on initial load.
        # A more complete implementation would involve checking for the "Ver más"
        # button, clicking it using headless browser capabilities, and waiting.

        # You would add code here to parse the HTML content of the detail page
        # and extract the desired data points.

        soup = BeautifulSoup(page.get_html(), 'html.parser')

        # **Add specific CSS selectors or HTML element traversal here**
        # Example: Extracting text from a specific div
        # data['some_field'] = soup.select_one('.some-class').get_text(strip=True) if soup.select_one('.some-class') else None

        self.extracted_data.append(data)
        print(f"Extracted data from {page.url}: {data}")


    async def run(self):
        """Runs the scraping process."""
        # Configure the website for the initial crawl to find detail links
        initial_website = Website(
            "https://www.guiacores.com.ar/index.php?r=search%2Findex&b=&R=&L=&Tm=1",
            # Setting raw_content to True might be useful for handling different encodings
            False
        )

        class SearchResultsSubscription:
            def __init__(self, scraper):
                self.scraper = scraper
            def __call__(self, page: Any):
                self.scraper.extract_detail_id(page)

        print("Starting initial crawl to find detail page links...")
        await initial_website.crawl(SearchResultsSubscription(self))
        print(f"Finished initial crawl. Found {len(self.detail_urls)} detail URLs.")

        if not self.detail_urls:
            print("No detail URLs found. Exiting.")
            return

        # Now, crawl each detail URL
        print("Starting to crawl detail pages...")
        detail_website = Website(self.base_url, False)  # Base URL for detail pages

        class DetailPageSubscription:
            def __init__(self, scraper):
                self.scraper = scraper
            async def __call__(self, page: Any):
                await self.scraper.scrape_detail_page(page)

        # Add all collected detail URLs to the crawl list
        # Use crawl_urls for specific URLs you want to crawl.
        detail_website = detail_website.with_urls(list(self.detail_urls))

        # Configure for headless browsing for potential "Ver más" interaction
        # Note: Actual interaction would require more advanced logic not directly
        # available through simple subscription callbacks in current spider_rs.
        # This is a placeholder to enable headless if needed for initial load.
        await detail_website.crawl(DetailPageSubscription(self), background=False, headless=True)

        print("\n--- Extracted Data ---")
        for item in self.extracted_data:
            print(item)

async def main():
    scraper = GuiacoresScraper()
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())