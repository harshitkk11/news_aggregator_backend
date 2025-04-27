from flask import Blueprint
from controllers.newsController import NewsController

news_routes = Blueprint('news', __name__)
controller = NewsController()

def set_routes(app):
    news_routes.add_url_rule('/fetch_news', view_func=controller.fetch_and_process_news, methods=['GET'])
    app.register_blueprint(news_routes)