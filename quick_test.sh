#!/bin/bash
# Quick test script for art auction scraper

echo "=================================="
echo "Art Auction Scraper - Quick Test"
echo "=================================="
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Check for .env
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠ WARNING: .env file not found!"
    echo "Please create .env file with your credentials:"
    echo "  cp .env.example .env"
    echo "  nano .env  # Add your API keys"
    echo ""
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run test
echo ""
echo "Running test scraper..."
echo ""
python test_scraper.py

echo ""
echo "=================================="
echo "Test complete!"
echo "=================================="
echo ""
echo "Check the data/ folder for HTML files:"
ls -lh data/ 2>/dev/null || echo "No data files yet"

echo ""
echo "Next: Read TESTING.md for detailed instructions"
