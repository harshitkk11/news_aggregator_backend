# News Aggregator Backend

This project is a news aggregator that fetches news articles from an RSS feed, processes them using AI models for summarization, sentiment analysis, and named entity recognition, and stores the processed data in a database.

## Project Structure

```
news_aggregator_backend
├── src
│   ├── controllers
│   │   └── newsController.py
│   ├── routes
│   │   └── newsRoutes.py
│   ├── services
│   │   └── newsService.py
│   ├── repositories
│   │   └── newsRepository.py
│   ├── scripts
│   │   └── news_fetcher.py
│   ├── db
│   │   ├── connection.py
│   │   └── cursor.py
│   └── app.py
├── requirements.txt
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