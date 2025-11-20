"""
Automatically discover and test Christie's selectors
This script will inspect the actual website and find working patterns
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import json

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

print("="*60)
print("AUTO-DISCOVERING CHRISTIE'S SELECTORS")
print("="*60)

driver = setup_driver()

try:
    # Test URL with filters
    url = "https://www.christies.com/en/results?month=11&year=2025&filters=|category_17|category_7|category_22|category_5|"
    print(f"\n[1] Loading: {url}")
    driver.get(url)
    time.sleep(5)

    # Scroll to load content
    driver.execute_script("window.scrollTo(0, 1000);")
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, 'lxml')

    # Save HTML for debugging
    with open('data/christies_auto_inspect.html', 'w') as f:
        f.write(driver.page_source)
    print("   Saved page HTML to data/christies_auto_inspect.html")

    print("\n[2] Searching for auction links...")

    # Find all links
    all_links = soup.find_all('a', href=True)

    # Filter links that look like auction pages
    auction_links = []
    for link in all_links:
        href = link.get('href', '')
        text = link.get_text(strip=True).lower()

        # Look for auction-related URLs
        if 'auction' in href or 'sale' in href:
            if href.startswith('/'):
                full_url = 'https://www.christies.com' + href
            else:
                full_url = href

            if full_url not in auction_links and 'christies.com' in full_url:
                auction_links.append(full_url)
                print(f"   Found: {full_url[:80]}...")

    print(f"\n   Total auction links found: {len(auction_links)}")

    if len(auction_links) == 0:
        print("\n   ⚠ No auction links found. Trying broader search...")

        # Try finding any links with sale/auction in text
        for link in all_links:
            text = link.get_text(strip=True).lower()
            if any(word in text for word in ['view', 'result', 'auction', 'sale']):
                href = link.get('href', '')
                if href and href.startswith('/'):
                    print(f"   Potential link: {text[:50]} -> {href[:50]}")

    # If we found links, test the first one
    if auction_links:
        test_url = auction_links[0]
        print(f"\n[3] Testing first auction: {test_url}")
        driver.get(test_url)
        time.sleep(5)

        # Scroll
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'lxml')

        # Save auction page HTML
        with open('data/christies_auction_page.html', 'w') as f:
            f.write(driver.page_source)
        print("   Saved auction page to data/christies_auction_page.html")

        print("\n[4] Looking for lot items...")

        # Search for elements with common lot-related classes
        lot_patterns = ['lot', 'item', 'artwork', 'object', 'product']

        for pattern in lot_patterns:
            divs = soup.find_all('div', class_=lambda x: x and pattern in str(x).lower())
            articles = soup.find_all('article', class_=lambda x: x and pattern in str(x).lower())

            total = len(divs) + len(articles)
            if total > 0:
                print(f"   Found {total} elements with '{pattern}' in class")

        # Look for price indicators
        price_elements = soup.find_all(string=lambda x: x and any(c in str(x) for c in ['$', '£', '€']))
        print(f"   Found {len(price_elements)} elements with currency symbols")

        # Try to find patterns
        print("\n[5] Analyzing structure...")

        # Find all divs with classes containing 'chr' (Christie's prefix)
        chr_elements = soup.find_all(['div', 'article', 'section'], class_=lambda x: x and 'chr-' in str(x).lower())

        if chr_elements:
            print(f"   Found {len(chr_elements)} elements with 'chr-' prefix")

            # Show unique classes
            classes = set()
            for elem in chr_elements[:20]:
                elem_classes = elem.get('class', [])
                for cls in elem_classes:
                    if 'chr-' in cls.lower():
                        classes.add(cls)

            print("\n   Christie's-specific classes found:")
            for cls in sorted(classes)[:15]:
                print(f"      - {cls}")

        print("\n[6] Extracting sample data...")

        # Try to extract any text that looks like artist names
        # Common patterns: All caps, or Name with comma
        potential_artists = soup.find_all(['h1', 'h2', 'h3', 'h4'])

        if potential_artists:
            print("\n   Potential artist/title fields:")
            for elem in potential_artists[:10]:
                text = elem.get_text(strip=True)
                classes = ' '.join(elem.get('class', []))
                if text and len(text) < 100:
                    print(f"      {text[:60]} | class='{classes[:40]}'")

        print("\n✓ Discovery complete!")
        print("\nCheck data/ folder for HTML files to manually inspect if needed")
        print("I'll now update the scraper with discovered patterns...")

    else:
        print("\n⚠ Could not find auction links automatically")
        print("The page structure may be different than expected")

finally:
    driver.quit()

print("\n" + "="*60)
