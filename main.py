# main.py
# Flask Server to handle API routes
print("🔥 main.py started")
import os

from flask import Flask, jsonify
from flask_cors import CORS  # 👈 import CORS
from scripts.news_fetcher import fetch_and_process_news
from routes.users.createUser import create_user_bp
from routes.users.statusUpdate import update_status_bp
from routes.users.preferences import user_preference_bp
from routes.categories.fetch_categories import fetch_categories_bp

app = Flask(__name__)
CORS(app)  # 👈 Enable CORS for all routes

# user
app.register_blueprint(create_user_bp, url_prefix="/api/user")
app.register_blueprint(update_status_bp, url_prefix="/api/user")
app.register_blueprint(user_preference_bp, url_prefix="/api/user")

# categories
app.register_blueprint(fetch_categories_bp, url_prefix="/api/categories")


# Home route
@app.route('/')
def home():
    return "News Aggregator Backend is Live 🚀"

# API to trigger fetching and processing news
@app.route('/api/fetch-news', methods=['GET'])
def fetch_news_route():
    fetch_and_process_news()
    return jsonify({"message": "Fetched and processed latest news successfully!"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Render sets PORT env variable
    app.run(host="0.0.0.0", port=port)
