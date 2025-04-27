from news_aggregator_backend.src.services.newsService import NewsService
def fetch_and_process_news():
    news_service = NewsService()
    news_service.fetch_and_process_news()
