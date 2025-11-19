"""
Test script for art auction scraper
Helps you inspect websites and validate selectors
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


def setup_driver(headless=False):
    """Set up Chrome WebDriver"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def test_christies():
    """Test Christie's website and inspect HTML"""
    print("\n" + "="*60)
    print("TESTING CHRISTIE'S SCRAPER")
    print("="*60)

    driver = setup_driver(headless=False)  # Visible browser

    try:
        # Navigate to Christie's November 2025 results
        url = "https://www.christies.com/en/results?month=11&year=2025"
        print(f"\n1. Loading: {url}")
        driver.get(url)

        print("2. Waiting for page to load...")
        time.sleep(5)

        # Scroll a bit
        print("3. Scrolling to load content...")
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)

        # Save page source for inspection
        html_file = 'data/christies_page_source.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"4. Saved HTML to: {html_file}")

        # Parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'lxml')

        # Try to find lot items with various selectors
        print("\n5. Searching for lot items with different selectors:")

        selectors = [
            ('div with "lot" class', 'div', lambda x: x and 'lot' in x.lower()),
            ('div with "result" class', 'div', lambda x: x and 'result' in x.lower()),
            ('article with "lot" class', 'article', lambda x: x and 'lot' in x.lower()),
            ('div with "item" class', 'div', lambda x: x and 'item' in x.lower()),
        ]

        for name, tag, class_filter in selectors:
            items = soup.find_all(tag, class_=class_filter)
            print(f"   - {name}: {len(items)} found")

        # Look for common text patterns
        print("\n6. Looking for price patterns in text:")
        text = driver.page_source
        price_indicators = ['$', '£', '€', 'USD', 'GBP', 'EUR', 'sold for', 'price realized']
        for indicator in price_indicators:
            count = text.lower().count(indicator.lower())
            print(f"   - '{indicator}': {count} occurrences")

        print("\n7. Browser will stay open for 30 seconds for manual inspection...")
        print("   - Right-click on elements and select 'Inspect'")
        print("   - Look for CSS classes for artist, title, price")
        print("   - Note down the selectors you find")
        time.sleep(30)

        print("\n✓ Christie's test complete")

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
    finally:
        driver.quit()


def test_sothebys():
    """Test Sotheby's website and inspect HTML"""
    print("\n" + "="*60)
    print("TESTING SOTHEBY'S SCRAPER")
    print("="*60)

    email = os.getenv('SOTHEBYS_EMAIL')
    password = os.getenv('SOTHEBYS_PASSWORD')

    if not email or not password:
        print("\n⚠ WARNING: Sotheby's credentials not found in .env")
        print("  Set SOTHEBYS_EMAIL and SOTHEBYS_PASSWORD to test login")
        print("  Continuing without login test...")
        time.sleep(3)

    driver = setup_driver(headless=False)

    try:
        # Test login (if credentials provided)
        if email and password:
            print("\n1. Testing login to Sotheby's...")
            driver.get("https://www.sothebys.com/en/login")
            time.sleep(3)

            print("2. Browser opened at login page")
            print("   - Look for email/password field IDs")
            print("   - Look for submit button selector")
            print("   - Try logging in manually if needed")
            time.sleep(10)

        # Navigate to November 2025 results
        url = "https://www.sothebys.com/en/results?from=11%2F1%2F2025&to=11%2F30%2F2025"
        print(f"\n3. Loading results page: {url}")
        driver.get(url)
        time.sleep(5)

        # Scroll
        print("4. Scrolling to load content...")
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)

        # Save page source
        html_file = 'data/sothebys_page_source.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"5. Saved HTML to: {html_file}")

        # Parse
        soup = BeautifulSoup(driver.page_source, 'lxml')

        print("\n6. Searching for auction/result elements:")

        # Look for links
        view_links = soup.find_all('a', string=lambda x: x and 'view' in x.lower())
        print(f"   - Links with 'view': {len(view_links)}")

        auction_links = soup.find_all('a', string=lambda x: x and 'auction' in x.lower())
        print(f"   - Links with 'auction': {len(auction_links)}")

        result_links = soup.find_all('a', string=lambda x: x and 'result' in x.lower())
        print(f"   - Links with 'result': {len(result_links)}")

        print("\n7. Looking for price-related elements:")
        price_elements = soup.find_all(['span', 'div'], class_=lambda x: x and 'price' in x.lower())
        print(f"   - Elements with 'price' class: {len(price_elements)}")

        print("\n8. Browser will stay open for 30 seconds for manual inspection...")
        print("   - Inspect auction result cards")
        print("   - Look for 'View Results' or 'View Auction' buttons")
        print("   - Note down the link structure")
        time.sleep(30)

        print("\n✓ Sotheby's test complete")

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
    finally:
        driver.quit()


def test_simple_christies():
    """Simplified Christie's test - just load and show stats"""
    print("\n" + "="*60)
    print("QUICK CHRISTIE'S TEST")
    print("="*60)

    driver = setup_driver(headless=True)

    try:
        url = "https://www.christies.com/en/results?month=11&year=2025"
        print(f"\nLoading: {url}")
        driver.get(url)
        time.sleep(5)

        # Basic stats
        soup = BeautifulSoup(driver.page_source, 'lxml')

        print("\nPage Statistics:")
        print(f"  - Total <a> tags: {len(soup.find_all('a'))}")
        print(f"  - Total <div> tags: {len(soup.find_all('div'))}")
        print(f"  - Total <article> tags: {len(soup.find_all('article'))}")
        print(f"  - Page title: {soup.title.string if soup.title else 'Not found'}")

        # Check for common class patterns
        all_classes = []
        for tag in soup.find_all(class_=True):
            all_classes.extend(tag.get('class', []))

        print(f"\n  - Unique CSS classes found: {len(set(all_classes))}")

        # Show some common classes
        from collections import Counter
        common_classes = Counter(all_classes).most_common(10)
        print("\n  Top 10 most used classes:")
        for cls, count in common_classes:
            print(f"    • {cls}: {count} times")

        print("\n✓ Quick test complete")

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
    finally:
        driver.quit()


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ART AUCTION SCRAPER - TEST SUITE")
    print("="*60)

    # Create data directory
    os.makedirs('data', exist_ok=True)

    print("\nThis test will:")
    print("1. Open Christie's in a browser (visible)")
    print("2. Open Sotheby's in a browser (visible)")
    print("3. Save HTML files for inspection")
    print("4. Show you what selectors to look for")
    print("\nEach browser will stay open for 30 seconds for manual inspection.")

    choice = input("\nChoose test:\n  1. Full test (Christie's + Sotheby's, visible browser)\n  2. Quick test (headless, stats only)\n  3. Christie's only\n  4. Sotheby's only\n\nEnter choice [1-4]: ").strip()

    if choice == '1':
        test_christies()
        test_sothebys()
    elif choice == '2':
        test_simple_christies()
    elif choice == '3':
        test_christies()
    elif choice == '4':
        test_sothebys()
    else:
        print("\nInvalid choice. Running quick test...")
        test_simple_christies()

    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("\n1. Check data/ folder for saved HTML files")
    print("2. Open HTML files in browser to inspect structure")
    print("3. Update selectors in scrapers/christies_scraper.py")
    print("4. Update selectors in scrapers/sothebys_scraper.py")
    print("5. Run: python scrapers/christies_scraper.py")
    print("6. Run: python scrapers/sothebys_scraper.py")
    print("7. Run: python main.py")
    print("\nSee TESTING.md for detailed instructions\n")


if __name__ == "__main__":
    main()
