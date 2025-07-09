import os
import json
import boto3
import matplotlib.pyplot as plt
from collections import Counter
import pandas as pd
from wordcloud import WordCloud
from datetime import datetime

# Initialize AWS Comprehend client
comprehend = boto3.client('comprehend')

#Loads the file containing the reviews for a specific hotel
def load_reviews(hotel_name):
    with open(f"../cache/{hotel_name}.json", encoding='utf-8') as f:
        return json.load(f)

#Used to filter out reviews that are not in English and contain no comments and are not too short
def filter_reviews(reviews):
    clean = []
    for r in reviews:
        lang = r.get('lang', '').lower()
        text = r.get('text', '').strip().lower()
        if lang not in ['en', 'en-us']:
            continue
        if "There are no comments available for this review" in text:
            continue
        if len(text) < 5:
            continue
        clean.append(r)
    return clean

#Generates a word cloud from the reviews
def enrich_reviews_with_aws(reviews):
    enriched = []
    for r in reviews:
        text = r['text']
        
        # Sentiment
        sent = comprehend.detect_sentiment(Text=text, LanguageCode='en')
        r['sentiment'] = sent['Sentiment']
        r['sentiment_scores'] = sent['SentimentScore']
        
        # Key phrases
        phrases = comprehend.detect_key_phrases(Text=text, LanguageCode='en')
        r['key_phrases'] = [p['Text'] for p in phrases['KeyPhrases']]
        
        enriched.append(r)
    return enriched

#save the processed reviews to a file
def save_processed(hotel_name, reviews):
    os.makedirs('./cache/processed', exist_ok=True)
    with open(f'./cache/processed/{hotel_name}_aws_processed.json', 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)

#Generate sentiment pie chart
def plot_sentiment_pie(hotel_name, reviews):
    sentiments = Counter(r['sentiment'] for r in reviews)
    labels, sizes = zip(*sentiments.items())
    plt.figure(figsize=(6,6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title(f"Sentiment Distribution - {hotel_name}")
    os.makedirs('charts', exist_ok=True)
    plt.savefig(f'charts/{hotel_name}_sentiment_pie.png')
    plt.close()

# Parse review date
def parse_review_date(date_str):
    # Example format: 'Reviewed: January 2024'
    try:
        return datetime.strptime(date_str.strip(), "%B %Y")
    except:
        return None

# Plotting the rating trend over time
def plot_rating_trend(hotel_name, reviews):
    data = []

    # Collect valid date/score pairs
    for r in reviews:
        date_obj = parse_review_date(r.get('date', ''))
        try:
            score = float(r.get('score'))
        except:
            score = None
        if date_obj and score is not None:
            # Normalize date to month-start
            date_obj = date_obj.replace(day=1)
            data.append({'date': date_obj, 'score': score})
    
    if not data:
        print("No rating data for trend")
        return

    # Make DataFrame
    df = pd.DataFrame(data)

    # Group by Month and Year, compute average
    df_grouped = df.groupby(pd.Grouper(key='date', freq='MS')).mean().reset_index()

    if df_grouped.empty:
        print("No data after grouping by month")
        return

    # Make sure charts directory exists
    os.makedirs("charts", exist_ok=True)

    # Plotting
    plt.figure(figsize=(10,6))
    plt.plot(df_grouped['date'], df_grouped['score'], marker='o', linestyle='-')
    plt.title(f"Average Rating Trend Over Time - {hotel_name}")
    plt.xlabel("Month")
    plt.ylabel("Average Rating")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.grid(True)
    plt.savefig(f'charts/{hotel_name}_rating_trend.png')
    plt.close()

# Generates country distribution bar chart
def plot_country_distribution(hotel_name, reviews):
    countries = Counter(r.get('user_country', 'Unknown') for r in reviews)
    top_countries = countries.most_common(10)
    
    labels, counts = zip(*top_countries)
    plt.figure(figsize=(10,6))
    plt.bar(labels, counts)
    plt.title(f"User Country Distribution - {hotel_name}")
    plt.xticks(rotation=45)
    plt.ylabel("Number of Reviews")
    plt.tight_layout()
    plt.savefig(f'charts/{hotel_name}_country_dist.png')
    plt.close()

# get the top 10 key phrases from the reviews
def plot_keyphrase_wordcloud(hotel_name, reviews):
    all_phrases = []
    for r in reviews:
        all_phrases.extend(r.get('key_phrases', []))
    text = ' '.join(all_phrases)

    if not text.strip():
        print("No key phrases found")
        return

    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    plt.figure(figsize=(10,6))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(f"Hotel Tags / Keywords - {hotel_name}")
    plt.savefig(f'charts/{hotel_name}_tags_wordcloud.png')
    plt.close()


# For later use
def filter_reviews_by_score_date(reviews, score_min=None, score_max=None, year=None, month=None):
    results = []
    for r in reviews:
        try:
            score = float(r.get('score', 0))
            date_obj = parse_review_date(r.get('date', ''))
        except:
            continue
        
        if score_min and score < score_min:
            continue
        if score_max and score > score_max:
            continue
        if year and (not date_obj or date_obj.year != year):
            continue
        if month and (not date_obj or date_obj.month != month):
            continue
        
        results.append(r)
    return results

# Main Pipeline
def run_pipeline(hotel_name):
    # Step 1: Load
    raw = load_reviews(hotel_name)
    clean = filter_reviews(raw)
    print(f"Loaded {len(clean)} reviews after cleaning.")

    # Step 2: Enrich
    enriched = enrich_reviews_with_aws(clean)
    save_processed(hotel_name, enriched)
    print("Processed and saved enriched reviews.")

    # Step 3: Charts
    plot_sentiment_pie(hotel_name, enriched)
    plot_rating_trend(hotel_name, enriched)
    plot_country_distribution(hotel_name, enriched)
    plot_keyphrase_wordcloud(hotel_name, enriched)
    print("Charts generated.")

if __name__ == '__main__':
    hotel_name = 'Trident_Nariman_Point_filtered'
    run_pipeline(hotel_name)
