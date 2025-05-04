from flask import Blueprint, request, jsonify
from config.db import get_db_connection

user_bp = Blueprint("user", __name__)

@user_bp.route("/create-user", methods=["POST"])
def create_user():
    try:
        data = request.get_json()
        user_id = data.get("userId")

        conn = get_db_connection()
        cur = conn.cursor()

        # 🔍 Check if user already exists
        cur.execute('SELECT * FROM users WHERE "userId" = %s', (user_id,))
        existing_user = cur.fetchone()

        if existing_user:
            return jsonify({
                "success": False,
                "message": "User already exists"
            }), 400

        # 📝 Insert new user
        cur.execute('INSERT INTO users ("userId") VALUES (%s)', (user_id,))
        conn.commit()

        cur.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "User registered successfully"
        }), 200

    except Exception as e:
        print("User creation error:", str(e))
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred."
        }), 500
