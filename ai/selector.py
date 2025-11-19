"""
AI-Powered Selection of Notable Art Sales
Uses OpenAI API to select the 20 most notable sales from each auction house
Criteria: Mix of famous artists and high prices
"""

import os
from typing import List, Dict
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class ArtSaleSelector:
    def __init__(self):
        """Initialize OpenAI client"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.client = OpenAI(api_key=api_key)

    def select_notable_sales(self, sales: List[Dict], auction_house: str, limit: int = 20) -> List[Dict]:
        """
        Select the most notable sales using AI

        Args:
            sales: List of sale dictionaries
            auction_house: Name of auction house (Christie's or Sotheby's)
            limit: Number of sales to select (default 20)

        Returns:
            List of top `limit` most notable sales
        """
        print(f"\nSelecting top {limit} notable sales from {len(sales)} {auction_house} results...")

        if len(sales) <= limit:
            print(f"Only {len(sales)} sales found, returning all")
            return sales

        # Prepare data for AI analysis
        sales_summary = self.prepare_sales_for_analysis(sales)

        # Use OpenAI to select notable sales
        selected_indices = self.ai_select(sales_summary, auction_house, limit)

        # Return selected sales
        selected_sales = [sales[i] for i in selected_indices if i < len(sales)]

        print(f"Selected {len(selected_sales)} notable sales")
        return selected_sales

    def prepare_sales_for_analysis(self, sales: List[Dict]) -> str:
        """Prepare sales data into a format suitable for AI analysis"""
        summary_lines = []

        for i, sale in enumerate(sales):
            artist = sale.get('artist', 'Unknown Artist')
            title = sale.get('title', 'Untitled')
            price = sale.get('price_realized', 0)

            summary_lines.append(f"{i}. {artist} - {title} - ${price:,}")

        return "\n".join(summary_lines)

    def ai_select(self, sales_summary: str, auction_house: str, limit: int) -> List[int]:
        """
        Use OpenAI to select the most notable sales
        Returns list of indices of selected sales
        """
        prompt = f"""You are an art market expert analyzing recent auction results from {auction_house}.

Below is a list of art sales with index numbers. Each entry shows:
[index]. [Artist Name] - [Artwork Title] - [Sale Price]

Your task: Select the {limit} MOST NOTABLE sales based on:
1. High sale prices (works that sold for exceptional amounts)
2. Famous/historically significant artists (e.g., Picasso, Monet, Basquiat, Warhol, etc.)
3. Important or landmark artworks
4. Balance between ultra-high-value sales and culturally significant pieces

Return ONLY a JSON array of the {limit} index numbers you selected, like this:
[0, 5, 12, 23, ...]

SALES DATA:
{sales_summary[:15000]}

Remember: Return ONLY the JSON array of indices, nothing else."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",  # or "gpt-3.5-turbo" for cost savings
                messages=[
                    {"role": "system", "content": "You are an expert art market analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent selections
                max_tokens=500
            )

            # Parse response
            content = response.choices[0].message.content.strip()

            # Extract JSON array
            indices = json.loads(content)

            if not isinstance(indices, list):
                raise ValueError("AI did not return a list")

            # Validate indices
            indices = [int(i) for i in indices if isinstance(i, (int, float))][:limit]

            print(f"AI selected {len(indices)} sales")
            return indices

        except Exception as e:
            print(f"Error in AI selection: {str(e)}")
            print("Falling back to price-based selection")
            return self.fallback_select(sales_summary, limit)

    def fallback_select(self, sales_summary: str, limit: int) -> List[int]:
        """
        Fallback selection method (simple price-based sorting)
        Used if AI selection fails
        """
        # Parse sales and sort by price
        lines = sales_summary.split('\n')
        sales_with_prices = []

        for line in lines:
            try:
                index = int(line.split('.')[0])
                price_str = line.split('$')[1].replace(',', '')
                price = int(price_str)
                sales_with_prices.append((index, price))
            except:
                continue

        # Sort by price descending
        sales_with_prices.sort(key=lambda x: x[1], reverse=True)

        # Return top N indices
        return [idx for idx, _ in sales_with_prices[:limit]]

    def save_selected(self, sales: List[Dict], filename: str):
        """Save selected sales to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(sales, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(sales)} selected sales to {filename}")


if __name__ == "__main__":
    # Test the selector with sample data
    selector = ArtSaleSelector()

    # Load sample data (you'll need to run scrapers first)
    try:
        with open('data/christies_november_2025.json', 'r') as f:
            christies_sales = json.load(f)

        selected = selector.select_notable_sales(christies_sales, "Christie's", 20)
        selector.save_selected(selected, 'data/christies_selected.json')

        print("\nSelected sales:")
        for sale in selected[:5]:
            print(f"- {sale['artist']}: {sale['title']} - {sale['price']}")

    except FileNotFoundError:
        print("Sample data not found. Run scrapers first.")
