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


def loading(request):
    return render(request, 'analysis/loading.html')

def result(request, hotel_name):
    # Load enriched review data
    processed_path = os.path.join(settings.BASE_DIR, 'cache', 'processed', f"{hotel_name}_aws_processed.json")
    if not os.path.exists(processed_path):
        return render(request, 'analysis/result.html', {'error': 'No data found'})

    with open(processed_path, encoding='utf-8') as f:
        reviews = json.load(f)

    return render(request, 'analysis/result.html', {
        'hotel_name': hotel_name.replace('_', ' '),
        'review_count': len(reviews),
        'charts': {
            'sentiment': f"/charts/{hotel_name}_sentiment_pie.png",
            'trend': f"/charts/{hotel_name}_rating_trend.png",
            'country': f"/charts/{hotel_name}_country_dist.png",
            'tags': f"/charts/{hotel_name}_tags_wordcloud.png",
        }
    })
