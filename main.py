from flask import Flask, jsonify
from news_aggregator_backend.src.scripts.news_fetcher import fetch_and_process_news

app = Flask(__name__)

@app.route('/')
def home():
    return "News Aggregator Backend is Live 🚀"

@app.route('/api/fetch-news', methods=['GET'])
def fetch_news_route():
    fetch_and_process_news()
    return jsonify({"message": "Fetched and processed latest news successfully!"})

if __name__ == '__main__':
    app.run(debug=True)
