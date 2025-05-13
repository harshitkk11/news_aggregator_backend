from flask import Blueprint, request, jsonify
from internal.src.controllers.newsController import NewsController
from internal.src.controllers.preferenceController import PreferenceController

news_routes = Blueprint('news', __name__)
news_controller = NewsController()
preference_controller = PreferenceController()

# filepath: /home/abhi/projects/news_aggregator_backend/internal/src/routes/newsRoutes.py
def set_routes(app):
    # Existing news fetch route with updated path
    news_routes.add_url_rule('/api/fetch-news', view_func=news_controller.fetch_and_process_news, methods=['GET'])

    # New preference fetch route with updated path
    news_routes.add_url_rule('/api/preferences', view_func=get_preferences, methods=['GET'])

    app.register_blueprint(news_routes)
    
def get_preferences():
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({"code": "FAILURE", "message": "User ID missing in headers"}), 401

    preferences = preference_controller.get_preferences(user_id)
    return jsonify({
        "code": "SUCCESS",
        "message": "Preferences fetched successfully",
        "data": preferences
    })
