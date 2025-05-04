# main.py
# Flask Server to handle API routes
print("🔥 main.py started")
import os

from flask import Flask, jsonify
from flask_cors import CORS  # 👈 import CORS
from scripts.news_fetcher import fetch_and_process_news
from routes.users.createUser import user_bp

app = Flask(__name__)
CORS(app)  # 👈 Enable CORS for all routes

app.register_blueprint(user_bp, url_prefix="/api/user")

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
