from flask import request, jsonify
from services.newsService import NewsService

class NewsController:
    def __init__(self):
        self.news_service = NewsService()

    def fetch_and_process_news(self):
        try:
            news_data = self.news_service.fetch_and_process_news()
            return jsonify(news_data), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500