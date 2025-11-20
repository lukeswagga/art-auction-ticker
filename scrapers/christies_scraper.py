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
        Intelligently find auction page links using multiple strategies
        """
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        auction_links = set()  # Use set to avoid duplicates

        # Strategy 1: Find links with auction-related text
        text_patterns = ['view results', 'view auction', 'browse sale', 'explore auction']
        for pattern in text_patterns:
            links = soup.find_all('a', string=lambda x: x and pattern in str(x).lower())
            for link in links:
                href = link.get('href')
                if href:
                    auction_links.add(self._build_full_url(href))

        # Strategy 2: Find links with auction/sale in href
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            if any(keyword in href.lower() for keyword in ['auction', 'sale', '/results/']):
                # Avoid calendar, search, and filter links
                if not any(skip in href.lower() for skip in ['calendar', 'search', 'filter', 'category']):
                    full_url = self._build_full_url(href)
                    if 'christies.com' in full_url:
                        auction_links.add(full_url)

        # Strategy 3: Find links in common container classes
        containers = soup.find_all(['div', 'article', 'section'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['sale', 'auction', 'event', 'card']
        ))
        for container in containers:
            link = container.find('a', href=True)
            if link:
                href = link.get('href')
                if href and 'auction' in href.lower() or 'sale' in href.lower():
                    auction_links.add(self._build_full_url(href))

        result = list(auction_links)
        print(f"  Found {len(result)} unique auction links using {3} strategies")
        return result

    def _build_full_url(self, href: str) -> str:
        """Build full URL from relative or absolute href"""
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            return 'https://www.christies.com' + href
        else:
            return 'https://www.christies.com/' + href

    def scrape_auction_page(self, auction_url: str) -> List[Dict]:
        """
        Scrape individual auction page to get lot data
        Uses intelligent pattern matching to find lots
        """
        self.driver.get(auction_url)
        time.sleep(3)

        # Scroll to load all lots
        self.scroll_to_load_all()

        # Parse lots
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        lots = []

        # Use multiple strategies to find lot items
        lot_items = []

        # Strategy 1: Elements with 'lot' in class
        lot_items.extend(soup.find_all(['div', 'article'], class_=lambda x: x and 'lot' in str(x).lower()))

        # Strategy 2: Elements with 'item', 'product', 'artwork' in class
        if len(lot_items) < 5:
            lot_items.extend(soup.find_all(['div', 'article'], class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['item', 'product', 'artwork', 'object']
            )))

        # Strategy 3: Look for repeating structures (likely lot listings)
        # Find divs/articles that appear multiple times with similar classes
        if len(lot_items) < 5:
            all_divs = soup.find_all(['div', 'article'])
            class_counts = {}
            for div in all_divs:
                classes = ' '.join(div.get('class', []))
                if classes:
                    class_counts[classes] = class_counts.get(classes, 0) + 1

            # Find most common class (likely the lot item class)
            if class_counts:
                most_common_class = max(class_counts.items(), key=lambda x: x[1])
                if most_common_class[1] >= 5:  # At least 5 items
                    print(f"    Detected repeating pattern: {most_common_class[0][:50]}... ({most_common_class[1]} items)")
                    lot_items = soup.find_all(['div', 'article'], class_=most_common_class[0])

        print(f"    Found {len(lot_items)} potential lots in this auction")

        for i, item in enumerate(lot_items):
            try:
                lot_data = self.extract_sale_data(item)
                if lot_data:
                    lots.append(lot_data)
                    # Print first few successful extractions
                    if len(lots) <= 3:
                        print(f"      ✓ Lot {len(lots)}: {lot_data.get('artist', 'Unknown')[:30]} - {lot_data.get('price', 'No price')}")
            except Exception as e:
                continue

        print(f"    Successfully extracted {len(lots)} lots with data")
        return lots

    def extract_sale_data(self, item_element) -> Dict:
        """
        Intelligently extract sale data using multiple strategies
        Works even if Christie's changes their HTML structure
        """
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

        # Strategy 1: Look for Christie's-specific classes (chr- prefix)
        # Strategy 2: Look for common semantic classes
        # Strategy 3: Look for headings and text patterns

        # ARTIST - try multiple approaches
        artist_selectors = [
            item_element.find(['h1', 'h2', 'h3'], class_=lambda x: x and 'artist' in str(x).lower()),
            item_element.find(['div', 'span'], class_=lambda x: x and 'artist' in str(x).lower()),
            item_element.find(['h1', 'h2', 'h3'], class_=lambda x: x and 'chr-' in str(x).lower()),
            item_element.find(['div', 'p'], class_=lambda x: x and 'maker' in str(x).lower()),
        ]

        for elem in artist_selectors:
            if elem:
                text = elem.get_text(strip=True)
                # Artist names are usually short, all caps, or have specific patterns
                if text and 10 < len(text) < 100:
                    data['artist'] = text
                    break

        # If no artist found, try finding first heading
        if not data['artist']:
            first_heading = item_element.find(['h1', 'h2', 'h3', 'h4'])
            if first_heading:
                data['artist'] = first_heading.get_text(strip=True)

        # TITLE - try multiple approaches
        title_selectors = [
            item_element.find(['h2', 'h3', 'h4'], class_=lambda x: x and 'title' in str(x).lower()),
            item_element.find(['div', 'span', 'p'], class_=lambda x: x and 'title' in str(x).lower()),
            item_element.find(['div', 'span'], class_=lambda x: x and 'description' in str(x).lower()),
        ]

        for elem in title_selectors:
            if elem:
                text = elem.get_text(strip=True)
                if text and text != data['artist']:
                    data['title'] = text
                    break

        # If no title, use second heading
        if not data['title']:
            headings = item_element.find_all(['h2', 'h3', 'h4', 'h5'])
            if len(headings) >= 2:
                data['title'] = headings[1].get_text(strip=True)
            elif len(headings) == 1:
                data['title'] = headings[0].get_text(strip=True)

        # PRICE - look for currency symbols and price patterns
        # Search all text for price indicators
        price_elem = None

        # Try class-based first
        price_selectors = [
            item_element.find(['span', 'div', 'p'], class_=lambda x: x and 'price' in str(x).lower()),
            item_element.find(['span', 'div', 'p'], class_=lambda x: x and 'sold' in str(x).lower()),
            item_element.find(['span', 'div', 'p'], class_=lambda x: x and 'realized' in str(x).lower()),
            item_element.find(['span', 'div', 'p'], class_=lambda x: x and 'hammer' in str(x).lower()),
        ]

        for elem in price_selectors:
            if elem:
                text = elem.get_text(strip=True)
                if any(sym in text for sym in ['$', '£', '€', 'USD', 'GBP', 'EUR']):
                    price_elem = elem
                    break

        # If no class-based price, search all text for currency
        if not price_elem:
            all_text_elems = item_element.find_all(['span', 'div', 'p', 'strong', 'b'])
            for elem in all_text_elems:
                text = elem.get_text(strip=True)
                # Look for price pattern: currency + numbers
                if any(sym in text for sym in ['$', '£', '€']) and any(c.isdigit() for c in text):
                    if len(text) < 50:  # Prices are usually short
                        price_elem = elem
                        break

        if price_elem:
            price_text = price_elem.get_text(strip=True)
            data['price'] = price_text
            data['price_realized'] = self.parse_price(price_text)

        # URL - find first link in element
        link_elem = item_element.find('a', href=True)
        if link_elem:
            href = link_elem['href']
            data['url'] = self._build_full_url(href)

        # LOT NUMBER - look for lot/number patterns
        lot_elem = item_element.find(['span', 'div'], class_=lambda x: x and 'lot' in str(x).lower())
        if lot_elem:
            lot_text = lot_elem.get_text(strip=True)
            # Extract number from "Lot 123" or similar
            import re
            match = re.search(r'\d+', lot_text)
            if match:
                data['lot_number'] = match.group()

        # Only return if we have at least artist OR title, and ideally price
        if (data['artist'] or data['title']):
            return data

        return None

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
