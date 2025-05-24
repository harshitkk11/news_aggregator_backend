from flask import Blueprint, request, jsonify
from config.db import get_db_connection
from psycopg2 import sql

fetch_news_bp = Blueprint("fetch_news", __name__)

@fetch_news_bp.route("/fetch-news", methods=["POST"])
def fetch_news():
    try:
        data = request.get_json()
        user_id = data.get("userId")

        if not user_id:
            return jsonify({"success": False, "message": "userId is required"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Step 1: Get user's preferred category IDs (as UUID)
        cur.execute('SELECT "categoryId" FROM user_preferences WHERE "userId" = %s', (user_id,))
        category_uuids = [row[0] for row in cur.fetchall()]

        if not category_uuids:
            return jsonify({"success": True, "news": []}), 200

        # Convert UUIDs to strings for comparison with news.categoryId (TEXT)
        category_ids = [str(uuid) for uuid in category_uuids]

        # Step 2: Fetch news with matching category IDs
        cur.execute("""
            SELECT *, 
                   "categoryId" as category_id, 
                   category as category_name
            FROM news
            WHERE "categoryId" = ANY(%s)
            ORDER BY published_at DESC
            LIMIT 100
        """, (category_ids,))
        
        news_data = cur.fetchall()
        column_names = [desc[0] for desc in cur.description]
        news_list = [dict(zip(column_names, row)) for row in news_data]

        return jsonify({
            "success": True,
            "news": news_list,
            "category_ids": category_ids
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Failed to fetch news",
            "error": str(e)
        }), 500
    finally:
        cur.close()
        conn.close()
    try:
        print("Fetching news by user preference...")
        data = request.get_json()
        user_id = data.get("userId")

        if not user_id:
            return jsonify({"success": False, "message": "userId is required"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Step 1: Fetch user preferences with category names
        query = sql.SQL("""
            SELECT c.id as category_id, c.name as category_name 
            FROM user_preferences up
            JOIN categories c ON up."categoryId" = c.id
            WHERE up."userId" = %s
        """)
        cur.execute(query, (user_id,))
        preferences = cur.fetchall()
        
        if not preferences:
            cur.close()
            conn.close()
            return jsonify({"success": True, "news": [], "message": "No preferences set"}), 200

        category_ids = [pref[0] for pref in preferences]
        category_names = [pref[1] for pref in preferences]

        # Step 2: Fetch news articles with category information
        news_query = sql.SQL("""
            SELECT n.*, c.name as category_name 
            FROM news n
            JOIN categories c ON n."categoryId" = c.id
            WHERE n."categoryId" = ANY(%s)
            ORDER BY n."publishedAt" DESC
            LIMIT 100  -- Add limit to prevent too many results
        """)
        cur.execute(news_query, (category_ids,))
        
        news_data = cur.fetchall()
        column_names = [desc[0] for desc in cur.description]
        news_list = [dict(zip(column_names, row)) for row in news_data]

        cur.close()
        conn.close()

        response = {
            "success": True,
            "news": news_list,
            "user_preferences": category_names,
            "count": len(news_list)
        }
        return jsonify(response), 200

    except Exception as e:
        print("Get News Error:", str(e))
        return jsonify({
            "success": False, 
            "message": "An unexpected error occurred.",
            "error": str(e)
        }), 500