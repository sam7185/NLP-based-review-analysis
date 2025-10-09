import os
import json
import boto3
from collections import Counter
from datetime import datetime


# Helper: create AWS Comprehend client lazily (may fail if credentials not configured)
def get_comprehend_client():
    try:
        return boto3.client('comprehend')
    except Exception:
        return None


# Very small fallback sentiment analyzer (keyword-based) used when AWS is unavailable
def simple_sentiment(text: str):
    text = (text or '').lower()
    pos = ['good', 'great', 'excellent', 'fantastic', 'amazing', 'lov', 'wonderful']
    neg = ['bad', 'terrible', 'poor', 'awful', 'worst', 'hate']
    p = sum(1 for w in pos if w in text)
    n = sum(1 for w in neg if w in text)
    if p > n:
        return {'Sentiment': 'POSITIVE', 'SentimentScore': {'Positive': 1.0, 'Negative': 0.0, 'Neutral': 0.0, 'Mixed': 0.0}}
    if n > p:
        return {'Sentiment': 'NEGATIVE', 'SentimentScore': {'Positive': 0.0, 'Negative': 1.0, 'Neutral': 0.0, 'Mixed': 0.0}}
    return {'Sentiment': 'NEUTRAL', 'SentimentScore': {'Positive': 0.0, 'Negative': 0.0, 'Neutral': 1.0, 'Mixed': 0.0}}


# Clean old chart files for hotel
def clean_old_charts(hotel_name):
    charts_dir = './cache/charts_json'
    for chart_type in ['sentiment', 'trend', 'country', 'charts']:
        path = os.path.join(charts_dir, f"{hotel_name}_{chart_type}.json")
        if os.path.exists(path):
            os.remove(path)
            print(f"[INFO] Deleted old chart: {path}")


# Load reviews from JSON
def load_reviews(hotel_name):
    with open(f"./cache/{hotel_name}.json", encoding='utf-8') as f:
        data = json.load(f)
    return data['reviews']


# Filter reviews
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


# Enrich with AWS
def enrich_reviews_with_aws(reviews):
    enriched = []
    client = get_comprehend_client()
    for r in reviews:
        text = r.get('text', '')
        if client:
            try:
                sent = client.detect_sentiment(Text=text, LanguageCode='en')
                r['sentiment'] = sent.get('Sentiment')
                r['sentiment_scores'] = sent.get('SentimentScore')

                phrases = client.detect_key_phrases(Text=text, LanguageCode='en')
                r['key_phrases'] = [p['Text'] for p in phrases.get('KeyPhrases', [])]
            except Exception as e:
                # If AWS fails at runtime, fallback to simple analyzer
                fallback = simple_sentiment(text)
                r['sentiment'] = fallback['Sentiment']
                r['sentiment_scores'] = fallback['SentimentScore']
                r['key_phrases'] = []
        else:
            # No AWS client available — use fallback analyzer
            fallback = simple_sentiment(text)
            r['sentiment'] = fallback['Sentiment']
            r['sentiment_scores'] = fallback['SentimentScore']
            r['key_phrases'] = []

        enriched.append(r)
    return enriched


# Save processed reviews
def save_processed(hotel_name, reviews):
    os.makedirs('./cache/processed', exist_ok=True)
    with open(f'./cache/processed/{hotel_name}_aws_processed.json', 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)


# Safely save plotly figure to JSON

def save_plotly_figure_json(fig, path):
    if fig is None:
        print(f"[WARNING] Not saving: figure is None for {path}")
        return
    try:
        import plotly
        import plotly.utils

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(fig.to_plotly_json(), f, cls=plotly.utils.PlotlyJSONEncoder)
        print(f"[INFO] Saved chart JSON: {path}")
    except Exception as e:
        print(f"[ERROR] Failed saving JSON for {path}: {e}")



# Sentiment Pie Chart
def plot_sentiment_pie(hotel_name, reviews):
    sentiments = Counter(r['sentiment'] for r in reviews)
    if not sentiments:
        print(f"[WARNING] No sentiment data for {hotel_name}")
        return None
    try:
        import plotly.graph_objects as go

        labels, sizes = zip(*sentiments.items())
        fig = go.Figure(data=[go.Pie(labels=labels, values=sizes, hole=0.3)])
        fig.update_layout(title=f"Sentiment Distribution - {hotel_name}")
        save_plotly_figure_json(fig, f'cache/charts_json/{hotel_name}_sentiment.json')
    except Exception as e:
        print(f"[ERROR] Could not create sentiment pie (missing plotly?): {e}")


# Parse review date
def parse_review_date(date_str):
    try:
        return datetime.strptime(date_str.strip(), "%B %Y")
    except:
        return None


# Rating Trend Chart
def plot_rating_trend(hotel_name, reviews):
    data = []
    for r in reviews:
        date_obj = parse_review_date(r.get('date', ''))
        try:
            score = float(r.get('score'))
        except:
            continue
        if date_obj and score is not None:
            date_obj = date_obj.replace(day=1)
            data.append({'date': date_obj, 'score': score})

    if not data:
        print(f"[WARNING] No rating data for {hotel_name}")
        return None

    try:
        import pandas as pd

        df = pd.DataFrame(data)
        df_grouped = df.groupby(pd.Grouper(key='date', freq='MS')).mean().reset_index()
    except Exception as e:
        print(f"[ERROR] pandas missing or failed to create DataFrame: {e}")
        return None

    if df_grouped.empty or df_grouped['score'].isnull().all():
        print(f"[WARNING] No valid grouped rating data for {hotel_name}")
        return None

    try:
        import plotly.express as px

        fig = px.line(
            df_grouped,
            x='date',
            y='score',
            markers=True,
            title=f"Average Rating Trend Over Time - {hotel_name}",
            labels={'date': 'Month', 'score': 'Average Rating'}
        )
        fig.update_layout(xaxis=dict(tickformat='%b %Y'))
        save_plotly_figure_json(fig, f'cache/charts_json/{hotel_name}_trend.json')
    except Exception as e:
        print(f"[ERROR] Could not create trend chart (missing plotly?): {e}")


# Country Distribution Chart
def plot_country_distribution(hotel_name, reviews):
    countries = [r.get('user_country') for r in reviews if r.get('user_country')]
    if not countries:
        print(f"[WARNING] No country data for {hotel_name}")
        return None

    counter = Counter(countries)
    top_countries = counter.most_common(10)

    if not top_countries:
        print(f"[WARNING] No top countries for {hotel_name}")
        return None

    labels, counts = zip(*top_countries)
    try:
        import plotly.express as px

        fig = px.bar(
            x=labels,
            y=counts,
            title=f"User Country Distribution - {hotel_name}",
            labels={'x': 'Country', 'y': 'Number of Reviews'}
        )
        fig.update_layout(xaxis_tickangle=-45)
        save_plotly_figure_json(fig, f'cache/charts_json/{hotel_name}_country.json')
    except Exception as e:
        print(f"[ERROR] Could not create country chart (missing plotly?): {e}")


# WordCloud for Key Phrases
def plot_keyphrase_wordcloud(hotel_name, reviews):
    all_phrases = []
    for r in reviews:
        all_phrases.extend(r.get('key_phrases', []))
    text = ' '.join(all_phrases)

    if not text.strip():
        print(f"[WARNING] No key phrases for {hotel_name}")
        return

    try:
        from wordcloud import WordCloud

        os.makedirs('charts', exist_ok=True)
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
        wordcloud.to_file(f'charts/{hotel_name}_tags_wordcloud.png')
        print(f"[INFO] Saved wordcloud image.")
    except Exception as e:
        print(f"[ERROR] Could not generate wordcloud (missing wordcloud lib?): {e}")


# Main Pipeline
def run_pipeline(hotel_name):
    clean_old_charts(hotel_name)

    raw = load_reviews(hotel_name)
    clean = filter_reviews(raw)
    print(f"[INFO] Loaded {len(clean)} reviews after cleaning.")

    enriched = enrich_reviews_with_aws(clean)
    save_processed(hotel_name, enriched)
    print("[INFO] Processed and saved enriched reviews.")

    # Generate charts
    plot_sentiment_pie(hotel_name, enriched)
    plot_rating_trend(hotel_name, enriched)
    plot_country_distribution(hotel_name, enriched)
    plot_keyphrase_wordcloud(hotel_name, enriched)

    # Combine charts JSON
    charts_dir = './cache/charts_json'
    combined_path = os.path.join(charts_dir, f'{hotel_name}_charts.json')
    os.makedirs(charts_dir, exist_ok=True)

    combined_data = {}
    for chart_type in ['sentiment', 'trend', 'country']:
        chart_file = os.path.join(charts_dir, f'{hotel_name}_{chart_type}.json')
        if os.path.exists(chart_file):
            try:
                with open(chart_file, encoding='utf-8') as f:
                    combined_data[chart_type] = json.load(f)
            except Exception as e:
                print(f"[ERROR] Failed loading {chart_file}: {e}")
        else:
            print(f"[WARNING] Missing {chart_type} chart JSON for {hotel_name}")

    if not combined_data:
        print(f"[WARNING] No chart JSON generated for {hotel_name}")

    with open(combined_path, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=2)

    print("[INFO] Charts generated and combined JSON saved.")
    return combined_data
