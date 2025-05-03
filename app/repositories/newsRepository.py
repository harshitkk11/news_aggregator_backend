class NewsRepository:
    def __init__(self, connection, cursor):
        self.connection = connection
        self.cursor = cursor

    def save_news(self, news_data: tuple):
        insert_query = """
        INSERT INTO news
        (title, description, summary, sentiment_label, sentiment_score, category, published_at, source, link, image_url, persons, organizations, locations, read_time, popularity)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (link) DO NOTHING;
        """
        try:
            self.cursor.execute(insert_query, news_data)
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e

    def close(self):
        self.cursor.close()
        self.connection.close()
