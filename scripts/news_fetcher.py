import feedparser
import datetime
import re
import requests
from bs4 import BeautifulSoup
from config.db import get_db_connection
from transformers import pipeline, BartTokenizer
from newspaper import Article
from typing import Optional
from flask import Flask, jsonify

app = Flask(__name__)

# ========== HELPER FUNCTIONS ==========
def fetch_description_from_article(url: str) -> Optional[str]:
    """Fetch a description from the article page if RSS description is missing"""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Try meta description first
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content']

        # Fallback to first paragraph
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if text and len(text.split()) > 10:  # Ensure it's a meaningful paragraph
                return text[:200]  # Limit to 200 characters for description

        return None
    except Exception as e:
        print(f"Failed to fetch description from article: {e}")
        return None

def clean_description(entry: dict, link: str) -> str:
    """Use RSS description as is, checking all possible fields including media, with fallback to article page"""
    description = None

    # Detailed logging to confirm field access
    print(f"🔍 Checking description field for entry: {getattr(entry, 'title', 'Unknown title')[:60]}...")
    if hasattr(entry, 'description'):
        print(f"🔍 Found 'description' attribute: {entry.description[:100] if entry.description else 'Empty'}")
        if entry.description:
            description = entry.description
    else:
        print("🔍 No 'description' attribute found in entry")

    if not description and hasattr(entry, 'summary'):
        print(f"🔍 Found 'summary' attribute: {entry.summary[:100] if entry.summary else 'Empty'}")
        if entry.summary:
            description = entry.summary
    else:
        print("🔍 No 'summary' attribute found or no description yet")

    if not description and hasattr(entry, 'content'):
        print(f"🔍 Found 'content' attribute: {entry.content[:100] if entry.content else 'Empty'}")
        content = entry.content[0].value if isinstance(entry.content, list) and entry.content else entry.content
        if content:
            description = content
    else:
        print("🔍 No 'content' attribute found or no description yet")

    if not description and 'content:encoded' in entry:
        print(f"🔍 Found 'content:encoded': {entry['content:encoded'][:100] if entry['content:encoded'] else 'Empty'}")
        if entry['content:encoded']:
            description = entry['content:encoded']
    else:
        print("🔍 No 'content:encoded' found or no description yet")

    if not description and hasattr(entry, 'media_description'):
        print(f"🔍 Found 'media_description': {entry.media_description[:100] if entry.media_description else 'Empty'}")
        if entry.media_description:
            description = entry.media_description
    else:
        print("🔍 No 'media_description' found or no description yet")

    if not description and hasattr(entry, 'media_text'):
        print(f"🔍 Found 'media_text': {entry.media_text[:100] if entry.media_text else 'Empty'}")
        if entry.media_text:
            description = entry.media_text
    else:
        print("🔍 No 'media_text' found or no description yet")

    if not description and hasattr(entry, 'media_content'):
        print(f"🔍 Found 'media_content': {entry.media_content[:100] if entry.media_content else 'Empty'}")
        for media in entry.media_content:
            if 'description' in media and media['description']:
                print(f"🔍 Found 'media_content.description': {media['description'][:100]}")
                description = media['description']
                break
            elif 'title' in media and media['title']:
                print(f"🔍 Found 'media_content.title': {media['title'][:100]}")
                description = media['title']
                break
    else:
        print("🔍 No 'media_content' found or no description yet")

    # Summary log of all fields
    print(f"📜 Entry fields - description: {getattr(entry, 'description', 'None')[:100]}, "
          f"summary: {getattr(entry, 'summary', 'None')[:100]}, "
          f"content: {getattr(entry, 'content', 'None')[:100] if hasattr(entry, 'content') else 'None'}, "
          f"content:encoded: {entry.get('content:encoded', 'None')[:100]}, "
          f"media_description: {getattr(entry, 'media_description', 'None')[:100]}, "
          f"media_content: {getattr(entry, 'media_content', 'None')[:100] if hasattr(entry, 'media_content') else 'None'}")

    # If no description found in RSS, fetch from article page
    if not description and link:
        print(f"🔍 Fetching description from article page: {link[:60]}...")
        description = fetch_description_from_article(link)
        if description:
            print(f"🔍 Fetched description from article: {description[:100]}...")

    if not description:
        print("⚠️ No description field found in entry or article")
        return "No description available"

    # Minimal cleaning to preserve content
    clean_text = BeautifulSoup(description, 'html.parser').get_text()
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    clean_text = re.sub(r'[^\w\s.,!?\-;:()\'"@#&]', '', clean_text)

    print(f"📜 Cleaned description: {clean_text[:100]}...")

    return clean_text if clean_text else "No description available"

def get_article_text(url: str, entry: dict = None) -> Optional[str]:
    """Fetch full article content, falling back to BeautifulSoup if necessary"""
    # First attempt with Newspaper3k
    try:
        article = Article(url)
        article.download()
        article.parse()
        if article.text and len(article.text.split()) > 50:  # Ensure enough content
            return article.text
    except Exception as e:
        print(f"Newspaper3k extraction failed: {e}")

    # Fallback to BeautifulSoup scraping
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Target common elements for article content
        content = []
        # Look for paragraphs (common for intro text)
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if text:
                content.append(text)

        # Look for divs with captions or descriptions (common in Indian Express articles)
        for div in soup.find_all('div', class_=re.compile('caption|description|content|story|article')):
            text = div.get_text(strip=True)
            if text:
                content.append(text)

        # If not enough content, extract from media_content in RSS feed
        if len(' '.join(content).split()) < 50 and entry and hasattr(entry, 'media_content'):
            for media in entry.media_content:
                if 'description' in media and media['description']:
                    caption = BeautifulSoup(media['description'], 'html.parser').get_text(strip=True)
                    if caption:
                        content.append(caption)
                elif 'title' in media and media['title']:
                    caption = BeautifulSoup(media['title'], 'html.parser').get_text(strip=True)
                    if caption:
                        content.append(caption)

        article_text = ' '.join(content).strip()
        return article_text if article_text else None
    except Exception as e:
        print(f"BeautifulSoup extraction failed: {e}")
        return None

def truncate_text(text: str, tokenizer, max_tokens: int = 1024) -> str:
    """Truncate text to fit within the model's max token length"""
    tokens = tokenizer(text, truncation=True, max_length=max_tokens, return_tensors="pt")
    truncated_text = tokenizer.decode(tokens['input_ids'][0], skip_special_tokens=True)
    return truncated_text

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

def create_summary(text: str, link: str, summarizer, tokenizer, entry: dict = None) -> str:
    """Create summary aiming for 6-15 lines (60-225 words), ensuring larger size"""
    if not link:
        return "No summary available"
    
    if not summarizer:
        return "No summary available"

    # Always use full article text for summarization to ensure enough content
    cleaned_text = None
    if link:
        article_text = get_article_text(link, entry)
        if article_text:
            print(f"📝 Fetched full article text for summary from {link[:60]}...")
            cleaned_text = BeautifulSoup(article_text, 'html.parser').get_text()
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
            cleaned_text = re.sub(r'[^\w\s.,!?\-;:()\'"@#&]', '', cleaned_text)

    # If no article text, fall back to the provided text
    if not cleaned_text:
        cleaned_text = BeautifulSoup(text, 'html.parser').get_text()
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        cleaned_text = re.sub(r'[^\w\s.,!?\-;:()\'"@#&]', '', cleaned_text)

    word_count = len(cleaned_text.split())
    print(f"📝 Input text length for summary: {word_count} words")
    if word_count < 5:
        return cleaned_text
    
    try:
        # Truncate the input to avoid token length issues (BART max is 1024 tokens)
        cleaned_text = truncate_text(cleaned_text, tokenizer, max_tokens=1024)

        # Aim for 6-15 lines: assuming 10-15 words per line, that's 60-225 words
        # Adjust parameters based on input length
        max_len = min(350, max(word_count // 2, 225))  # Aim for up to 350 words
        min_len = min(150, max(word_count // 3, 100))  # Start with 150 words, adjust down if input is short
        summary = summarizer(
            cleaned_text,
            max_length=max_len,
            min_length=min_len,
            do_sample=False
        )[0]['summary_text']

        # Check if the summary is too short (less than 150 words for ~15 lines)
        summary_word_count = len(summary.split())
        print(f"📝 Initial summary length: {summary_word_count} words")
        if summary_word_count < 150 and link:
            # Retry with higher length parameters
            print(f"📝 Retrying summary with adjusted parameters from {link[:60]}...")
            max_len = min(500, max(word_count, 350))  # Increase max_length for retry
            min_len = min(175, max(word_count // 2, 150))  # Increase min_length
            summary = summarizer(
                cleaned_text,
                max_length=max_len,
                min_length=min_len,
                do_sample=False
            )[0]['summary_text']
            print(f"📝 Retry summary length: {len(summary.split())} words")

        return summary
    except Exception as e:
        print(f"Summarization failed: {e}")
        # Fallback to truncated input text
        return cleaned_text[:225] + "..." if len(cleaned_text.split()) > 225 else cleaned_text

# ========== MAIN FUNCTION ==========
def fetch_and_process_news():
    print("⚙️ Loading AI models...")
    try:
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")
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
        # Query with type casting to handle text = uuid mismatch
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

                # Log channel metadata
                print(f"📋 Feed metadata - Title: {feed.feed.get('title', 'N/A')}, "
                      f"Link: {feed.feed.get('link', 'N/A')}, "
                      f"Description: {feed.feed.get('description', 'N/A')[:100]}, "
                      f"Language: {feed.feed.get('language', 'N/A')}, "
                      f"Last Build Date: {feed.feed.get('lastbuilddate', 'N/A')}, "
                      f"Generator: {feed.feed.get('generator', 'N/A')}")

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
                        link = getattr(entry, 'link', '')
                        description = clean_description(entry, link)
                        
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
                        summary_text = create_summary(description, link, summarizer, tokenizer, entry)
                        sentiment_label, sentiment_score = process_sentiment(title, sentiment_classifier)
                        # Use summary_text for NER instead of description
                        persons, organizations, locations = process_entities(summary_text, ner_model)

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