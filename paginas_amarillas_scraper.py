import asyncio
import csv
from spider_rs import Website, Page
from bs4 import BeautifulSoup
import re

class PaginasAmarillasScraper:
    def __init__(self, query="contadores", location="general-roca"):
        # URL format: https://www.paginasamarillas.com.ar/buscar/q/contadores/loc/general-roca/
        self.base_url = f"https://www.paginasamarillas.com.ar/buscar/q/{query}/loc/{location}/"
        self.results = []

    def handle_page(self, page: Page):
        """Callback to process each page crawled."""
        html = page.get_html()
        if not html:
            print(f"No HTML for {page.url}")
            return

        print(f"Processing page: {page.url} (Length: {len(html)})")
        print(f"HTML Snippet: {html[:200]}")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all business card containers. 
        # Based on the subagent findings, the structure uses classes starting with 'Advertise_'.
        # We can look for the title containers and traverse up or down.
        # Usually, each result is in a <li> or <div> container.
        
        # Testing the specific selectors from the browser subagent:
        # div[class*="Advertise_title__"] a
        
        titles = soup.select('div[class*="Advertise_title__"] a')
        for title_tag in titles:
            # Try to find the parent container of the result to find phone and address
            # Usually, they are siblings or inside the same parent.
            container = title_tag.find_parent('div', class_=re.compile(r'Advertise_cardContent__'))
            if not container:
                # Fallback to searching nearby
                container = title_tag.find_parent('li') or title_tag.find_parent('div', recursive=False)

            name = title_tag.get_text(strip=True)
            
            # Select from container if found, otherwise from global (less accurate)
            root = container if container else soup
            
            phone_tag = root.select_one('a[class*="Advertise_phone__"]')
            phone = phone_tag.get_text(strip=True) if phone_tag else "N/A"
            
            address_tag = root.select_one('div[class*="Advertise_address__"]')
            address = address_tag.get_text(strip=True) if address_tag else "N/A"
            
            web_tag = root.select_one('a[class*="Advertise_webURL__"]')
            website = web_tag['href'] if web_tag and web_tag.has_attr('href') else "N/A"
            
            result = {
                "Nombre": name,
                "Teléfono": phone,
                "Dirección": address,
                "Sitio Web": website,
                "URL Origen": page.url
            }
            
            # Avoid duplicates
            if result not in self.results:
                self.results.append(result)
                print(f"Found: {name} - {phone}")

    async def run(self):
        print(f"Starting crawl at: {self.base_url}")
        # Configure Website
        website = Website(self.base_url)
        # Wait for the search results to actually load (since it's dynamic)
        website.with_wait_for_selector('div[class*="Advertise_title__"]', 10000)
        # Limit to the search results pages (don't go to external sites)
        website.with_blacklist_url(["facebook.com", "instagram.com", "google.com"])
        
        # Start crawl with subscription
        website.crawl(self.handle_page, headless=True)
        
        # Save to CSV
        self.save_results()

    def save_results(self, filename="accountants_roc.csv"):
        if not self.results:
            print("No results found to save.")
            return
        
        keys = self.results[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(self.results)
        
        print(f"Saved {len(self.results)} results to {filename}")

async def main():
    scraper = PaginasAmarillasScraper()
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())
