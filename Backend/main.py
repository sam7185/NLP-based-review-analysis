import sys
from scrap import scrape_hotel_reviews, extract_pagename
from analyze import run_pipeline

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <HOTEL_URL>")
        return

    hotel_url = sys.argv[1]
    print(f"Hotel URL provided: {hotel_url}")

    # Step 1: Scrape
    print("\n[Step 1] Scraping hotel reviews...")
    scrape_hotel_reviews(hotel_url, max_pages=2)  # adjust pages if needed

    # Determine hotel file name
    pagename = extract_pagename(hotel_url).replace('-', ' ').title().replace(' ', '_')

    print(f"\n[Step 2] Analyzing hotel reviews from file: {pagename}.json")
    run_pipeline(pagename)

if __name__ == "__main__":
    main()
