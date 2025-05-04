# main.py
# Flask Server to handle API routes
print("🔥 main.py started")  # Add this at the top

from flask import Flask, jsonify
from scripts.news_fetcher import fetch_and_process_news  # import your function

app = Flask(__name__)

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
    app.run(debug=True)
