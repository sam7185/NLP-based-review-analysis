import os
import json
from django.shortcuts import render, redirect
from django.conf import settings
from scrap import scrape_hotel_reviews
from analyze import run_pipeline
from scrap import extract_pagename

def index(request):
    if request.method == 'POST':
        hotel_url = request.POST.get('hotel_url')
        if hotel_url:
            try:
                # STEP 1: Scrape hotel reviews
                scrape_hotel_reviews(hotel_url, max_pages=1)

                # STEP 2: Get hotel name from metadata
                pagename = extract_pagename(hotel_url)
                hotel_file = f"{pagename}.json"

                # STEP 3: Run analysis
                run_pipeline(pagename)

                # STEP 4: Redirect to result
                return redirect('result', hotel_name=pagename)
            except Exception as e:
                return render(request, 'analysis/index.html', {'error': str(e)})

    return render(request, 'analysis/index.html')


def loading_view(request):
    hotel_url = request.GET.get('hotel_url')
    if not hotel_url:
        return redirect('index')

    pagename = extract_pagename(hotel_url)
    processed_file = f'./cache/processed/{pagename}_aws_processed.json'

    if os.path.exists(processed_file):
        # Already processed → skip scraping
        return redirect('result', hotel_name=pagename)

    # Not processed → run pipeline (scraping + analyze)
    scrape_hotel_reviews(hotel_url, max_pages=1)
    charts = run_pipeline(pagename)
    os.makedirs(f'./cache/charts_json', exist_ok=True)
    with open(f'./cache/charts_json/{pagename}_charts.json', 'w', encoding='utf-8') as f:
        json.dump(charts, f)

def result(request, hotel_name):
    processed_path = os.path.join(settings.BASE_DIR, 'cache', 'processed', f"{hotel_name}_aws_processed.json")
    charts_combined_path = os.path.join(settings.BASE_DIR, 'cache', 'charts_json', f"{hotel_name}_charts.json")

    if not os.path.exists(processed_path):
        return render(request, 'analysis/result.html', {'error': 'No processed data found'})

    with open(processed_path, encoding='utf-8') as f:
        reviews = json.load(f)

    if os.path.exists(charts_combined_path):
        with open(charts_combined_path, encoding='utf-8') as f:
            charts_json = json.load(f)
    else:
        print(f"[WARNING] charts JSON not found for {hotel_name}, re-running pipeline...")
        from analyze import run_pipeline
        run_pipeline(hotel_name)
        # After rerun, try loading again:
        if os.path.exists(charts_combined_path):
            with open(charts_combined_path, encoding='utf-8') as f:
                charts_json = json.load(f)
        else:
            charts_json = {}

    return render(request, 'analysis/result.html', {
        'hotel_name': hotel_name.replace('_', ' '),
        'review_count': len(reviews),
        'charts': json.dumps(charts_json),  # important: make sure it's a JSON string for template
        'tags_wordcloud': f"/charts/{hotel_name}_tags_wordcloud.png"
    })
