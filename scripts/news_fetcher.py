# scripts/news_fetcher.py
# Fetch RSS ➔ Process with AI ➔ Save into news table

import feedparser
import datetime
from config.db import get_db_connection

def fetch_and_process_news():
    from transformers import pipeline

    print("⚙️ Loading AI models...")
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    sentiment_classifier = pipeline("text-classification", model="nlptown/bert-base-multilingual-uncased-sentiment")
    ner_model = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")

    print("📥 Fetching RSS feed...")
    rss_url = "https://indianexpress.com/section/technology/feed/"
    feed = feedparser.parse(rss_url)

    for entry in feed.entries:
        try:
            # Extract fields
            title = entry.title
            description = entry.description
            link = entry.link
            published_at = entry.published if hasattr(entry, 'published') else None
            source = "Indian Express"
            image_url = None

            if 'media_content' in entry:
                image_url = entry.media_content[0]['url']

            # ✨ AI Processing
            summary_text = summarizer(description, min_length=20, do_sample=False)[0]['summary_text']
            sentiment = sentiment_classifier(title)[0]
            sentiment_label = sentiment['label']
            sentiment_score = float(sentiment['score'])

            # 🧠 Named Entity Recognition (NER)
            entities = ner_model(description)
            persons = [entity['word'] for entity in entities if entity['entity_group'] == 'PER']
            organizations = [entity['word'] for entity in entities if entity['entity_group'] == 'ORG']
            locations = [entity['word'] for entity in entities if entity['entity_group'] == 'LOC']

            # Default fields
            read_time = 2
            popularity = 0

            # 🔗 Open fresh DB connection per entry
            conn = get_db_connection()
            cursor = conn.cursor()

            insert_query = """
            INSERT INTO news 
            (title, description, summary, sentiment_label, sentiment_score, category, published_at, source, link, image_url, persons, organizations, locations, read_time, popularity)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (link) DO NOTHING;
            """

            cursor.execute(insert_query, (
                title,
                description,
                summary_text,
                sentiment_label,
                sentiment_score,
                "Technology",
                datetime.datetime.strptime(published_at, '%a, %d %b %Y %H:%M:%S %z') if published_at else None,
                source,
                link,
                image_url,
                ', '.join(persons) if persons else None,
                ', '.join(organizations) if organizations else None,
                ', '.join(locations) if locations else None,
                read_time,
                popularity
            ))
            conn.commit()
            cursor.close()
            conn.close()

            print(f"✅ Saved news: {title}")

        except Exception as e:
            print(f"❌ Error processing {entry.title}: {e}")
            if 'conn' in locals():
                conn.rollback()
                cursor.close()
                conn.close()
