"""
Sotheby's Auction Results Scraper
Scrapes monthly auction results from Sotheby's website
URL Pattern: https://www.sothebys.com/en/results?from=MM%2FDD%2FYYYY&to=MM%2FDD%2FYYYY
NOTE: Requires login to view prices
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
import os
from dotenv import load_dotenv

load_dotenv()


class SothebysScraper:
    def __init__(self, headless: bool = True):
        """Initialize the Sotheby's scraper with Selenium WebDriver"""
        self.headless = headless
        self.driver = None
        self.email = os.getenv('SOTHEBYS_EMAIL')
        self.password = os.getenv('SOTHEBYS_PASSWORD')

        if not self.email or not self.password:
            print("WARNING: Sotheby's credentials not found in .env file")
            print("Price data will not be accessible without login")

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

    def login(self) -> bool:
        """
        Login to Sotheby's account
        Returns True if successful, False otherwise
        """
        if not self.email or not self.password:
            print("Cannot login: credentials not provided")
            return False

        try:
            print("Attempting to login to Sotheby's...")

            # Go to login page
            self.driver.get("https://www.sothebys.com/en/login")
            time.sleep(3)

            # Find and fill email field
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))  # Adjust selector as needed
            )
            email_field.send_keys(self.email)

            # Find and fill password field
            password_field = self.driver.find_element(By.ID, "password")  # Adjust selector as needed
            password_field.send_keys(self.password)

            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")  # Adjust selector
            login_button.click()

            # Wait for login to complete
            time.sleep(5)

            # Check if login was successful (adjust verification logic)
            if "login" not in self.driver.current_url.lower():
                print("Login successful!")
                return True
            else:
                print("Login may have failed - still on login page")
                return False

        except Exception as e:
            print(f"Login error: {str(e)}")
            return False

    def get_url_for_month(self, year: int, month: int) -> str:
        """
        Generate Sotheby's results URL for specific month
        Format: https://www.sothebys.com/en/results?from=11%2F1%2F2025&to=11%2F30%2F2025
        """
        from calendar import monthrange

        # Get last day of month
        last_day = monthrange(year, month)[1]

        # Format dates
        from_date = f"{month}%2F1%2F{year}"
        to_date = f"{month}%2F{last_day}%2F{year}"

        # Generate timestamp filter (f0 parameter) - may need adjustment
        from_timestamp = int(datetime(year, month, 1).timestamp() * 1000)
        to_timestamp = int(datetime(year, month, last_day, 23, 59, 59).timestamp() * 1000)

        return f"https://www.sothebys.com/en/results?from={from_date}&to={to_date}&f0={from_timestamp}-{to_timestamp}&q="

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

        print(f"Scraping Sotheby's results for {year}-{month:02d}...")

        try:
            self.setup_driver()

            # Login first (required to see prices)
            if not self.login():
                print("WARNING: Continuing without login - price data may be unavailable")

            url = self.get_url_for_month(year, month)
            print(f"URL: {url}")

            self.driver.get(url)
            time.sleep(5)

            # Get list of auctions
            auctions = self.get_auction_links()
            print(f"Found {len(auctions)} auctions to scrape")

            # Scrape each auction
            all_sales = []
            for i, auction_url in enumerate(auctions[:20]):  # Limit to first 20 auctions
                print(f"Scraping auction {i+1}/{min(len(auctions), 20)}: {auction_url}")
                sales = self.scrape_auction(auction_url)
                all_sales.extend(sales)
                time.sleep(2)  # Be polite

            print(f"Found {len(all_sales)} total sales from Sotheby's")
            return all_sales

        except Exception as e:
            print(f"Error scraping Sotheby's: {str(e)}")
            return []
        finally:
            if self.driver:
                self.driver.quit()

    def get_auction_links(self) -> List[str]:
        """Get links to individual auction result pages"""
        links = []

        # Scroll to load all auctions
        self.scroll_to_load_all()

        soup = BeautifulSoup(self.driver.page_source, 'lxml')

        # TODO: Update selector based on actual Sotheby's HTML
        # Look for "View Results" or "View Auction" links
        auction_elements = soup.find_all('a', href=True, string=lambda x: x and ('view results' in x.lower() or 'view auction' in x.lower()))

        for elem in auction_elements:
            href = elem['href']
            full_url = 'https://www.sothebys.com' + href if href.startswith('/') else href
            links.append(full_url)

        return links

    def scrape_auction(self, auction_url: str) -> List[Dict]:
        """Scrape individual auction page for lot results"""
        self.driver.get(auction_url)
        time.sleep(3)

        # Scroll to load all lots
        self.scroll_to_load_all()

        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        sales = []

        # TODO: Update selectors based on actual HTML structure
        lot_items = soup.find_all(['div', 'article'], class_=lambda x: x and 'lot' in x.lower())

        for item in lot_items:
            try:
                sale_data = self.extract_sale_data(item)
                if sale_data and sale_data.get('price'):
                    sales.append(sale_data)
            except Exception as e:
                continue

        return sales

    def scroll_to_load_all(self):
        """Scroll page to load all dynamic content"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        for _ in range(10):  # Max 10 scrolls
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def extract_sale_data(self, item_element) -> Dict:
        """Extract sale data from a single lot item"""
        data = {
            'artist': None,
            'title': None,
            'price': None,
            'price_realized': None,
            'currency': 'USD',
            'auction_house': 'Sotheby\'s',
            'sale_date': None,
            'lot_number': None,
            'auction_title': None,
            'url': None
        }

        # TODO: Update selectors based on actual Sotheby's HTML

        # Extract artist
        artist_elem = item_element.find(['h2', 'h3'], class_=lambda x: x and 'artist' in x.lower())
        if artist_elem:
            data['artist'] = artist_elem.get_text(strip=True)

        # Extract title
        title_elem = item_element.find(['h3', 'h4'], class_=lambda x: x and 'title' in x.lower())
        if title_elem:
            data['title'] = title_elem.get_text(strip=True)

        # Extract price (only visible when logged in)
        price_elem = item_element.find(['span', 'div'], class_=lambda x: x and 'price' in x.lower())
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            data['price'] = price_text
            data['price_realized'] = self.parse_price(price_text)

        return data if data['artist'] and data['price'] else None

    def parse_price(self, price_text: str) -> int:
        """Parse price string to integer"""
        try:
            cleaned = ''.join(filter(lambda x: x.isdigit(), price_text))
            return int(cleaned) if cleaned else 0
        except:
            return 0

    def save_to_json(self, sales: List[Dict], filename: str = 'sothebys_results.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(sales, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(sales)} sales to {filename}")


if __name__ == "__main__":
    # Test the scraper
    scraper = SothebysScraper(headless=False)

    # Scrape November 2025
    results = scraper.scrape_month(year=2025, month=11)

    # Save results
    scraper.save_to_json(results, 'data/sothebys_november_2025.json')

    # Print sample
    if results:
        print("\nSample results:")
        for sale in results[:5]:
            print(f"- {sale.get('artist', 'Unknown')}: {sale.get('title', 'Untitled')} - {sale.get('price', 'N/A')}")
