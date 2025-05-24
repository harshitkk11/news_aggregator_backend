import feedparser
import datetime
import re
from bs4 import BeautifulSoup
from config.db import get_db_connection
from transformers import pipeline
from newspaper import Article
from typing import Optional
from flask import Flask, jsonify

app = Flask(__name__)

# ========== HELPER FUNCTIONS ==========
def clean_description(description: str) -> str:
    """Clean and sanitize RSS description content"""
    if not description:
        return "No description available"
    
    clean_text = BeautifulSoup(description, 'html.parser').get_text()
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    clean_text = re.sub(r'[^\w\s.,!?\-]', '', clean_text)
    
    return clean_text if len(clean_text.split()) >= 3 else "Description too short"

def get_article_text(url: str) -> Optional[str]:
    """Fallback content extraction using Newspaper3k"""
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        print(f"Article extraction failed: {e}")
        return None

def process_sentiment(title: str, classifier) -> tuple:
    """Process sentiment analysis with error handling"""
    try:
        sentiment = classifier(title)[0]
        return sentiment['label'], float(sentiment['score'])
    except Exception as e:
        print(f"Sentiment analysis failed: {e}")
        return "NEUTRAL", 0.0

def process_entities(text: str, ner_model) -> tuple:
    """Process named entity recognition"""
    try:
        entities = ner_model(text)
        persons = [entity['word'] for entity in entities if entity['entity_group'] == 'PER']
        organizations = [entity['word'] for entity in entities if entity['entity_group'] == 'ORG']
        locations = [entity['word'] for entity in entities if entity['entity_group'] == 'LOC']
        return persons, organizations, locations
    except Exception as e:
        print(f"NER failed: {e}")
        return [], [], []

def create_summary(text: str, summarizer) -> str:
    """Create summary with dynamic length handling"""
    if not text or not summarizer:
        return "No summary available"
    
    word_count = len(text.split())
    if word_count < 5:
        return text
    
    try:
        max_len = min(50, max(10, word_count // 2))
        return summarizer(
            text,
            max_length=max_len,
            min_length=3,
            do_sample=False
        )[0]['summary_text']
    except Exception as e:
        print(f"Summarization failed: {e}")
        return text[:200] + "..." if len(text) > 200 else text

# ========== MAIN FUNCTION ==========
def fetch_and_process_news():
    print("⚙️ Loading AI models...")
    try:
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        sentiment_classifier = pipeline(
            "text-classification", 
            model="nlptown/bert-base-multilingual-uncased-sentiment"
        )
        ner_model = pipeline(
            "ner", 
            model="dslim/bert-base-NER", 
            aggregation_strategy="simple"
        )
    except Exception as e:
        print(f"❌ Failed to load models: {e}")
        return {"status": "error", "message": f"Failed to load models: {e}"}

    print("📊 Fetching feed URLs and categories from database...")
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Modified query with type casting to handle text = uuid mismatch
        cur.execute("""
            SELECT fu.feed_url, fu.category_id, c.title AS category_title 
            FROM feed_urls fu
            LEFT JOIN categories c ON fu.category_id::uuid = c.id
        """)
        feed_urls = cur.fetchall()
        
        if not feed_urls:
            print("ℹ️ No feed URLs found in database")
            return {"status": "info", "message": "No feed URLs found in database"}

        total_processed = 0
        two_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=2)

        for feed_url, category_id, category_title in feed_urls:
            try:
                print(f"\n🔍 Processing feed: {feed_url[:60]}... (Category: {category_title or 'Unknown'})")
                feed = feedparser.parse(feed_url)
                
                if not feed.entries:
                    print(f"⚠️ No entries found in feed")
                    continue

                # Filter and sort entries by published date (latest first)
                recent_entries = []
                for entry in feed.entries:
                    published_at = datetime.datetime.now(datetime.timezone.utc)
                    if hasattr(entry, 'published'):
                        try:
                            published_at = datetime.datetime.strptime(
                                entry.published, 
                                '%a, %d %b %Y %H:%M:%S %z'
                            )
                        except ValueError:
                            continue
                    
                    # Skip entries older than 2 days
                    if published_at < two_days_ago:
                        continue
                    
                    recent_entries.append((published_at, entry))
                
                # Sort by published date (descending) and take the latest 5
                recent_entries.sort(key=lambda x: x[0], reverse=True)
                recent_entries = [entry for _, entry in recent_entries[:5]]

                if not recent_entries:
                    print(f"⚠️ No recent entries (within 2 days) found in feed")
                    continue

                for entry in recent_entries:
                    try:
                        # Extract and clean fields
                        title = getattr(entry, 'title', 'No title').strip()
                        raw_description = getattr(entry, 'description', '')
                        description = clean_description(raw_description)
                        
                        # Fallback to article extraction
                        if len(description.split()) < 20:
                            article_text = get_article_text(getattr(entry, 'link', ''))
                            if article_text:
                                description = clean_description(article_text)
                        
                        link = getattr(entry, 'link', '')
                        published_at = datetime.datetime.now()
                        if hasattr(entry, 'published'):
                            try:
                                published_at = datetime.datetime.strptime(
                                    entry.published, 
                                    '%a, %d %b %Y %H:%M:%S %z'
                                )
                            except ValueError:
                                pass

                        source = feed_url.split('/')[2]  # Extract domain
                        image_url = None
                        if hasattr(entry, 'media_content') and entry.media_content:
                            image_url = entry.media_content[0].get('url')

                        # AI Processing
                        summary_text = create_summary(description, summarizer)
                        sentiment_label, sentiment_score = process_sentiment(title, sentiment_classifier)
                        persons, organizations, locations = process_entities(description, ner_model)

                        # Database insertion
                        insert_query = """
                        INSERT INTO news 
                        (title, description, summary, sentiment_label, sentiment_score, 
                         category, published_at, source, link, image_url, 
                         persons, organizations, locations, read_time, popularity, "categoryId")
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (link) DO NOTHING;
                        """

                        cur.execute(insert_query, (
                            title,
                            description,
                            summary_text,
                            sentiment_label,
                            sentiment_score,
                            category_title or "General",  # Use the category title from the database
                            published_at,
                            source,
                            link,
                            image_url,
                            ', '.join(persons) if persons else None,
                            ', '.join(organizations) if organizations else None,
                            ', '.join(locations) if locations else None,
                            2,  # read_time
                            0,  # popularity
                            category_id
                        ))
                        conn.commit()
                        total_processed += 1
                        print(f"✅ Saved: {title[:60]}... (Published: {published_at})")

                    except Exception as entry_error:
                        print(f"❌ Entry processing failed: {str(entry_error)[:100]}...")
                        continue

                print(f"✔️ Finished processing 5 recent articles from {feed_url[:60]}")

            except Exception as feed_error:
                print(f"🚨 Feed processing failed: {str(feed_error)[:100]}...")
                continue

        print(f"\n🎉 Finished! Processed {total_processed} articles from {len(feed_urls)} feeds")
        return {"status": "success", "message": f"Processed {total_processed} articles from {len(feed_urls)} feeds"}

    except Exception as db_error:
        print(f"💥 Database error: {db_error}")
        return {"status": "error", "message": f"Database error: {db_error}"}
    finally:
        cur.close()
        conn.close()

# ========== FLASK ROUTE ==========
@app.route('/api/fetch-news', methods=['GET'])
def fetch_news():
    print("🔥 Fetching news...")
    result = fetch_and_process_news()
    return jsonify(result)

if __name__ == "__main__":
    print("🔥 main.py started")
    app.run(host='0.0.0.0', port=5000)