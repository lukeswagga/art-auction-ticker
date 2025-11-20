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
        """
        Generate Christie's results URL for specific month and year with category filters
        Categories: 17, 7, 22, 5 (art and paintings)
        """
        base_url = f"https://www.christies.com/en/results?month={month:02d}&year={year}"
        # Add category filters for art and paintings
        filters = "&filters=|category_17|category_7|category_22|category_5|"
        return base_url + filters

    def scrape_month(self, year: int = None, month: int = None) -> List[Dict]:
        """
        Scrape auction results for a specific month
        Multi-level scraping:
        1. Load main results page with category filters
        2. Find all "View Results" links for auctions
        3. Click into each auction to get individual lots
        4. Parse lot data (artist, title, price, etc.)
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
            time.sleep(5)

            # Scroll to load all auctions
            self.scroll_to_load_all()

            # STEP 1: Get all auction links (View Results buttons)
            auction_links = self.get_auction_links()
            print(f"Found {len(auction_links)} auctions to scrape")

            # STEP 2: Scrape each auction
            all_lots = []
            for i, auction_url in enumerate(auction_links):
                print(f"  Scraping auction {i+1}/{len(auction_links)}: {auction_url}")
                lots = self.scrape_auction_page(auction_url)
                all_lots.extend(lots)
                time.sleep(2)  # Be polite to the server

            print(f"Found {len(all_lots)} total lots from Christie's")
            return all_lots

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

    def get_auction_links(self) -> List[str]:
        """
        Get links to individual auction pages from main results page
        Looks for "View Results" buttons/links
        """
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        auction_links = []

        # TODO: Update selector based on actual HTML structure
        # Look for links/buttons that say "View Results" or similar

        # Try multiple patterns
        patterns = [
            soup.find_all('a', string=lambda x: x and 'view results' in x.lower()),
            soup.find_all('a', string=lambda x: x and 'view auction' in x.lower()),
            soup.find_all('button', string=lambda x: x and 'view results' in x.lower()),
            # Look for links in auction cards
            soup.find_all('a', class_=lambda x: x and 'auction' in x.lower()),
        ]

        for pattern in patterns:
            for link in pattern:
                href = link.get('href')
                if href:
                    # Build full URL
                    if href.startswith('/'):
                        full_url = 'https://www.christies.com' + href
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue

                    # Avoid duplicates
                    if full_url not in auction_links:
                        auction_links.append(full_url)

        return auction_links

    def scrape_auction_page(self, auction_url: str) -> List[Dict]:
        """
        Scrape individual auction page to get lot data
        Each lot has: artist, title, price, lot number, etc.
        """
        self.driver.get(auction_url)
        time.sleep(3)

        # Scroll to load all lots
        self.scroll_to_load_all()

        # Parse lots
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        lots = []

        # TODO: Update selector based on actual auction page HTML
        # Look for lot items
        lot_items = soup.find_all(['div', 'article'], class_=lambda x: x and 'lot' in x.lower())

        print(f"    Found {len(lot_items)} lots in this auction")

        for item in lot_items:
            try:
                lot_data = self.extract_sale_data(item)
                if lot_data and lot_data.get('price'):
                    lots.append(lot_data)
            except Exception as e:
                continue

        return lots

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
