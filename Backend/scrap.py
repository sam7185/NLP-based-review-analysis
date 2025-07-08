import os
import time
import requests
from parsel import Selector
import urllib.parse
import re
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

def extract_pagename(hotel_url):
    parsed = urllib.parse.urlparse(hotel_url)
    path = parsed.path
    match = re.search(r'/hotel/.+?/(.+?)\.html', path)
    return match.group(1) if match else None

def get_review_page_html(pagename, offset=0, rows=10, country_code='in', lang='en-us'):
    base = "https://www.booking.com/reviewlist.html"
    params = {
        'cc1': country_code,
        'lang': lang,
        'pagename': pagename,
        'rows': rows,
        'offset': offset,
        'type': 'total',
        'sort': 'f_recent_desc'
    }
    response = requests.get(base, params=params, headers=HEADERS)
    response.raise_for_status()
    return response.text

def parse_reviews(html):
    selector = Selector(text=html)
    reviews = []
    for review in selector.css('.review_list_new_item_block'):
        get = lambda sel: review.css(sel).get(default='').strip()
        get_all = lambda sel: ' '.join([t.strip() for t in review.css(sel).getall()]).strip()
        reviews.append({
            'score': get('.bui-review-score__badge::text'),
            'title': get('.c-review-block__title::text'),
            'date': get('.c-review-block__date::text'),
            'user_name': get('.bui-avatar-block__title::text'),
            'user_country': get('.bui-avatar-block__subtitle::text'),
            'text': get_all('.c-review__body ::text'),
            'lang': get('.c-review__body::attr(lang)')
        })
    return reviews

def get_hotel_metadata(hotel_url):
    response = requests.get(hotel_url, headers=HEADERS)
    response.raise_for_status()
    sel = Selector(text=response.text)

    title = sel.css('h2#hp_hotel_name::text').get(default='').strip()
    address = sel.css('.hp_address_subtitle::text').get(default='').strip()
    description = ' '.join(sel.css('#property_description_content ::text').getall()).strip()
    
    return {
        'url': hotel_url,
        'title': title,
        'address': address,
        'description': description
    }

def scrape_all_reviews(hotel_url, delay_seconds=2, max_pages=100):
    pagename = extract_pagename(hotel_url)
    if not pagename:
        raise ValueError("Could not extract pagename from URL")

    print(f"Scraping hotel: {pagename}")

    all_reviews = []
    for page in range(max_pages):
        offset = page * 10
        try:
            html = get_review_page_html(pagename, offset=offset)
        except Exception as e:
            print(f"Error fetching page {page+1}: {e}")
            break

        reviews = parse_reviews(html)
        if not reviews:
            print("No more reviews found, stopping.")
            break

        all_reviews.extend(reviews)
        print(f"Scraped {len(reviews)} reviews from page {page+1} (total so far: {len(all_reviews)})")

        time.sleep(delay_seconds)

    return all_reviews

def save_to_cache(hotel_url, data):
    os.makedirs('cache', exist_ok=True)
    pagename = extract_pagename(hotel_url)
    if not pagename:
        pagename = "unknown_hotel"
    filename = os.path.join('cache', f"{pagename}.json")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved data to {filename}")

if __name__ == '__main__':
    HOTEL_URL = 'https://www.booking.com/hotel/in/trident-nariman-point.html'
    
    try:
        metadata = get_hotel_metadata(HOTEL_URL)
        print(f"Hotel Metadata:\n{json.dumps(metadata, indent=2)}")
    except Exception as e:
        print(f"Error scraping hotel metadata: {e}")
        exit(1)
    
    reviews = scrape_all_reviews(HOTEL_URL, delay_seconds=2, max_pages=5)

    data = {
        'metadata': metadata,
        'reviews': reviews
    }

    hotel_name_safe = metadata['title'].replace(' ', '_').replace('/', '_')
    print(hotel_name_safe)
    save_to_cache(HOTEL_URL, data)
