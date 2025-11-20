"""
Main orchestration script for art auction ticker scraping
Runs monthly to scrape Christie's, then selects top 20
(Sotheby's disabled due to CAPTCHA/login issues)
"""

import os
import json
from datetime import datetime, timedelta
from scrapers.christies_scraper import ChristiesScraper
# from scrapers.sothebys_scraper import SothebysScraper  # Disabled for now
from ai.selector import ArtSaleSelector


def get_previous_month() -> tuple:
    """Get year and month for previous month"""
    today = datetime.now()
    first_of_month = today.replace(day=1)
    last_month = first_of_month - timedelta(days=1)
    return last_month.year, last_month.month


def scrape_and_select(year: int = None, month: int = None):
    """
    Simplified pipeline (Christie's only):
    1. Scrape Christie's
    2. Use AI to select top 40 notable pieces
    3. Save final results
    """

    # Use previous month if not specified
    if year is None or month is None:
        year, month = get_previous_month()

    print(f"=" * 60)
    print(f"Art Auction Ticker - Christie's Only - {year}-{month:02d}")
    print(f"=" * 60)

    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)

    # Step 1: Scrape Christie's
    print("\n[1/3] Scraping Christie's...")
    christies_scraper = ChristiesScraper(headless=True)
    christies_sales = christies_scraper.scrape_month(year, month)
    christies_scraper.save_to_json(christies_sales, f'data/christies_raw_{year}_{month:02d}.json')

    # Step 2: AI Selection for Christie's (select 40 instead of 20)
    print("\n[2/3] AI selecting top 40 Christie's sales...")
    selector = ArtSaleSelector()
    christies_selected = selector.select_notable_sales(christies_sales, "Christie's", 40)
    selector.save_selected(christies_selected, f'data/christies_selected_{year}_{month:02d}.json')

    # Step 3: Save final results
    print("\n[3/3] Saving final results...")
    combined = {
        'month': f"{year}-{month:02d}",
        'generated_at': datetime.now().isoformat(),
        'total_sales': len(christies_selected),
        'christies': christies_selected,
        'note': 'Sotheby\'s disabled due to login/CAPTCHA issues'
    }

    output_file = f'data/auction_ticker_{year}_{month:02d}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Complete! Final data saved to {output_file}")
    print(f"  - Christie's: {len(christies_selected)} sales")
    print(f"  - Total: {combined['total_sales']} sales")

    return combined


if __name__ == "__main__":
    # Run for previous month
    results = scrape_and_select()

    # Print sample
    print("\n" + "=" * 60)
    print("SAMPLE RESULTS")
    print("=" * 60)

    print("\nChristie's Top Sales:")
    for sale in results['christies'][:5]:
        print(f"  • {sale['artist']}: {sale['title']} - {sale['price']}")
