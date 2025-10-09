"""
Quick test script for scraping helpers.
Usage (from project root, with venv activated):
  python scripts\test_scrape.py "https://www.booking.com/hotel/in/example.html"

It will:
 - fetch the booking review page (reviewlist endpoint)
 - save the raw HTML to scripts/debug_review_page.html
 - run parse_reviews and print counts and first example
"""
import sys
import os

# Ensure Backend directory is on sys.path so we can import project modules like `scrap`.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, 'Backend')
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from scrap import extract_pagename, get_review_page_html, parse_reviews, get_hotel_metadata


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts\\test_scrape.py <hotel_page_url>")
        sys.exit(1)

    hotel_url = sys.argv[1]
    pagename = extract_pagename(hotel_url)
    if not pagename:
        print("Failed to extract pagename from URL:", hotel_url)
        sys.exit(2)

    print("Pagename:", pagename)

    try:
        html = get_review_page_html(pagename, rows=10, offset=0)
        os.makedirs('scripts', exist_ok=True)
        out_path = 'scripts/debug_review_page.html'
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Saved review-list HTML to {out_path} (open in browser to inspect)")

        reviews = parse_reviews(html)
        print(f"Parsed {len(reviews)} reviews from the review page")
        if reviews:
            print("First review (truncated):")
            import json
            print(json.dumps(reviews[0], indent=2)[:1000])

        print("Also fetching hotel metadata page to verify selectors...")
        meta = get_hotel_metadata(hotel_url)
        import json
        print(json.dumps(meta, indent=2))

    except Exception as e:
        print("Error during scraping test:", e)
        raise


if __name__ == '__main__':
    main()
