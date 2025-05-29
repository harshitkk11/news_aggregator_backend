from flask import Blueprint, request, jsonify
from config.db import get_db_connection
from psycopg2 import sql

fetch_news_bp = Blueprint("fetch_news", __name__)

@fetch_news_bp.route("/fetch-news", methods=["POST"])
def fetch_news():
    try:
        data = request.get_json()
        user_id = data.get("userId")

        conn = get_db_connection()
        cur = conn.cursor()

        if not user_id:
            # No userId: Fetch all news without category filter
            cur.execute("""
                SELECT n.*, c.title as category_name
                FROM news n
                LEFT JOIN categories c ON n."categoryId" = CAST(c.id AS TEXT)
                ORDER BY n.published_at DESC
                LIMIT 100
            """)
            news_data = cur.fetchall()
            column_names = [desc[0] for desc in cur.description]
            news_list = [dict(zip(column_names, row)) for row in news_data]

            cur.close()
            conn.close()
            return jsonify({
                "success": True,
                "news": news_list,
                "count": len(news_list),
                "message": "No userId provided, returning all news"
            }), 200

        # Step 1: Check for user preferences
        cur.execute("""
            SELECT c.id as category_id, c.title as category_name 
            FROM user_preferences up
            JOIN categories c ON up."categoryId" = c.id
            WHERE up."userId" = %s
        """, (user_id,))
        preferences = cur.fetchall()

        if not preferences:
            # Valid userId but no preferences: Fetch all news
            cur.execute("""
                SELECT n.*, c.title as category_name
                FROM news n
                LEFT JOIN categories c ON n."categoryId" = CAST(c.id AS TEXT)
                ORDER BY n.published_at DESC
                LIMIT 100
            """)
            news_data = cur.fetchall()
            column_names = [desc[0] for desc in cur.description]
            news_list = [dict(zip(column_names, row)) for row in news_data]

            cur.close()
            conn.close()
            return jsonify({
                "success": True,
                "news": news_list,
                "count": len(news_list),
                "message": "No preferences set for user, returning all news"
            }), 200

        # Step 2: Fetch news based on user preferences
        category_ids = [str(pref[0]) for pref in preferences]  # Convert UUIDs to strings

        cur.execute("""
            SELECT n.*, c.title as category_name 
            FROM news n
            LEFT JOIN categories c ON n."categoryId" = CAST(c.id AS TEXT)
            WHERE n."categoryId" = ANY(%s)
            ORDER BY n.published_at DESC
            LIMIT 100
        """, (category_ids,))
        
        news_data = cur.fetchall()
        column_names = [desc[0] for desc in cur.description]
        news_list = [dict(zip(column_names, row)) for row in news_data]

        cur.close()
        conn.close()

        return jsonify({
            "success": True,
            "news": news_list,
            "count": len(news_list)
        }), 200

    except Exception as e:
        print("Get News Error:", str(e))
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()