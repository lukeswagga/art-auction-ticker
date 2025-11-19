"""
Christie's Auction Results Scraper
Scrapes monthly auction results from Christie's website
URL Pattern: https://www.christies.com/en/results?month=MM&year=YYYY
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
from typing import List, Dict
import json


class ChristiesScraper:
    def __init__(self, headless: bool = True):
        """Initialize the Christie's scraper with Selenium WebDriver"""
        self.headless = headless
        self.driver = None

    def setup_driver(self):
        """Set up Chrome WebDriver with options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def get_url_for_month(self, year: int, month: int) -> str:
        """Generate Christie's results URL for specific month and year"""
        return f"https://www.christies.com/en/results?month={month:02d}&year={year}"

    def scrape_month(self, year: int = None, month: int = None) -> List[Dict]:
        """
        Scrape auction results for a specific month
        If year/month not provided, uses previous month
        """
        if year is None or month is None:
            # Default to previous month
            today = datetime.now()
            first_of_month = today.replace(day=1)
            last_month = first_of_month - timedelta(days=1)
            year = last_month.year
            month = last_month.month

        print(f"Scraping Christie's results for {year}-{month:02d}...")

        try:
            self.setup_driver()
            url = self.get_url_for_month(year, month)
            print(f"URL: {url}")

            self.driver.get(url)

            # Wait for page to load
            time.sleep(5)  # Initial wait for dynamic content

            # Scroll to load more items (infinite scroll)
            self.scroll_to_load_all()

            # Parse the page
            sales = self.parse_results_page()

            print(f"Found {len(sales)} auction sales from Christie's")
            return sales

        except Exception as e:
            print(f"Error scraping Christie's: {str(e)}")
            return []
        finally:
            if self.driver:
                self.driver.quit()

    def scroll_to_load_all(self):
        """Scroll page to load all dynamic content"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for content to load

            # Calculate new scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                # No more content loading
                break
            last_height = new_height

    def parse_results_page(self) -> List[Dict]:
        """Parse the results page and extract auction sale data"""
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        sales = []

        # TODO: Inspect actual Christie's HTML structure and update selectors
        # This is a placeholder - we need to inspect the real page structure

        # Look for auction lot items (common patterns)
        # We'll need to adjust these selectors based on actual HTML
        lot_items = soup.find_all(['div', 'article'], class_=lambda x: x and ('lot' in x.lower() or 'result' in x.lower() or 'item' in x.lower()))

        print(f"Found {len(lot_items)} potential lot items")

        for item in lot_items[:100]:  # Limit to first 100 to avoid overwhelming
            try:
                sale_data = self.extract_sale_data(item)
                if sale_data and sale_data.get('price'):  # Only include items with prices
                    sales.append(sale_data)
            except Exception as e:
                print(f"Error parsing individual item: {str(e)}")
                continue

        return sales

    def extract_sale_data(self, item_element) -> Dict:
        """Extract sale data from a single lot item"""
        # TODO: Update these selectors based on actual Christie's HTML
        # This is a template structure

        data = {
            'artist': None,
            'title': None,
            'price': None,
            'price_realized': None,
            'currency': 'USD',
            'auction_house': 'Christie\'s',
            'sale_date': None,
            'lot_number': None,
            'auction_title': None,
            'url': None
        }

        # Extract artist name
        artist_elem = item_element.find(['h2', 'h3', 'div'], class_=lambda x: x and 'artist' in x.lower())
        if artist_elem:
            data['artist'] = artist_elem.get_text(strip=True)

        # Extract artwork title
        title_elem = item_element.find(['h3', 'h4', 'div'], class_=lambda x: x and 'title' in x.lower())
        if title_elem:
            data['title'] = title_elem.get_text(strip=True)

        # Extract price
        price_elem = item_element.find(['span', 'div'], class_=lambda x: x and ('price' in x.lower() or 'sold' in x.lower()))
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            data['price'] = price_text
            data['price_realized'] = self.parse_price(price_text)

        # Extract URL
        link_elem = item_element.find('a', href=True)
        if link_elem:
            data['url'] = 'https://www.christies.com' + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']

        return data if data['artist'] and data['price'] else None

    def parse_price(self, price_text: str) -> int:
        """Parse price string to integer (e.g., '$1,234,567' -> 1234567)"""
        try:
            # Remove currency symbols, commas, and spaces
            cleaned = ''.join(filter(lambda x: x.isdigit(), price_text))
            return int(cleaned) if cleaned else 0
        except:
            return 0

    def save_to_json(self, sales: List[Dict], filename: str = 'christies_results.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(sales, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(sales)} sales to {filename}")


if __name__ == "__main__":
    # Test the scraper
    scraper = ChristiesScraper(headless=False)  # Set to False to see browser

    # Scrape November 2025
    results = scraper.scrape_month(year=2025, month=11)

    # Save results
    scraper.save_to_json(results, 'data/christies_november_2025.json')

    # Print sample
    if results:
        print("\nSample results:")
        for sale in results[:5]:
            print(f"- {sale.get('artist', 'Unknown')}: {sale.get('title', 'Untitled')} - {sale.get('price', 'N/A')}")
