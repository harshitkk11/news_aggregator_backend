import feedparser
import datetime
import re
from bs4 import BeautifulSoup
from config.db import get_db_connection
from transformers import pipeline
from newspaper import Article
from typing import Optional

def clean_description(description: str) -> str:
    """Clean and sanitize RSS description content"""
    if not description:
        return "No description available"
    
    # Remove HTML tags
    clean_text = BeautifulSoup(description, 'html.parser').get_text()
    
    # Remove excessive whitespace and special characters
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    clean_text = re.sub(r'[^\w\s.,!?\-]', '', clean_text)
    
    # Ensure minimum length
    if len(clean_text.split()) < 3:
        return "Description too short"
    
    return clean_text

def get_article_text(url: str) -> Optional[str]:
    """Fallback content extraction using Newspaper3k"""
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        print(f"Failed to extract article text: {e}")
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
        print(f"Failed to load models: {e}")
        return

    print("📥 Fetching RSS feed...")
    try:
        rss_url = "https://indianexpress.com/section/technology/feed/"
        feed = feedparser.parse(rss_url)
        if not feed.entries:
            print("No entries found in RSS feed")
            return
    except Exception as e:
        print(f"Failed to fetch RSS feed: {e}")
        return

    for entry in feed.entries[:10]:  # Process only first 10 entries
        try:
            # Extract and clean fields
            title = getattr(entry, 'title', 'No title').strip()
            raw_description = getattr(entry, 'description', '')
            description = clean_description(raw_description)
            
            # Fallback to article extraction if description is poor
            if len(description.split()) < 20:
                article_text = get_article_text(getattr(entry, 'link', ''))
                if article_text:
                    description = clean_description(article_text)
            
            link = getattr(entry, 'link', '')
            published_at = None
            if hasattr(entry, 'published'):
                try:
                    published_at = datetime.datetime.strptime(
                        entry.published, 
                        '%a, %d %b %Y %H:%M:%S %z'
                    )
                except ValueError:
                    published_at = datetime.datetime.now()
            
            source = "Indian Express"
            image_url = None
            if hasattr(entry, 'media_content') and entry.media_content:
                image_url = entry.media_content[0].get('url')

            # ✨ AI Processing
            summary_text = create_summary(description, summarizer)
            sentiment_label, sentiment_score = process_sentiment(title, sentiment_classifier)
            persons, organizations, locations = process_entities(description, ner_model)

            # Database insertion
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                insert_query = """
                INSERT INTO news 
                (title, description, summary, sentiment_label, sentiment_score, 
                 category, published_at, source, link, image_url, 
                 persons, organizations, locations, read_time, popularity, "categoryId")
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (link) DO UPDATE 
                SET description = EXCLUDED.description,
                    summary = EXCLUDED.summary,
                    sentiment_label = EXCLUDED.sentiment_label,
                    sentiment_score = EXCLUDED.sentiment_score;
                """

                cursor.execute(insert_query, (
                    title,
                    description,
                    summary_text,
                    sentiment_label,
                    sentiment_score,
                    "Technology",
                    published_at,
                    source,
                    link,
                    image_url,
                    ', '.join(persons) if persons else None,
                    ', '.join(organizations) if organizations else None,
                    ', '.join(locations) if locations else None,
                    2,  # read_time
                    0,  # popularity
                    "aa63ec0e-aedd-4a0e-b75a-e1979c31d6a8"  # Your tech category ID
                ))
                conn.commit()
                print(f"✅ Saved news: {title}")

            except Exception as db_error:
                print(f"❌ Database error for {title}: {db_error}")
                if conn:
                    conn.rollback()
            finally:
                if conn:
                    cursor.close()
                    conn.close()

        except Exception as e:
            print(f"❌ Error processing entry: {e}")
            continue

if __name__ == "__main__":
    fetch_and_process_news()