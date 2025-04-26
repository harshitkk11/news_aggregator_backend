# fetch_rss_to_raw.py — Fetch RSS feed and save into raw_news table in Supabase

import feedparser
from db import connection, cursor  # Your db.py file for connection

# RSS Feed URL (example: Indian Express Technology)
rss_url = "https://indianexpress.com/section/technology/feed/"

# Parse the RSS feed
feed = feedparser.parse(rss_url)

for entry in feed.entries:
    # Extract necessary fields
    title = entry.title
    description = entry.description
    link = entry.link
    published_at = entry.published if hasattr(entry, 'published') else None
    source = "Indian Express"  # Hardcoded because we know it's Indian Express
    image_url = None

    # Check if media content (image) exists
    if 'media_content' in entry:
        image_url = entry.media_content[0]['url']

    try:
        # Insert into raw_news table
        insert_query = """
        INSERT INTO raw_news (title, description, link, published_at, source, image_url)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (link) DO NOTHING;  -- Avoid inserting same article twice
        """
        cursor.execute(insert_query, (title, description, link, published_at, source, image_url))
        connection.commit()

        print(f"✅ Saved to raw_news: {title}")

    except Exception as e:
        print(f"❌ Error inserting {title}: {e}")
        connection.rollback()
