"""
Main orchestration script for art auction ticker scraping
Runs monthly to scrape Christie's and Sotheby's, then selects top 20 from each
"""

import os
import json
from datetime import datetime, timedelta
from scrapers.christies_scraper import ChristiesScraper
from scrapers.sothebys_scraper import SothebysScraper
from ai.selector import ArtSaleSelector


def get_previous_month() -> tuple:
    """Get year and month for previous month"""
    today = datetime.now()
    first_of_month = today.replace(day=1)
    last_month = first_of_month - timedelta(days=1)
    return last_month.year, last_month.month


def scrape_and_select(year: int = None, month: int = None):
    """
    Main pipeline:
    1. Scrape Christie's
    2. Scrape Sotheby's
    3. Use AI to select top 20 from each
    4. Combine and save final results
    """

    # Use previous month if not specified
    if year is None or month is None:
        year, month = get_previous_month()

    print(f"=" * 60)
    print(f"Art Auction Ticker - Scraping {year}-{month:02d}")
    print(f"=" * 60)

    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)

    # Step 1: Scrape Christie's
    print("\n[1/5] Scraping Christie's...")
    christies_scraper = ChristiesScraper(headless=True)
    christies_sales = christies_scraper.scrape_month(year, month)
    christies_scraper.save_to_json(christies_sales, f'data/christies_raw_{year}_{month:02d}.json')

    # Step 2: Scrape Sotheby's
    print("\n[2/5] Scraping Sotheby's...")
    sothebys_scraper = SothebysScraper(headless=True)
    sothebys_sales = sothebys_scraper.scrape_month(year, month)
    sothebys_scraper.save_to_json(sothebys_sales, f'data/sothebys_raw_{year}_{month:02d}.json')

    # Step 3: AI Selection for Christie's
    print("\n[3/5] AI selecting top 20 Christie's sales...")
    selector = ArtSaleSelector()
    christies_selected = selector.select_notable_sales(christies_sales, "Christie's", 20)
    selector.save_selected(christies_selected, f'data/christies_selected_{year}_{month:02d}.json')

    # Step 4: AI Selection for Sotheby's
    print("\n[4/5] AI selecting top 20 Sotheby's sales...")
    sothebys_selected = selector.select_notable_sales(sothebys_sales, "Sotheby's", 20)
    selector.save_selected(sothebys_selected, f'data/sothebys_selected_{year}_{month:02d}.json')

    # Step 5: Combine results
    print("\n[5/5] Combining final results...")
    combined = {
        'month': f"{year}-{month:02d}",
        'generated_at': datetime.now().isoformat(),
        'total_sales': len(christies_selected) + len(sothebys_selected),
        'christies': christies_selected,
        'sothebys': sothebys_selected
    }

    output_file = f'data/auction_ticker_{year}_{month:02d}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Complete! Final data saved to {output_file}")
    print(f"  - Christie's: {len(christies_selected)} sales")
    print(f"  - Sotheby's: {len(sothebys_selected)} sales")
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
    for sale in results['christies'][:3]:
        print(f"  • {sale['artist']}: {sale['title']} - {sale['price']}")

    print("\nSotheby's Top Sales:")
    for sale in results['sothebys'][:3]:
        print(f"  • {sale['artist']}: {sale['title']} - {sale['price']}")
