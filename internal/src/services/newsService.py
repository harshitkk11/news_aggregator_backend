import feedparser
from transformers import pipeline
from internal.src.repositories.newsRepository import NewsRepository
from internal.src.db.cursor import get_cursor

class NewsService:
    def __init__(self):
        self.connection, self.cursor = get_cursor()
        self.news_repository = NewsRepository(self.connection, self.cursor)
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        self.sentiment_classifier = pipeline("text-classification", model="nlptown/bert-base-multilingual-uncased-sentiment")
        self.ner_model = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english", aggregation_strategy="simple")

    def fetch_and_process_news(self):
        print("📥 Fetching RSS feed...")
        rss_url = "https://indianexpress.com/section/technology/feed/"
        feed = feedparser.parse(rss_url)

        for entry in feed.entries:
            try:
                # Print all available data from RSS feed
                print("\n=== RSS Entry Data ===")
                print(f"Title: {entry.title}")
                print(f"Description: {entry.description}")
                print(f"Link: {entry.link}")
                print(f"Published Date: {getattr(entry, 'published', 'Not available')}")
                print(f"Source: Indian Express")
                print(f"Image URL: {entry.media_content[0]['url'] if 'media_content' in entry else 'No image'}")
                
                # Continue with existing processing
                title = entry.title
                description = entry.description
                link = entry.link
                published_at = getattr(entry, 'published', None)
                source = "Indian Express"
                image_url = entry.media_content[0]['url'] if 'media_content' in entry else None

                summary_text = self.summarize_description(description)
                sentiment_label, sentiment_score = self.analyze_sentiment(title)
                persons, organizations, locations = self.extract_entities(description)

                read_time = 2  # dummy
                popularity = 0

                self.news_repository.save_news((
                    title, description, summary_text, sentiment_label, sentiment_score, "Technology",
                    published_at, source, link, image_url,
                    persons, organizations, locations,
                    read_time, popularity
                ))

                print(f"✅ Saved news: {title}")

            except Exception as e:
                print(f"❌ Error processing {entry.title}: {e}")

        self.news_repository.close()

    def summarize_description(self, description: str) -> str:
        if len(description.split()) < 30:
            return description
        return self.summarizer(description, max_length=100, min_length=30, do_sample=False)[0]['summary_text']

    def analyze_sentiment(self, title: str):
        sentiment = self.sentiment_classifier(title)[0]
        return sentiment['label'], float(sentiment['score'])

    def extract_entities(self, description: str):
        entities = self.ner_model(description)
        persons = [entity['word'] for entity in entities if entity['entity_group'] == 'PER']
        organizations = [entity['word'] for entity in entities if entity['entity_group'] == 'ORG']
        locations = [entity['word'] for entity in entities if entity['entity_group'] == 'LOC']
        return persons, organizations, locations
