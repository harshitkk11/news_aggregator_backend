from flask import Flask, jsonify
from internal.src.routes.newsRoutes import set_routes

app = Flask(__name__)

@app.route('/')
def home():
    return "News Aggregator Backend is Live 🚀"

# Register all API routes (including fetch-news and preferences)
set_routes(app)

if __name__ == '__main__':
    app.run(debug=True)
