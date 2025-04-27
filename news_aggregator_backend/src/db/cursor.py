from news_aggregator_backend.src.db.connection import get_connection
def get_cursor():
    connection = get_connection()
    return connection, connection.cursor()
