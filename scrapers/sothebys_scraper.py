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

        TODO: Update selectors after inspecting actual login page HTML
        Common field selectors to try:
        - By.ID: "email", "username", "login-email"
        - By.NAME: "email", "username"
        - By.CSS_SELECTOR: "input[type='email']"
        """
        if not self.email or not self.password:
            print("Cannot login: credentials not provided")
            return False

        try:
            print("Attempting to login to Sotheby's...")

            # Go to login page
            self.driver.get("https://www.sothebys.com/en/login")
            time.sleep(5)  # Wait for page to fully load

            # TODO: Update these selectors based on actual HTML
            # Try multiple selector patterns

            # Try to find email field
            email_field = None
            email_selectors = [
                (By.ID, "email"),
                (By.NAME, "email"),
                (By.ID, "username"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.CSS_SELECTOR, "input[name='email']"),
            ]

            for by, selector in email_selectors:
                try:
                    email_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    print(f"  Found email field: {by}='{selector}'")
                    break
                except:
                    continue

            if not email_field:
                print("  ERROR: Could not find email field - check HTML selectors")
                return False

            email_field.send_keys(self.email)
            time.sleep(1)

            # Try to find password field
            password_field = None
            password_selectors = [
                (By.ID, "password"),
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
            ]

            for by, selector in password_selectors:
                try:
                    password_field = self.driver.find_element(by, selector)
                    print(f"  Found password field: {by}='{selector}'")
                    break
                except:
                    continue

            if not password_field:
                print("  ERROR: Could not find password field - check HTML selectors")
                return False

            password_field.send_keys(self.password)
            time.sleep(1)

            # Try to find and click login button
            login_button = None
            button_selectors = [
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Sign In')]"),
                (By.XPATH, "//button[contains(text(), 'Log In')]"),
                (By.CSS_SELECTOR, "input[type='submit']"),
            ]

            for by, selector in button_selectors:
                try:
                    login_button = self.driver.find_element(by, selector)
                    print(f"  Found login button: {by}='{selector}'")
                    break
                except:
                    continue

            if not login_button:
                print("  ERROR: Could not find login button - check HTML selectors")
                return False

            login_button.click()

            # Wait for login to complete
            print("  Waiting for login to complete...")
            time.sleep(7)

            # Check if login was successful
            current_url = self.driver.current_url.lower()
            if "login" not in current_url:
                print("✓ Login successful!")
                return True
            else:
                print("✗ Login may have failed - still on login page")
                print(f"  Current URL: {self.driver.current_url}")
                return False

        except Exception as e:
            print(f"✗ Login error: {str(e)}")
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
        """
        Get links to individual auction result pages
        Looks for "View Results" or "View Auction" buttons

        TODO: Update selector after inspecting actual results page
        """
        links = []

        # Scroll to load all auctions
        self.scroll_to_load_all()

        soup = BeautifulSoup(self.driver.page_source, 'lxml')

        # Try multiple patterns to find auction links
        print("  Looking for auction links...")

        # Pattern 1: Links with "View Results" text
        view_links = soup.find_all('a', string=lambda x: x and 'view results' in x.lower())
        print(f"    Found {len(view_links)} 'View Results' links")

        for elem in view_links:
            href = elem.get('href')
            if href:
                full_url = 'https://www.sothebys.com' + href if href.startswith('/') else href
                if full_url not in links:
                    links.append(full_url)

        # Pattern 2: Links with "View Auction" text
        auction_links = soup.find_all('a', string=lambda x: x and 'view auction' in x.lower())
        print(f"    Found {len(auction_links)} 'View Auction' links")

        for elem in auction_links:
            href = elem.get('href')
            if href:
                full_url = 'https://www.sothebys.com' + href if href.startswith('/') else href
                if full_url not in links:
                    links.append(full_url)

        # Pattern 3: Buttons with these texts
        buttons = soup.find_all('button', string=lambda x: x and ('view' in x.lower() and ('results' in x.lower() or 'auction' in x.lower())))
        print(f"    Found {len(buttons)} view buttons")

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
