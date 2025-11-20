"""
UPDATED Test script for multi-level art auction scraping
Shows you the HTML at each level:
1. Main results page with category filters
2. Individual auction pages (after clicking "View Results")
3. Individual lot data within auctions
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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


def test_christies_multilevel():
    """Test Christie's multi-level scraping: results page -> auction pages -> lots"""
    print("\n" + "="*60)
    print("TESTING CHRISTIE'S MULTI-LEVEL SCRAPING")
    print("="*60)

    driver = setup_driver(headless=False)

    try:
        # LEVEL 1: Main results page with category filters
        print("\n[LEVEL 1] Main Results Page with Category Filters")
        print("-" * 60)

        url = "https://www.christies.com/en/results?month=11&year=2025&filters=|category_17|category_7|category_22|category_5|"
        print(f"URL: {url}")
        driver.get(url)
        time.sleep(5)

        # Scroll a bit
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)

        # Save HTML
        with open('data/christies_level1_results_page.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("✓ Saved: data/christies_level1_results_page.html")

        # Parse and find auction links
        soup = BeautifulSoup(driver.page_source, 'lxml')

        print("\nLooking for 'View Results' or auction links:")

        # Try different patterns
        view_results_links = soup.find_all('a', string=lambda x: x and 'view results' in x.lower())
        print(f"  - Links with 'View Results' text: {len(view_results_links)}")

        view_auction_links = soup.find_all('a', string=lambda x: x and 'view auction' in x.lower())
        print(f"  - Links with 'View Auction' text: {len(view_auction_links)}")

        auction_class_links = soup.find_all('a', class_=lambda x: x and 'auction' in x.lower())
        print(f"  - Links with 'auction' in class: {len(auction_class_links)}")

        all_links = soup.find_all('a', href=True)
        print(f"  - Total <a> tags: {len(all_links)}")

        print("\n⏸ Browser will stay open for 30 seconds")
        print("  WHAT TO DO:")
        print("  1. Find a 'View Results' or auction link/button")
        print("  2. Right-click → Inspect to see its HTML")
        print("  3. Note the CSS class or link pattern")
        print("  4. Copy one auction URL to test Level 2")
        time.sleep(30)

        # LEVEL 2: Try to navigate to an auction page
        print("\n[LEVEL 2] Individual Auction Page")
        print("-" * 60)

        # Try to find and click first auction link
        first_auction_url = None

        for link in view_results_links + view_auction_links:
            href = link.get('href')
            if href:
                first_auction_url = 'https://www.christies.com' + href if href.startswith('/') else href
                break

        if first_auction_url:
            print(f"Navigating to: {first_auction_url}")
            driver.get(first_auction_url)
            time.sleep(5)

            # Scroll
            driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(2)

            # Save HTML
            with open('data/christies_level2_auction_page.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("✓ Saved: data/christies_level2_auction_page.html")

            # Parse lots
            soup = BeautifulSoup(driver.page_source, 'lxml')

            print("\nLooking for lot items on auction page:")

            lot_divs = soup.find_all('div', class_=lambda x: x and 'lot' in x.lower())
            print(f"  - <div> with 'lot' in class: {len(lot_divs)}")

            lot_articles = soup.find_all('article', class_=lambda x: x and 'lot' in x.lower())
            print(f"  - <article> with 'lot' in class: {len(lot_articles)}")

            # Look for price indicators
            price_elements = soup.find_all(['span', 'div'], string=lambda x: x and '$' in str(x))
            print(f"  - Elements with '$' in text: {len(price_elements)}")

            print("\n⏸ Browser will stay open for 30 seconds")
            print("  WHAT TO DO:")
            print("  1. Find a lot/painting item on the page")
            print("  2. Right-click → Inspect")
            print("  3. Note the CSS classes for:")
            print("     - Artist name")
            print("     - Artwork title")
            print("     - Sale price")
            print("     - Lot number")
            time.sleep(30)

        else:
            print("⚠ Could not find auction link to navigate to Level 2")
            print("  Please manually copy an auction URL and test it")

        print("\n✓ Christie's multi-level test complete")

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
    finally:
        driver.quit()


def test_sothebys_multilevel():
    """Test Sotheby's multi-level scraping with login"""
    print("\n" + "="*60)
    print("TESTING SOTHEBY'S MULTI-LEVEL SCRAPING (WITH LOGIN)")
    print("="*60)

    email = os.getenv('SOTHEBYS_EMAIL')
    password = os.getenv('SOTHEBYS_PASSWORD')

    if not email or not password:
        print("\n⚠ ERROR: Sotheby's credentials not found in .env")
        print("  Add SOTHEBYS_EMAIL and SOTHEBYS_PASSWORD to .env file")
        return

    driver = setup_driver(headless=False)

    try:
        # LEVEL 0: Login
        print("\n[LEVEL 0] Login to Sotheby's")
        print("-" * 60)

        driver.get("https://www.sothebys.com/en/login")
        time.sleep(5)

        # Save login page HTML
        with open('data/sothebys_level0_login_page.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("✓ Saved: data/sothebys_level0_login_page.html")

        print("\n⏸ Login page opened - will stay open for 20 seconds")
        print("  WHAT TO DO:")
        print("  1. Inspect email field → Note the ID or CSS selector")
        print("  2. Inspect password field → Note the ID or CSS selector")
        print("  3. Inspect submit button → Note the selector")
        print("  4. OR manually log in now for testing")
        time.sleep(20)

        # Try to login automatically
        print("\nAttempting automatic login...")

        email_selectors = [
            (By.ID, "email"),
            (By.NAME, "email"),
            (By.CSS_SELECTOR, "input[type='email']"),
        ]

        email_field = None
        for by, selector in email_selectors:
            try:
                email_field = driver.find_element(by, selector)
                print(f"  ✓ Found email field: {by}='{selector}'")
                break
            except:
                continue

        if email_field:
            email_field.send_keys(email)
            time.sleep(1)

            password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_field.send_keys(password)
            time.sleep(1)

            login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_btn.click()

            print("  Waiting for login...")
            time.sleep(7)

            if "login" not in driver.current_url.lower():
                print("  ✓ Login successful!")
            else:
                print("  ⚠ Login may have failed - please login manually")
                time.sleep(10)
        else:
            print("  ⚠ Could not find email field - please login manually")
            time.sleep(15)

        # LEVEL 1: Main results page
        print("\n[LEVEL 1] Main Results Page")
        print("-" * 60)

        url = "https://www.sothebys.com/en/results?from=11%2F1%2F2025&to=11%2F30%2F2025"
        print(f"URL: {url}")
        driver.get(url)
        time.sleep(5)

        # Scroll
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)

        # Save HTML
        with open('data/sothebys_level1_results_page.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("✓ Saved: data/sothebys_level1_results_page.html")

        # Parse
        soup = BeautifulSoup(driver.page_source, 'lxml')

        print("\nLooking for 'View Results' links:")

        view_links = soup.find_all('a', string=lambda x: x and 'view' in x.lower())
        print(f"  - Links with 'view' in text: {len(view_links)}")

        for link in view_links[:5]:
            print(f"    • {link.get_text(strip=True)[:50]}")

        print("\n⏸ Browser will stay open for 30 seconds")
        print("  WHAT TO DO:")
        print("  1. Find 'View Results' or 'View Auction' buttons")
        print("  2. Right-click → Inspect")
        print("  3. Note the link href pattern")
        time.sleep(30)

        # LEVEL 2: Try to navigate to auction page
        print("\n[LEVEL 2] Individual Auction Page")
        print("-" * 60)

        first_auction_url = None
        for link in view_links:
            href = link.get('href')
            if href and 'auction' in href.lower():
                first_auction_url = 'https://www.sothebys.com' + href if href.startswith('/') else href
                break

        if first_auction_url:
            print(f"Navigating to: {first_auction_url}")
            driver.get(first_auction_url)
            time.sleep(5)

            # Save HTML
            with open('data/sothebys_level2_auction_page.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("✓ Saved: data/sothebys_level2_auction_page.html")

            # Parse lots
            soup = BeautifulSoup(driver.page_source, 'lxml')

            print("\nLooking for lot items:")

            lot_items = soup.find_all(['div', 'article'], class_=lambda x: x and 'lot' in x.lower())
            print(f"  - Lot items found: {len(lot_items)}")

            # Check for prices (should be visible after login)
            price_items = soup.find_all(string=lambda x: x and '$' in str(x))
            print(f"  - Items with '$' (prices): {len(price_items)}")

            print("\n⏸ Browser will stay open for 30 seconds")
            print("  WHAT TO DO:")
            print("  1. Find lot items with artist, title, price")
            print("  2. Inspect each element")
            print("  3. Note the CSS selectors")
            time.sleep(30)

        else:
            print("⚠ Could not find auction link")

        print("\n✓ Sotheby's multi-level test complete")

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
    finally:
        driver.quit()


def main():
    """Run multi-level tests"""
    print("\n" + "="*60)
    print("MULTI-LEVEL AUCTION SCRAPER TEST")
    print("="*60)

    os.makedirs('data', exist_ok=True)

    print("\nThis test navigates through multiple levels:")
    print("  Christie's: Results → Auction → Lots")
    print("  Sotheby's: Login → Results → Auction → Lots")
    print("\nAt each level, the browser stays open for inspection.")

    choice = input("\nChoose test:\n  1. Christie's multi-level\n  2. Sotheby's multi-level\n  3. Both\n\nEnter choice [1-3]: ").strip()

    if choice == '1':
        test_christies_multilevel()
    elif choice == '2':
        test_sothebys_multilevel()
    elif choice == '3':
        test_christies_multilevel()
        test_sothebys_multilevel()
    else:
        print("\nInvalid choice")

    print("\n" + "="*60)
    print("FILES CREATED:")
    print("="*60)
    print("\nCheck data/ folder for HTML files:")
    import glob
    for html_file in sorted(glob.glob('data/*.html')):
        size = os.path.getsize(html_file) / 1024
        print(f"  • {html_file} ({size:.1f} KB)")

    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("\n1. Open HTML files in browser to inspect structure")
    print("2. Update selectors in scrapers/christies_scraper.py:")
    print("   - get_auction_links() - find 'View Results' links")
    print("   - extract_sale_data() - find artist, title, price")
    print("\n3. Update selectors in scrapers/sothebys_scraper.py:")
    print("   - login() - find email, password, submit")
    print("   - get_auction_links() - find 'View Results' links")
    print("   - extract_sale_data() - find artist, title, price")
    print("\n4. Test updated scrapers:")
    print("   python scrapers/christies_scraper.py")
    print("   python scrapers/sothebys_scraper.py")
    print("\n5. Run full pipeline:")
    print("   python main.py\n")


if __name__ == "__main__":
    main()
