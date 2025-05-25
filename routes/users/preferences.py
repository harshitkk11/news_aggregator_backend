from flask import Blueprint, request, jsonify
from config.db import get_db_connection
import uuid

user_preference_bp = Blueprint("preference", __name__)

def is_valid_uuid(val: str) -> bool:
    """Validate if a string is a valid UUID."""
    try:
        uuid.UUID(val)
        return True
    except ValueError:
        return False

@user_preference_bp.route("/preference", methods=["PATCH"])
def update_user_preference():
    try:
        print("Updating user preferences...")
        data = request.get_json()
        user_id = data.get("userId")
        new_preferences = data.get("preference")  # Expecting a list of categoryIds

        # Validate input
        if not user_id or not isinstance(new_preferences, list):
            print("Invalid input: userId or preference missing/invalid")
            return jsonify({"success": False, "message": "Invalid input: userId and preference (list) are required"}), 400

        # Validate each categoryId is a valid UUID
        invalid_categories = [cat for cat in new_preferences if not is_valid_uuid(cat)]
        if invalid_categories:
            print(f"Invalid category IDs: {invalid_categories}")
            return jsonify({"success": False, "message": f"Invalid category IDs: {invalid_categories}"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Step 1: Check if user exists
        # No UUID casting for userId (assuming userId is now text)
        print(f"Checking user existence for userId: {user_id}")
        cur.execute('SELECT * FROM users WHERE "userId" = %s', (user_id,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            print(f"User not found: {user_id}")
            return jsonify({"success": False, "message": "User not found"}), 404

        # Step 2: Validate category IDs (ensure they exist in categories table)
        if new_preferences:  # Only validate if the list is not empty
            print(f"Validating category IDs: {new_preferences}")
            cur.execute('SELECT id FROM categories WHERE id = ANY(%s::uuid[])', (new_preferences,))
            valid_categories = set(row[0] for row in cur.fetchall())
            invalid_categories = set(new_preferences) - valid_categories
            if invalid_categories:
                cur.close()
                conn.close()
                print(f"Invalid category IDs: {invalid_categories}")
                return jsonify({"success": False, "message": f"Invalid category IDs: {invalid_categories}"}), 400

        # Step 3: Delete all existing preferences for the user
        # No UUID casting for userId (assuming userId is now text)
        cur.execute('DELETE FROM user_preferences WHERE "userId" = %s', (user_id,))
        print(f"Deleted existing preferences for user: {user_id}")

        # Step 4: Insert new preferences (if any)
        if new_preferences:
            for category_id in new_preferences:
                # Keep UUID casting for categoryId
                cur.execute(
                    'INSERT INTO user_preferences ("userId", "categoryId") VALUES (%s, %s::uuid)',
                    (user_id, category_id)
                )
            print(f"Added new preferences for user {user_id}: {new_preferences}")
        else:
            print(f"No new preferences to add for user {user_id} (cleared preferences)")

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "message": "Preferences updated successfully"}), 200

    except Exception as e:
        print("Update Preference Error:", str(e))
        return jsonify({"success": False, "message": "An unexpected error occurred."}), 500