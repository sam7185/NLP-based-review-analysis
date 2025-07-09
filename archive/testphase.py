import json
import os

def load_cached_reviews(filename):
    """Load a JSON file from the cache folder"""
    path = os.path.join('cache', filename)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def filter_reviews_for_testing(reviews_json, max_count=5):
    """Filter English reviews with non-empty text"""
    filtered = []
    for review in reviews_json:
        lang = review.get('lang', '').lower()
        text = review.get('text', '').strip()
        
        if lang not in ('en', 'en-us'):
            continue
        
        if "there are no comments available for this review" in text.lower():
            continue
        
        if not text:
            continue

        filtered.append(review)
        if len(filtered) >= max_count:
            break
    
    return filtered

def save_filtered_reviews(hotel_name, reviews):
    """Save filtered reviews to a new JSON file in cache"""
    os.makedirs('cache', exist_ok=True)
    filename = os.path.join('cache', f"{hotel_name}_filtered.json")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    print(f"Saved filtered reviews to {filename}")

def main():
    # replace with the actual file name you saved with scrap.py
    hotel_json_filename = '../cache/trident-nariman-point.json'

    print(f"Loading cached reviews from {hotel_json_filename}")
    data = load_cached_reviews(hotel_json_filename)
    reviews = data.get('reviews', [])

    print(f"Total reviews loaded: {len(reviews)}")
    filtered = filter_reviews_for_testing(reviews)
    print(f"Filtered reviews count: {len(filtered)}")

    # save for AWS Comprehend input
    save_filtered_reviews('Trident_Nariman_Point', filtered)

    # also print them to see
    print(json.dumps(filtered, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
