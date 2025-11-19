# Art Auction Ticker - AI-Powered Scraper

An automated scraper that collects notable art auction sales from Christie's and Sotheby's, then uses AI to select the 20 most interesting sales from each auction house for display on a luxury fashion website.

## Features

- **Automated scraping** of Christie's and Sotheby's monthly auction results
- **AI-powered selection** using OpenAI to identify the most notable sales (mix of high prices and famous artists)
- **Selenium-based** web scraping for dynamic content
- **Monthly scheduling** capability
- **JSON output** ready for frontend consumption

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
OPENAI_API_KEY=sk-your-openai-api-key
SOTHEBYS_EMAIL=your-email@example.com
SOTHEBYS_PASSWORD=your-password
```

**Note:** Sotheby's requires login to view sale prices. You'll need a free account.

### 3. Run the Scraper

```bash
python main.py
```

This will:
1. Scrape Christie's results for the previous month
2. Scrape Sotheby's results for the previous month
3. Use AI to select top 20 sales from each auction house
4. Save results to `data/auction_ticker_YYYY_MM.json`

## Project Structure

```
art-auction-ticker/
├── scrapers/
│   ├── christies_scraper.py   # Christie's scraper
│   └── sothebys_scraper.py    # Sotheby's scraper (with login)
├── ai/
│   └── selector.py            # AI-powered sale selection
├── data/                      # Output directory for JSON files
├── main.py                    # Main orchestration script
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
└── README.md
```

## How It Works

### Christie's Scraping
- URL pattern: `https://www.christies.com/en/results?month=MM&year=YYYY`
- No authentication required
- Scrapes all sales from specified month

### Sotheby's Scraping
- URL pattern: `https://www.sothebys.com/en/results?from=MM%2F1%2FYYYY&to=MM%2F30%2FYYYY`
- **Requires login** to view prices
- Scrapes individual auction pages

### AI Selection
- Uses OpenAI GPT-4 to analyze all scraped sales
- Selects top 20 based on:
  - High sale prices
  - Famous/significant artists
  - Art historical importance
- Falls back to price-based sorting if AI fails

## Output Format

The final JSON output (`data/auction_ticker_YYYY_MM.json`) looks like:

```json
{
  "month": "2025-11",
  "generated_at": "2025-11-30T12:00:00",
  "total_sales": 40,
  "christies": [
    {
      "artist": "Pablo Picasso",
      "title": "Femme au béret rouge",
      "price": "$15,400,000",
      "price_realized": 15400000,
      "currency": "USD",
      "auction_house": "Christie's",
      "sale_date": "2025-11-15",
      "url": "https://www.christies.com/..."
    }
  ],
  "sothebys": [...]
}
```

## Monthly Automation

### Option 1: Cron Job (Linux/Mac)

Add to crontab to run on the last day of each month:
```bash
0 0 28-31 * * [ "$(date -d tomorrow +\%d)" = "01" ] && cd /path/to/art-auction-ticker && python main.py
```

### Option 2: GitHub Actions

Create `.github/workflows/monthly-scrape.yml`:
```yaml
name: Monthly Art Auction Scrape
on:
  schedule:
    - cron: '0 0 28-31 * *'  # Last day of month
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
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          SOTHEBYS_EMAIL: ${{ secrets.SOTHEBYS_EMAIL }}
          SOTHEBYS_PASSWORD: ${{ secrets.SOTHEBYS_PASSWORD }}
```

## Testing

Test individual scrapers:

```bash
# Test Christie's scraper
python scrapers/christies_scraper.py

# Test Sotheby's scraper (requires .env)
python scrapers/sothebys_scraper.py

# Test AI selector
python ai/selector.py
```

## Troubleshooting

### "Sotheby's credentials not found"
- Make sure `.env` file exists with `SOTHEBYS_EMAIL` and `SOTHEBYS_PASSWORD`

### "OPENAI_API_KEY not found"
- Add your OpenAI API key to `.env`

### Scraper returns no results
- The HTML selectors may need updating (Christie's/Sotheby's change their website)
- Run with `headless=False` to see what's happening:
  ```python
  scraper = ChristiesScraper(headless=False)
  ```

### Login fails for Sotheby's
- Verify credentials are correct
- Check if Sotheby's has CAPTCHA (may need manual intervention)
- Try running with `headless=False` to debug

## Next Steps

1. **Frontend Integration**: Build React ticker component to display this data
2. **Improve Selectors**: Update HTML selectors after inspecting actual website structure
3. **Error Handling**: Add retry logic and better error recovery
4. **Caching**: Store cookies for faster Sotheby's authentication
5. **Monitoring**: Add alerts for scraping failures

## License

MIT
