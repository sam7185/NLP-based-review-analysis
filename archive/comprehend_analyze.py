# import boto3

# def analyze_sentiment(text):
#     client = boto3.client('comprehend', region_name='us-east-1')
#     response = client.detect_sentiment(
#         Text=text,
#         LanguageCode='en'
#     )
#     return response['Sentiment']

# if __name__ == '__main__':
#     sample_text = "I love this hotel. The staff were very helpful!"
#     sentiment = analyze_sentiment(sample_text)
#     print(f"Sentiment: {sentiment}")
