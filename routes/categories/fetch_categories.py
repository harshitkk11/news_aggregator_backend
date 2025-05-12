from flask import Blueprint, request, jsonify
from config.db import get_db_connection
import psycopg2.extras

fetch_categories_bp = Blueprint("fetch_categories", __name__)

@fetch_categories_bp.route("/fetch_categories", methods=["GET"])
def fetch_categories():
    try:
        print("Fetching categories...")
        conn = get_db_connection()
        
        # Use RealDictCursor to get rows as dictionaries
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute('SELECT id, title FROM categories')
        categories = cur.fetchall()

        # categories is already a list of dictionaries
        # categories_list = []
        # for category in categories:
        #     categories_list.append({
        #         "categoryId": category["id"],
        #         "categoryName": category["title"]
        #     })

        cur.close()
        conn.close()

        return jsonify({"categories": categories}), 200

    except Exception as e:
        print("Fetch Categories Error:", str(e))
        return jsonify({"success": False, "message": "An unexpected error occurred."}), 500
