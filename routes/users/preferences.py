from flask import Blueprint, request, jsonify
from config.db import get_db_connection

user_preference_bp = Blueprint("preference", __name__)

@user_preference_bp.route("/preference", methods=["PATCH"])
def update_user_preference():
    try:
        print("Updating user preferences...") 
        data = request.get_json()
        user_id = data.get("userId")
        new_preferences = data.get("preference")  # Expecting a list of categoryIds

        if not user_id or not isinstance(new_preferences, list):
            return jsonify({"success": False, "message": "Invalid input"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Step 1: Check if user exists
        cur.execute('SELECT * FROM users WHERE "userId" = %s', (user_id,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": "User not found"}), 404

        # Step 2: Get existing preferences
        cur.execute('SELECT "categoryId" FROM user_preferences WHERE "userId" = %s', (user_id,))
        existing_preferences = set(row[0] for row in cur.fetchall())
        new_preferences_set = set(new_preferences)

        # Step 3: Determine preferences to add and delete
        to_add = new_preferences_set - existing_preferences
        to_delete = existing_preferences - new_preferences_set

        # Step 4: Delete old preferences
        if to_delete:
            cur.execute('DELETE FROM user_preferences WHERE "userId" = %s AND "categoryId" = ANY(%s)', (user_id, list(to_delete)))

        # Step 5: Insert new preferences
        for category_id in to_add:
            cur.execute('INSERT INTO user_preferences ("userId", "categoryId") VALUES (%s, %s)', (user_id, category_id))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "message": "Preferences updated successfully"}), 200

    except Exception as e:
        print("Update Preference Error:", str(e))
        return jsonify({"success": False, "message": "An unexpected error occurred."}), 500
