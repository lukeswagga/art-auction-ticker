# Testing Guide - Art Auction Scraper

This guide walks you through testing the scraping system step-by-step.

## Step 1: Install Dependencies

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

## Step 2: Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

Add the following to `.env`:
```
# Required for AI selection
OPENAI_API_KEY=sk-your-actual-openai-key-here

# Required for Sotheby's price data
SOTHEBYS_EMAIL=your-email@example.com
SOTHEBYS_PASSWORD=your-password

# Optional: day of month to run scraper
SCRAPE_DAY_OF_MONTH=30
```

**Note:** You need a Sotheby's account to view prices. Create one at https://www.sothebys.com/en/register (it's free).

## Step 3: Run Test Script (Recommended First Step)

Use the test script to see the websites and inspect HTML:

```bash
python test_scraper.py
```

This will:
1. Open Christie's in a visible browser
2. Open Sotheby's and attempt login
3. Save HTML to files for inspection
4. Show you what selectors to look for

## Step 4: Test Individual Scrapers

### Test Christie's Scraper

```bash
# With visible browser (see what's happening)
python scrapers/christies_scraper.py
```

This will:
- Open Chrome browser
- Navigate to Christie's November 2025 results
- Scroll through the page
- Attempt to scrape data
- Save to `data/christies_november_2025.json`

**What to look for:**
- Does the page load correctly?
- Are there auction results visible?
- Check console output for number of items found

### Test Sotheby's Scraper

```bash
# Make sure .env has your credentials first!
python scrapers/sothebys_scraper.py
```

This will:
- Open Chrome browser
- Go to Sotheby's login page
- Attempt to log in with your credentials
- Navigate to November 2025 results
- Scrape auction data
- Save to `data/sothebys_november_2025.json`

**What to look for:**
- Does login succeed?
- Are prices visible after login?
- How many auctions are found?

## Step 5: Inspect and Update HTML Selectors

The scrapers won't work perfectly at first because the HTML selectors are placeholders. You need to update them.

### How to Find Correct Selectors

1. **Run test script with browser visible** (headless=False)
2. **While browser is open, right-click on elements and select "Inspect"**
3. **Find the CSS classes/IDs for:**
   - Artist name
   - Artwork title
   - Sale price
   - Lot number
   - Links to detail pages

### Example: Updating Christie's Selectors

In `scrapers/christies_scraper.py`, find the `extract_sale_data()` method and update:

```python
# BEFORE (placeholder)
artist_elem = item_element.find(['h2', 'h3', 'div'], class_=lambda x: x and 'artist' in x.lower())

# AFTER (with real selector from inspection)
artist_elem = item_element.find('h2', class_='chr-lot-detail__artist-name')
```

Do this for all data fields (artist, title, price, etc.)

## Step 6: Test AI Selection

Once you have some scraped data:

```bash
python ai/selector.py
```

This will:
- Load scraped Christie's data
- Use OpenAI to select top 20 notable sales
- Save selected results
- Print sample output

**Note:** This requires `OPENAI_API_KEY` in `.env` and costs ~$0.01-0.05 per run (GPT-4).

## Step 7: Run Full Pipeline

```bash
python main.py
```

This runs the complete workflow:
1. Scrape Christie's → `data/christies_raw_2025_11.json`
2. Scrape Sotheby's → `data/sothebys_raw_2025_11.json`
3. AI select Christie's → `data/christies_selected_2025_11.json`
4. AI select Sotheby's → `data/sothebys_selected_2025_11.json`
5. Combine → `data/auction_ticker_2025_11.json`

## Common Issues & Solutions

### Issue: "Chrome driver not found"
**Solution:** The script auto-downloads ChromeDriver. If it fails:
```bash
pip install --upgrade webdriver-manager
```

### Issue: "Sotheby's login failed"
**Solutions:**
- Verify credentials in `.env` are correct
- Check if Sotheby's has CAPTCHA (you may need to login manually first)
- Run with `headless=False` to see what's happening

### Issue: "No results found"
**Solutions:**
- HTML selectors need updating (see Step 5)
- Website structure may have changed
- Try a different month that definitely has results

### Issue: "OpenAI API error"
**Solutions:**
- Check API key is valid and has credits
- Verify key is correctly set in `.env`
- Try using `gpt-3.5-turbo` instead of `gpt-4` (cheaper) in `ai/selector.py`

### Issue: Scraper finds 0 items
**Solutions:**
- The CSS selectors are wrong - inspect HTML and update
- Page might need more time to load - increase `time.sleep()` values
- JavaScript might not be fully loaded - add explicit waits

## Debugging Tips

### 1. Run with Visible Browser
Change `headless=False` in the scraper initialization:
```python
scraper = ChristiesScraper(headless=False)  # See what's happening
```

### 2. Save Page Source
Add this to see the actual HTML:
```python
with open('page_source.html', 'w') as f:
    f.write(self.driver.page_source)
```

### 3. Use Python Debugger
Add breakpoint to pause and inspect:
```python
import pdb; pdb.set_trace()
```

### 4. Check Data Files
After running, check `data/` folder:
```bash
ls -lh data/
cat data/christies_raw_2025_11.json | head -50
```

## Expected Output

After successful run of `main.py`, you should see:

```
============================================================
Art Auction Ticker - Scraping 2025-11
============================================================

[1/5] Scraping Christie's...
URL: https://www.christies.com/en/results?month=11&year=2025
Found 150 auction sales from Christie's
Saved 150 sales to data/christies_raw_2025_11.json

[2/5] Scraping Sotheby's...
Login successful!
Found 25 auctions to scrape
Found 200 total sales from Sotheby's
Saved 200 sales to data/sothebys_raw_2025_11.json

[3/5] AI selecting top 20 Christie's sales...
AI selected 20 sales
Saved 20 selected sales to data/christies_selected_2025_11.json

[4/5] AI selecting top 20 Sotheby's sales...
AI selected 20 sales
Saved 20 selected sales to data/sothebys_selected_2025_11.json

[5/5] Combining final results...
✓ Complete! Final data saved to data/auction_ticker_2025_11.json
  - Christie's: 20 sales
  - Sotheby's: 20 sales
  - Total: 40 sales
```

## Next Steps After Testing

Once scrapers work correctly:
1. Test with different months
2. Set up monthly automation (cron or GitHub Actions)
3. Build frontend ticker component
4. Deploy to production

## Need Help?

If you get stuck:
1. Run `test_scraper.py` to inspect HTML
2. Save screenshots of errors
3. Check the HTML structure has the expected elements
4. Update selectors based on what you find
