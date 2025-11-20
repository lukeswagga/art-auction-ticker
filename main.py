"""
Main orchestration script for art auction ticker scraping
Runs monthly to scrape Christie's and get top 20 most expensive paintings
No AI needed - just sorts by price!
"""

import os
import json
from datetime import datetime, timedelta
from scrapers.christies_scraper import ChristiesScraper


def get_previous_month() -> tuple:
    """Get year and month for previous month"""
    today = datetime.now()
    first_of_month = today.replace(day=1)
    last_month = first_of_month - timedelta(days=1)
    return last_month.year, last_month.month


def scrape_and_select(year: int = None, month: int = None, top_n: int = 20):
    """
    Simple automated pipeline:
    1. Scrape all Christie's auctions for the month
    2. Sort by price (highest first)
    3. Take top 20 most expensive
    4. Save results

    No AI, no manual work - fully automated!
    """

    # Use previous month if not specified
    if year is None or month is None:
        year, month = get_previous_month()

    print(f"=" * 60)
    print(f"Christie's Top {top_n} Most Expensive - {year}-{month:02d}")
    print(f"=" * 60)

    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)

    # Step 1: Scrape ALL Christie's sales for the month
    print(f"\n[1/3] Scraping Christie's auctions for {year}-{month:02d}...")
    christies_scraper = ChristiesScraper(headless=True)
    all_sales = christies_scraper.scrape_month(year, month)

    # Save raw data
    christies_scraper.save_to_json(all_sales, f'data/christies_raw_{year}_{month:02d}.json')
    print(f"  Scraped {len(all_sales)} total paintings")

    # Step 2: Sort by price and take top N
    print(f"\n[2/3] Selecting top {top_n} by price...")

    # Filter out sales without prices
    sales_with_prices = [s for s in all_sales if s.get('price_realized') and s.get('price_realized') > 0]
    print(f"  Found {len(sales_with_prices)} sales with valid prices")

    # Sort by price (highest first)
    sorted_sales = sorted(sales_with_prices, key=lambda x: x['price_realized'], reverse=True)

    # Take top N
    top_sales = sorted_sales[:top_n]

    # Step 3: Save final results
    print(f"\n[3/3] Saving top {len(top_sales)} results...")

    result = {
        'month': f"{year}-{month:02d}",
        'generated_at': datetime.now().isoformat(),
        'total_scraped': len(all_sales),
        'total_with_prices': len(sales_with_prices),
        'top_sales_count': len(top_sales),
        'selection_method': 'Price-based (highest to lowest)',
        'sales': top_sales
    }

    output_file = f'data/auction_ticker_{year}_{month:02d}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Complete! Top {len(top_sales)} sales saved to {output_file}")
    print(f"  Total scraped: {len(all_sales)} paintings")
    print(f"  With prices: {len(sales_with_prices)} paintings")
    print(f"  Selected: {len(top_sales)} most expensive")

    if top_sales:
        print(f"\n  Price range:")
        print(f"    Highest: {top_sales[0]['price']}")
        print(f"    Lowest:  {top_sales[-1]['price']}")

    return result


if __name__ == "__main__":
    # Run for previous month, get top 20
    results = scrape_and_select(top_n=20)

    # Print sample
    print("\n" + "=" * 60)
    print("TOP 5 MOST EXPENSIVE")
    print("=" * 60)

    for i, sale in enumerate(results['sales'][:5], 1):
        artist = sale.get('artist', 'Unknown')
        title = sale.get('title', 'Untitled')
        price = sale.get('price', 'N/A')
        print(f"  {i}. {artist}: {title}")
        print(f"      {price}")
