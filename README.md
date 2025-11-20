# Art Auction Ticker - Automated Christie's Scraper

**Fully automated** scraper that collects the top 20 most expensive paintings from Christie's each month. No manual work, no API keys, completely free to run!

## 🎯 What It Does

1. **Scrapes Christie's** - Goes through all art/painting auctions for a given month
2. **Finds prices** - Intelligently extracts sale prices using pattern matching
3. **Sorts by price** - Automatically ranks all paintings by price (highest first)
4. **Selects top 20** - Returns the 20 most expensive paintings
5. **Saves to JSON** - Ready to display on your website

## ⚡ Key Features

- ✅ **100% Automated** - No manual selector updates needed
- ✅ **Intelligent scraping** - Adapts to HTML changes automatically
- ✅ **FREE** - No API costs, no subscriptions
- ✅ **Self-contained** - Only needs Chrome/Chromium installed
- ✅ **Monthly ready** - Set it and forget it

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Scraper

```bash
python main.py
```

That's it! It will scrape the previous month's data automatically.

### 3. Check the Output

Results saved to: `data/auction_ticker_YYYY_MM.json`

```json
{
  "month": "2025-11",
  "generated_at": "2025-11-30T10:00:00",
  "total_scraped": 456,
  "total_with_prices": 320,
  "top_sales_count": 20,
  "selection_method": "Price-based (highest to lowest)",
  "sales": [
    {
      "artist": "Pablo Picasso",
      "title": "Femme au béret rouge",
      "price": "$15,400,000",
      "price_realized": 15400000,
      "currency": "USD",
      "auction_house": "Christie's",
      "url": "https://www.christies.com/..."
    },
    ...
  ]
}
```

## 🧠 How It Works (Intelligent Scraping)

The scraper doesn't rely on fixed CSS selectors. Instead, it uses **multiple strategies**:

### Finding Auction Links
1. Searches for "View Results" / "View Auction" text
2. Looks for URLs containing "auction" or "sale"
3. Detects common container patterns (cards, sections)

### Extracting Lot Data
- **Artist**: Tries 4 class patterns + heading fallbacks
- **Title**: Tries 3 class patterns + heading fallbacks
- **Price**: Searches ALL text for currency symbols ($, £, €)
- **Auto-detection**: Finds repeating HTML structures

### Why This Works
Even if Christie's changes their CSS classes, the scraper will:
- Still find currency symbols in the page
- Still detect repeating patterns (lot listings)
- Still match semantic keywords like "artist", "title", "price"

## 📅 Monthly Automation

### Option 1: Cron Job (Mac/Linux)

Run on the last day of each month:

```bash
# Edit crontab
crontab -e

# Add this line (runs at midnight on day 28-31 if next day is the 1st)
0 0 28-31 * * [ "$(date -d tomorrow +\%d)" = "01" ] && cd /path/to/art-auction-ticker && python3 main.py
```

### Option 2: GitHub Actions

Create `.github/workflows/monthly-scrape.yml`:

```yaml
name: Monthly Christie's Scrape
on:
  schedule:
    - cron: '0 0 28 * *'  # 28th of each month
jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python main.py
      - uses: actions/upload-artifact@v3
        with:
          name: auction-data
          path: data/*.json
```

### Option 3: Manual

Just run whenever you want:

```bash
# Scrape November 2025
python main.py  # Defaults to previous month

# Or specify a month
python -c "from main import scrape_and_select; scrape_and_select(2025, 11)"
```

## 🎨 Frontend Display

The JSON output is ready to use in a ticker component:

```javascript
// Example: React ticker component
fetch('/data/auction_ticker_2025_11.json')
  .then(res => res.json())
  .then(data => {
    data.sales.forEach(sale => {
      console.log(`${sale.artist} | ${sale.title} | ${sale.price}`)
    })
  })
```

## 🔧 Customization

### Change Number of Results

```python
# Get top 40 instead of 20
scrape_and_select(top_n=40)
```

### Scrape Different Months

```python
# Scrape January 2024
scrape_and_select(year=2024, month=1)
```

### Run in Background

```python
# Use headless=True (default) for no browser window
# Use headless=False to see what it's doing
from scrapers.christies_scraper import ChristiesScraper

scraper = ChristiesScraper(headless=False)  # Show browser
```

## 📁 Project Structure

```
art-auction-ticker/
├── scrapers/
│   └── christies_scraper.py   # Intelligent Christie's scraper
├── data/                       # Output directory
├── main.py                     # Main script
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🐛 Troubleshooting

### "Chrome binary not found"
Install Chrome or Chromium:
```bash
# Mac
brew install --cask google-chrome

# Ubuntu/Debian
sudo apt-get install chromium-browser
```

### No results found
- Check the URL is correct for the month
- Christie's may have changed their structure (scraper should adapt, but check logs)
- Run with `headless=False` to see the browser

### Prices not extracted
- Scraper looks for $, £, € symbols
- If Christie's uses different currency format, update `parse_price()` in `christies_scraper.py`

## 🎯 Next Steps

1. **Test it**: Run `python main.py` to scrape previous month
2. **Check output**: Look at `data/auction_ticker_*.json`
3. **Build frontend**: Use the JSON to display on your website
4. **Automate**: Set up monthly cron job or GitHub Actions
5. **Customize**: Adjust number of results, filters, etc.

## 📝 Notes

- **No login required** - Christie's results are public
- **Respects rate limits** - 2-second delay between auction pages
- **Saves progress** - Raw data saved in case you need it
- **Christie's only** - Sotheby's removed due to CAPTCHA issues

## License

MIT
