import json
from transformers import pipeline

# Load models
classifier = pipeline("text-classification", model="nlptown/bert-base-multilingual-uncased-sentiment")
summarizer = pipeline("summarization")

# Load dummy news
with open('news_data.json', 'r') as file:
    news_data = json.load(file)

# Process each article
for data in news_data:
    title = data['title']
    description = data['description']
    article = data['article']

    # Get sentiment from title
    sentiment = classifier(title)[0]

    # Generate summary from description
    summary = summarizer(article, max_length=40, min_length=10, do_sample=False)[0]['summary_text']

    print("📰 Title:", title)
    print("🔍 Sentiment:", sentiment['label'], f"({round(sentiment['score'] * 100, 2)}%)")
    print("📝 Summary:", summary)
    print("📅 Published:", data['published_at'])
    print("🌐 Source:", data['source'])
    print("🔗 Link:", data['link'])
    print("-" * 80)
