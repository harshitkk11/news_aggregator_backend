# News Aggregator Backend

This project is a news aggregator that fetches news articles from an RSS feed, processes them using AI models for summarization, sentiment analysis, and named entity recognition, and stores the processed data in a database.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py                # App factory
│   ├── config.py                  # App config (e.g., DB URL, API keys)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── news_routes.py         # News fetch, read endpoints
│   │   ├── user_routes.py         # User preferences, profile
│   │   ├── ai_routes.py           # Summarization, sentiment, recommend
│   ├── services/
│   │   ├── __init__.py
│   │   ├── news_fetcher.py        # NewsAPI, RSS parsers
│   │   ├── summarizer.py          # HuggingFace models (T5/BART)
│   │   ├── sentiment_analyzer.py  # BERT or similar
│   │   ├── recommender.py         # ML-based recommendation logic
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                # SQLAlchemy models for User
│   │   ├── article.py             # News Article model
│   │   ├── preference.py          # User preferences
│   ├── db/
│   │   ├── __init__.py            # DB connection using SQLAlchemy
│   │   ├── supabase_client.py     # Supabase SDK / REST calls
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── response_wrapper.py    # Standard API response format
│   │   ├── logger.py              # Custom logging if needed
│   └── main.py                    # Entrypoint (Flask app)
│
├── tests/
│   ├── test_news.py
│   ├── test_summarizer.py
│   └── ...
│
├── requirements.txt               # Python dependencies
├── run.py                         # Run server
├── .env                           # Environment variables
└── README.md
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd news_aggregator_backend
   ```

2. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

3. **Configure the database:**
   Update the database connection settings in `src/db/connection.py` as per your database configuration.

4. **Run the application:**
   ```
   python src/app.py
   ```

## Usage

- The application exposes HTTP endpoints for fetching and processing news articles.
- You can access the news aggregator functionality through the defined routes in `src/routes/newsRoutes.py`.

## AI Models

The application utilizes the following AI models for processing news articles:

- **Summarization:** `facebook/bart-large-cnn`
- **Sentiment Analysis:** `nlptown/bert-base-multilingual-uncased-sentiment`
- **Named Entity Recognition:** `dbmdz/bert-large-cased-finetuned-conll03-english`

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.